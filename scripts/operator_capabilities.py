"""Astra steal: local operator capabilities. Fail closed. No ChatGPT Pro / Astra API."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

PROXY_METRICS = frozenset({"tokens", "pr_velocity", "daily_messages", "agent_count"})
METERED_PLATFORMS = frozenset(
    {
        "gpt6_astra",
        "gpt_6_astra",
        "astra",
        "astra_pro",
        "chatgpt_pro",
        "openai_primary",
        "codex_app",
    }
)
ALLOWED_SURFACES = frozenset({"local_cli", "reusable_cli", "fail_closed_script"})
PAID_SURFACES = frozenset(
    {"chatgpt_pro", "chatgpt_codex", "openai_api", "gpt6_astra_api", "astra_api"}
)
ALLOWED_HARNESSES = frozenset({"browseros", "local_computer_use", "cursor_browser"})
PAID_HARNESSES = frozenset({"astra_desktop", "chatgpt_desktop", "computer_use_api"})
ALLOWED_EFFORT = frozenset({"low", "medium"})
BLOCKED_DEFAULT_EFFORT = frozenset({"high", "xhigh", "max", "extra_high"})
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
    if name in {"local_operator", "operator_capabilities", "king_mode_local"}:
        return ControlDecision(
            action="allow_local_operator",
            ok=True,
            reason="run operator patterns locally under the monthly cap",
        )
    if name in METERED_PLATFORMS or "astra" in name or "chatgpt" in name:
        return ControlDecision(
            action="block_metered",
            ok=False,
            reason="ChatGPT Pro and gpt-6-astra API pricing break the $20 cap",
        )
    return ControlDecision(
        action="block_metered",
        ok=False,
        reason="unknown operator platform is denied",
    )


def evaluate_surface(*, surface: str) -> ControlDecision:
    name = _norm(surface)
    if name in ALLOWED_SURFACES:
        return ControlDecision(
            action="allow_reusable_cli",
            ok=True,
            reason="reusable local CLIs beat chat-session theater",
        )
    if name in PAID_SURFACES or "chatgpt" in name or "astra" in name:
        return ControlDecision(
            action="block_paid_surface",
            ok=False,
            reason="Codex-in-ChatGPT and Astra API surfaces stay denied",
        )
    return ControlDecision(
        action="block_paid_surface",
        ok=False,
        reason="unknown operator surface is denied",
    )


def evaluate_harness(*, harness: str) -> ControlDecision:
    name = _norm(harness)
    if name in ALLOWED_HARNESSES:
        return ControlDecision(
            action="allow_local_computer_use",
            ok=True,
            reason="screen control uses BrowserOS / local harness, not Astra Desktop",
        )
    if name in PAID_HARNESSES or "astra" in name or "chatgpt" in name:
        return ControlDecision(
            action="block_paid_harness",
            ok=False,
            reason="Astra Desktop computer-use is outside the cap",
        )
    return ControlDecision(
        action="block_paid_harness",
        ok=False,
        reason="unknown computer-use harness is denied",
    )


def evaluate_effort(*, effort: str) -> ControlDecision:
    name = _norm(effort)
    if name in ALLOWED_EFFORT:
        return ControlDecision(
            action="allow_medium_effort",
            ok=True,
            reason="medium (or low) effort is the default; escalate only for hard bugs",
        )
    if name in BLOCKED_DEFAULT_EFFORT:
        return ControlDecision(
            action="block_max_by_default",
            ok=False,
            reason="max/xhigh effort is not the default under the budget cap",
        )
    return ControlDecision(
        action="block_max_by_default",
        ok=False,
        reason="unknown effort setting is denied",
    )


def _cap_clears(cap: Mapping[str, object]) -> bool:
    surface = evaluate_surface(surface=str(cap.get("surface") or ""))
    harness = evaluate_harness(harness=str(cap.get("harness") or ""))
    effort = evaluate_effort(effort=str(cap.get("effort") or ""))
    return surface.ok and harness.ok and effort.ok


def pick_capability(*, capabilities: Sequence[Mapping[str, object]]) -> ControlDecision:
    for raw in capabilities:
        cap_id = str(raw.get("id") or "").strip()
        if cap_id and _cap_clears(raw):
            return ControlDecision(
                action="allow_local_cap",
                ok=True,
                reason="keep local CLI + BrowserOS + medium effort",
                addresses=(f"cap:{cap_id}",),
            )
    return ControlDecision(
        action="block_no_local_cap",
        ok=False,
        reason="no capability cleared local operator controls",
    )


def evaluate_claim(*, cite: str, addresses: Sequence[str]) -> ControlDecision:
    target = (cite or "").strip()
    if target and target in set(addresses):
        return ControlDecision(
            action="allow_on_operator",
            ok=True,
            reason="cite is the local operator capability",
        )
    return ControlDecision(
        action="block_off_operator",
        ok=False,
        reason="cite is not the local operator capability",
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


def require_operator_controls(
    *,
    has_platform: bool,
    has_capabilities: bool,
    has_cite: bool,
) -> ControlDecision:
    if has_platform and has_capabilities and has_cite:
        return ControlDecision(
            action="controls_complete",
            ok=True,
            reason="platform, capabilities, and cite evaluated",
        )
    return ControlDecision(
        action="block_incomplete_controls",
        ok=False,
        reason="fail closed: missing platform, capabilities, or cite",
    )


def _load_capabilities(path: str) -> list[dict[str, object]]:
    if not path:
        return []
    raw = Path(path)
    if not raw.is_file():
        return []
    payload = json.loads(raw.read_text())
    items = (
        payload.get("capabilities", payload) if isinstance(payload, Mapping) else payload
    )
    return [dict(item) for item in items if isinstance(item, Mapping)]


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Local operator capabilities (no ChatGPT Pro / Astra API)."
    )
    parser.add_argument("--platform", default="")
    parser.add_argument("--capabilities", default="")
    parser.add_argument("--cite", default="")
    args = parser.parse_args()

    payload: dict[str, object] = {}
    ok = True

    has_platform = bool(args.platform)
    if has_platform:
        platform = evaluate_platform(platform=args.platform)
        payload["platform"] = {k: v for k, v in platform.__dict__.items() if k != "addresses"}
        ok = ok and platform.ok

    capabilities = _load_capabilities(args.capabilities)
    has_capabilities = bool(args.capabilities)
    addresses: list[str] = []
    if has_capabilities:
        picked = pick_capability(capabilities=capabilities)
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
        payload["cite"] = {k: v for k, v in grounded.__dict__.items() if k != "addresses"}
        ok = ok and grounded.ok

    completeness = require_operator_controls(
        has_platform=has_platform,
        has_capabilities=has_capabilities,
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
