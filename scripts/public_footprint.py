"""Metabigor steal: free public sources for owned surfaces. Fail closed. No recon."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

OWNED_PLAY = "com.iganapolsky.randomtimer"
OWNED_ITUNES = "6758355312"
OWNED_IOS_BUNDLE = "com.igorganapolsky.randomtimer"
OWNED_GITHUB = "igorganapolsky/random-timer"
PROXY_METRICS = frozenset({"tokens", "pr_velocity", "daily_messages", "recon_hops"})
RECON_ENGINES = frozenset(
    {
        "metabigor",
        "shodan",
        "shodan_internetdb",
        "internetdb",
        "crt",
        "crt_sh",
        "grep_app",
        "zoomeye",
        "fofa",
        "censys",
    }
)
METERED_ENGINES = frozenset(
    {"virustotal", "intelx", "urlscan_paid", "builtwith", "viewdns"}
)
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


def _slug(value: str) -> str:
    return (value or "").strip().lower()


def evaluate_engine(*, engine: str) -> ControlDecision:
    name = _norm(engine)
    if name in {"public_owned", "local_public", "owned_public"}:
        return ControlDecision(
            action="allow_public_owned",
            ok=True,
            reason="compose owned Play, iTunes, and GitHub from free public reads",
        )
    if name in RECON_ENGINES or "metabigor" in name or "shodan" in name:
        return ControlDecision(
            action="block_recon",
            ok=False,
            reason="do not install metabigor or scan third-party infra",
        )
    if name in METERED_ENGINES or "virustotal" in name or "intelx" in name:
        return ControlDecision(
            action="block_metered",
            ok=False,
            reason="paid OSINT keys are outside the monthly cap",
        )
    return ControlDecision(
        action="block_recon",
        ok=False,
        reason="unknown footprint engine is denied",
    )


def evaluate_target(*, target: str) -> ControlDecision:
    raw = (target or "").strip()
    lowered = raw.lower()
    owned = {
        OWNED_PLAY,
        OWNED_ITUNES,
        OWNED_IOS_BUNDLE,
        OWNED_GITHUB,
        f"https://play.google.com/store/apps/details?id={OWNED_PLAY}",
        f"https://apps.apple.com/us/app/random-tactical-timer/id{OWNED_ITUNES}",
        "https://github.com/igorganapolsky/random-timer",
    }
    if lowered in owned or OWNED_PLAY in lowered or OWNED_ITUNES in lowered:
        if "igorganapolsky/random-timer" in lowered.replace("_", "-") or lowered in {
            OWNED_PLAY,
            OWNED_ITUNES,
            OWNED_IOS_BUNDLE,
            OWNED_GITHUB,
        }:
            return ControlDecision(
                action="allow_owned",
                ok=True,
                reason="target is an owned Random Timer public identity",
            )
        if OWNED_PLAY in lowered or OWNED_ITUNES in lowered:
            return ControlDecision(
                action="allow_owned",
                ok=True,
                reason="target is an owned Random Timer public identity",
            )
    if OWNED_GITHUB in lowered.replace("_", "-"):
        return ControlDecision(
            action="allow_owned",
            ok=True,
            reason="target is an owned Random Timer public identity",
        )
    return ControlDecision(
        action="block_off_scope",
        ok=False,
        reason="third-party hosts are out of scope",
    )


def _hit(*, kind: str, identity: str, status: object, body: str, result_count: object) -> str:
    ident = (identity or "").strip()
    code = int(status or 0)
    if code != 200 or not ident:
        return ""
    if kind == "play":
        if _slug(ident) != OWNED_PLAY or OWNED_PLAY not in (body or "").lower():
            return ""
        return f"play:{ident}"
    if kind == "itunes":
        if ident != OWNED_ITUNES or int(result_count or 0) < 1:
            return ""
        return f"itunes:{ident}"
    if kind == "github":
        if _slug(ident).replace("_", "-") != OWNED_GITHUB:
            return ""
        return f"github:{ident}"
    return ""


def compose_footprint(*, sources: Sequence[Mapping[str, object]]) -> ControlDecision:
    addresses: list[str] = []
    for raw in sources:
        kind = _slug(str(raw.get("kind", "")))
        address = _hit(
            kind=kind,
            identity=str(raw.get("identity", "")),
            status=raw.get("status"),
            body=str(raw.get("body", "")),
            result_count=raw.get("result_count"),
        )
        if address:
            addresses.append(address)
    if addresses:
        return ControlDecision(
            action="allow_compose",
            ok=True,
            reason="public owned surfaces read back without API keys",
            addresses=tuple(addresses),
        )
    return ControlDecision(
        action="block_empty_footprint",
        ok=False,
        reason="no owned public surface returned a verified hit",
    )


def evaluate_claim(*, cite: str, addresses: Sequence[str]) -> ControlDecision:
    target = (cite or "").strip()
    if target and target in set(addresses):
        return ControlDecision(
            action="allow_on_footprint",
            ok=True,
            reason="cite sits on a composed public owned surface",
        )
    return ControlDecision(
        action="block_off_footprint",
        ok=False,
        reason="cite is not a verified owned public surface",
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


def require_footprint_controls(
    *,
    has_engine: bool,
    has_target: bool,
    has_sources: bool,
    has_cite: bool,
) -> ControlDecision:
    if has_engine and has_target and has_sources and has_cite:
        return ControlDecision(
            action="controls_complete",
            ok=True,
            reason="engine, target, sources, and cite evaluated",
        )
    return ControlDecision(
        action="block_incomplete_controls",
        ok=False,
        reason="fail closed: missing engine, target, sources, or cite",
    )


def _load_sources(path: str) -> list[dict[str, object]]:
    if not path:
        return []
    raw = Path(path)
    if not raw.is_file():
        return []
    payload = json.loads(raw.read_text())
    if isinstance(payload, dict):
        items = payload.get("sources", [])
    else:
        items = payload
    return [dict(item) for item in items if isinstance(item, Mapping)]


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Owned public footprint (no metabigor).")
    parser.add_argument("--engine", default="")
    parser.add_argument("--target", default="")
    parser.add_argument("--sources", default="")
    parser.add_argument("--cite", default="")
    args = parser.parse_args()

    payload: dict[str, object] = {}
    ok = True

    has_engine = bool(args.engine)
    if has_engine:
        engine = evaluate_engine(engine=args.engine)
        payload["engine"] = {k: v for k, v in engine.__dict__.items() if k != "addresses"}
        ok = ok and engine.ok

    has_target = bool(args.target)
    if has_target:
        scoped = evaluate_target(target=args.target)
        payload["target"] = {k: v for k, v in scoped.__dict__.items() if k != "addresses"}
        ok = ok and scoped.ok

    sources = _load_sources(args.sources)
    has_sources = bool(args.sources)
    addresses: list[str] = []
    if has_sources:
        composed = compose_footprint(sources=sources)
        payload["compose"] = {
            "action": composed.action,
            "ok": composed.ok,
            "reason": composed.reason,
            "addresses": list(composed.addresses),
        }
        addresses = list(composed.addresses)
        ok = ok and composed.ok

    has_cite = bool(args.cite)
    if has_cite:
        grounded = evaluate_claim(cite=args.cite, addresses=addresses)
        payload["cite"] = {k: v for k, v in grounded.__dict__.items() if k != "addresses"}
        ok = ok and grounded.ok

    completeness = require_footprint_controls(
        has_engine=has_engine,
        has_target=has_target,
        has_sources=has_sources,
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
