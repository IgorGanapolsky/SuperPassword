"""Omarchy steal: pin+hash, idle release, lazy open, loopback. Fail closed. No QEMU desktop."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

PROXY_METRICS = frozenset(
    {
        "idle_cpu",
        "qemu_cpu",
        "stars",
        "vm_boot_time",
        "virgl_fps",
        "desktop_polish",
    }
)
OMARCHY_DESKTOPS = frozenset(
    {
        "try_omarchy",
        "try_omarchy_qemu",
        "omarchy",
        "omarchy_linux_desktop",
        "basecamp_omarchy",
        "qemu_hv",
        "qemu_desktop",
        "arch_omarchy_vm",
    }
)
ALLOWED_PLATFORMS = frozenset(
    {
        "local_omarchy_harness",
        "agent_omarchy",
        "local_pin_hash_harness",
    }
)
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
IAP_WEIGHT = 10
TASK_WEIGHT = 5


@dataclass(frozen=True)
class ControlDecision:
    action: str
    ok: bool
    reason: str
    addresses: tuple[str, ...] = ()


def _norm(value: str) -> str:
    return (value or "").strip().lower().replace("-", "_").replace(".", "_")


def evaluate_platform(*, platform: str) -> ControlDecision:
    name = _norm(platform)
    if name in ALLOWED_PLATFORMS:
        return ControlDecision(
            action="allow_local_omarchy_harness",
            ok=True,
            reason="keep Omarchy methods as a local harness under the monthly cap",
        )
    if name in OMARCHY_DESKTOPS or "omarchy" in name or "qemu" in name:
        return ControlDecision(
            action="block_omarchy_desktop",
            ok=False,
            reason="Try Omarchy / QEMU desktop install is denied as product infra",
        )
    return ControlDecision(
        action="block_omarchy_desktop",
        ok=False,
        reason="unknown Omarchy platform is denied",
    )


def evaluate_pin(*, revision: str, sha256: str, floating: bool) -> ControlDecision:
    rev = (revision or "").strip()
    digest = (sha256 or "").strip()
    if floating or rev.lower() in {"main", "master", "latest", "head", ""}:
        return ControlDecision(
            action="block_floating_pin",
            ok=False,
            reason="floating pins are denied; pin a revision with a sha256",
        )
    if not SHA256_RE.match(digest):
        return ControlDecision(
            action="block_missing_hash",
            ok=False,
            reason="strict sha256 provenance is required",
        )
    return ControlDecision(
        action="allow_pinned_provenance",
        ok=True,
        reason="revision is pinned with a sha256 preimage",
    )


def evaluate_idle(*, held_open: bool, idle: bool) -> ControlDecision:
    if idle and held_open:
        return ControlDecision(
            action="block_idle_hold",
            ok=False,
            reason="expensive resources must release when idle",
        )
    return ControlDecision(
        action="allow_idle_released",
        ok=True,
        reason="idle path does not hold devices or sessions open",
    )


def evaluate_lazy_open(*, opened_at_startup: bool, demanded: bool) -> ControlDecision:
    if opened_at_startup and not demanded:
        return ControlDecision(
            action="block_eager_open",
            ok=False,
            reason="open capture or paid APIs only on demand",
        )
    return ControlDecision(
        action="allow_lazy_open",
        ok=True,
        reason="resource open is deferred until demand",
    )


def evaluate_dirty_loop(*, dirty: bool, refreshed: bool) -> ControlDecision:
    if refreshed and not dirty:
        return ControlDecision(
            action="block_unconditional_refresh",
            ok=False,
            reason="do not refresh or re-render when nothing is dirty",
        )
    return ControlDecision(
        action="allow_dirty_refresh",
        ok=True,
        reason="refresh only when dirty",
    )


def evaluate_forward(*, bind: str, protocol: str) -> ControlDecision:
    host = (bind or "").strip().lower()
    proto = _norm(protocol)
    if proto not in {"tcp", "udp"}:
        return ControlDecision(
            action="block_public_forward",
            ok=False,
            reason="only tcp or udp loopback forwards are allowed",
        )
    if host in {"127.0.0.1", "localhost", "::1"}:
        return ControlDecision(
            action="allow_loopback_forward",
            ok=True,
            reason="forward only on loopback",
        )
    return ControlDecision(
        action="block_public_forward",
        ok=False,
        reason="public binds are denied; use 127.0.0.1 only",
    )


def evaluate_share(*, paths: Sequence[str]) -> ControlDecision:
    cleaned = [p.strip() for p in paths if str(p).strip()]
    if len(cleaned) == 1:
        return ControlDecision(
            action="allow_single_share",
            ok=True,
            reason="one optional shared path keeps the blast radius small",
        )
    return ControlDecision(
        action="block_multi_share",
        ok=False,
        reason="multiple shared folders are denied",
    )


def evaluate_reset(*, confirm_text: str, expected: str) -> ControlDecision:
    if (confirm_text or "") == (expected or "") and expected:
        return ControlDecision(
            action="allow_confirmed_reset",
            ok=True,
            reason="destructive reset requires exact typed confirmation",
        )
    return ControlDecision(
        action="block_unconfirmed_reset",
        ok=False,
        reason="reset blocked without exact confirmation text",
    )


def _control_clears(raw: Mapping[str, object]) -> bool:
    platform = evaluate_platform(platform=str(raw.get("platform") or ""))
    return platform.ok


def pick_control(*, controls: Sequence[Mapping[str, object]]) -> ControlDecision:
    for raw in controls:
        control_id = str(raw.get("id") or "").strip()
        if control_id and _control_clears(raw):
            return ControlDecision(
                action="allow_local_control",
                ok=True,
                reason="local Omarchy harness control cleared",
                addresses=(f"omarchy:{control_id}",),
            )
    return ControlDecision(
        action="block_no_local_control",
        ok=False,
        reason="no control cleared local Omarchy harness gates",
    )


def evaluate_claim(*, cite: str, addresses: Sequence[str]) -> ControlDecision:
    target = (cite or "").strip()
    if target and target in set(addresses):
        return ControlDecision(
            action="allow_on_omarchy",
            ok=True,
            reason="cite is the local Omarchy control address",
        )
    return ControlDecision(
        action="block_off_omarchy",
        ok=False,
        reason="cite is not the local Omarchy address",
    )


def rank_work(*, candidates: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    scored: list[tuple[float, dict[str, object]]] = []
    for raw in candidates:
        row = dict(raw)
        metric = _norm(str(row.get("metric", "")))
        effort = max(float(row.get("effort") or 1), 1.0)
        if metric in PROXY_METRICS:
            score = 0.0
        else:
            iap = float(row.get("expected_iap_attempts") or 0)
            tasks = float(row.get("expected_completed_tasks") or 0)
            score = (iap * IAP_WEIGHT + tasks * TASK_WEIGHT) / effort
        row["score"] = score
        scored.append((score, row))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [row for _, row in scored]


def require_omarchy_controls(
    *,
    has_platform: bool,
    has_controls: bool,
    has_cite: bool,
) -> ControlDecision:
    if has_platform and has_controls and has_cite:
        return ControlDecision(
            action="controls_complete",
            ok=True,
            reason="platform, controls, and cite evaluated",
        )
    return ControlDecision(
        action="block_incomplete_controls",
        ok=False,
        reason="fail closed: missing platform, controls, or cite",
    )


def _load_controls(path: str) -> list[dict[str, object]]:
    if not path:
        return []
    raw = Path(path)
    if not raw.is_file():
        return []
    payload = json.loads(raw.read_text())
    items = payload.get("controls", payload) if isinstance(payload, Mapping) else payload
    return [dict(item) for item in items if isinstance(item, Mapping)]


def _truthy(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Local Omarchy harness controls (no QEMU desktop)."
    )
    parser.add_argument("--platform", default="")
    parser.add_argument("--controls", default="")
    parser.add_argument("--cite", default="")
    parser.add_argument("--revision", default="")
    parser.add_argument("--sha256", default="")
    parser.add_argument("--floating", default="0")
    parser.add_argument("--bind", default="")
    parser.add_argument("--protocol", default="tcp")
    parser.add_argument("--idle", default="")
    parser.add_argument("--held-open", default="0")
    parser.add_argument("--opened-at-startup", default="")
    parser.add_argument("--demanded", default="0")
    parser.add_argument("--dirty", default="")
    parser.add_argument("--refreshed", default="0")
    parser.add_argument("--share", default="")
    parser.add_argument("--confirm-text", default="")
    parser.add_argument("--confirm-expected", default="")
    args = parser.parse_args()

    payload: dict[str, object] = {}
    ok = True

    has_platform = bool(args.platform)
    if has_platform:
        platform = evaluate_platform(platform=args.platform)
        payload["platform"] = {
            k: v for k, v in platform.__dict__.items() if k != "addresses"
        }
        ok = ok and platform.ok

    controls = _load_controls(args.controls)
    has_controls = bool(args.controls)
    addresses: list[str] = []
    if has_controls:
        picked = pick_control(controls=controls)
        payload["pick"] = {
            "action": picked.action,
            "ok": picked.ok,
            "reason": picked.reason,
            "addresses": list(picked.addresses),
        }
        addresses = list(picked.addresses)
        ok = ok and picked.ok

    has_cite = bool(args.cite)
    if has_cite:
        grounded = evaluate_claim(cite=args.cite, addresses=addresses)
        payload["cite"] = {
            k: v for k, v in grounded.__dict__.items() if k != "addresses"
        }
        ok = ok and grounded.ok

    if args.revision or args.sha256 or _truthy(args.floating):
        pinned = evaluate_pin(
            revision=args.revision,
            sha256=args.sha256,
            floating=_truthy(args.floating),
        )
        payload["pin"] = {
            k: v for k, v in pinned.__dict__.items() if k != "addresses"
        }
        ok = ok and pinned.ok

    if args.bind:
        forwarded = evaluate_forward(bind=args.bind, protocol=args.protocol)
        payload["forward"] = {
            k: v for k, v in forwarded.__dict__.items() if k != "addresses"
        }
        ok = ok and forwarded.ok

    if args.idle != "":
        idle = evaluate_idle(
            held_open=_truthy(args.held_open),
            idle=_truthy(args.idle),
        )
        payload["idle"] = {
            k: v for k, v in idle.__dict__.items() if k != "addresses"
        }
        ok = ok and idle.ok

    if args.opened_at_startup != "":
        lazy = evaluate_lazy_open(
            opened_at_startup=_truthy(args.opened_at_startup),
            demanded=_truthy(args.demanded),
        )
        payload["lazy_open"] = {
            k: v for k, v in lazy.__dict__.items() if k != "addresses"
        }
        ok = ok and lazy.ok

    if args.dirty != "":
        dirty = evaluate_dirty_loop(
            dirty=_truthy(args.dirty),
            refreshed=_truthy(args.refreshed),
        )
        payload["dirty_loop"] = {
            k: v for k, v in dirty.__dict__.items() if k != "addresses"
        }
        ok = ok and dirty.ok

    if args.share:
        shares = [part for part in args.share.split(",") if part.strip()]
        shared = evaluate_share(paths=shares)
        payload["share"] = {
            k: v for k, v in shared.__dict__.items() if k != "addresses"
        }
        ok = ok and shared.ok

    if args.confirm_text or args.confirm_expected:
        reset = evaluate_reset(
            confirm_text=args.confirm_text,
            expected=args.confirm_expected,
        )
        payload["reset"] = {
            k: v for k, v in reset.__dict__.items() if k != "addresses"
        }
        ok = ok and reset.ok

    completeness = require_omarchy_controls(
        has_platform=has_platform,
        has_controls=has_controls,
        has_cite=has_cite,
    )
    payload["completeness"] = {
        k: v for k, v in completeness.__dict__.items() if k != "addresses"
    }
    ok = ok and completeness.ok
    print(json.dumps(payload, indent=2))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
