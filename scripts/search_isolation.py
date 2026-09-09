"""ArcticSwarm steal: isolate search before review. Fail closed. No ArcticSwarm."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

PROXY_METRICS = frozenset({"tokens", "pr_velocity", "daily_messages", "agent_count"})
METERED_PLATFORMS = frozenset(
    {
        "arctic_swarm",
        "arcticswarm",
        "more_agents",
        "qwen_primary",
        "miroflow",
        "browsecomp",
    }
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


def evaluate_platform(*, platform: str) -> ControlDecision:
    name = _norm(platform)
    if name in {"local_isolation", "search_isolation", "deferred_consensus"}:
        return ControlDecision(
            action="allow_local_isolation",
            ok=True,
            reason="isolate searches locally, then review evidence",
        )
    if name in METERED_PLATFORMS or "arctic" in name or "swarm" in name:
        return ControlDecision(
            action="block_metered",
            ok=False,
            reason="ArcticSwarm and more-agent stacks stay outside the monthly cap",
        )
    return ControlDecision(
        action="block_metered",
        ok=False,
        reason="unknown isolation platform is denied",
    )


def evaluate_isolation(*, peer_reads_during_search: bool) -> ControlDecision:
    if peer_reads_during_search:
        return ControlDecision(
            action="block_premature_consensus",
            ok=False,
            reason="peer reads during search collapse exploration onto one idea",
        )
    return ControlDecision(
        action="allow_isolated_search",
        ok=True,
        reason="blocked peer reads keep independent search paths",
    )


def evaluate_evidence(*, findings: Sequence[object]) -> ControlDecision:
    cleaned = [str(item).strip() for item in findings if str(item).strip()]
    if cleaned:
        return ControlDecision(
            action="allow_evidence_ready",
            ok=True,
            reason="collaboration waits until findings exist",
        )
    return ControlDecision(
        action="block_no_evidence",
        ok=False,
        reason="do not compare notes before evidence exists",
    )


def evaluate_consensus(*, reviewed: bool, peer_reads_during_search: bool) -> ControlDecision:
    if peer_reads_during_search:
        return ControlDecision(
            action="block_premature_consensus",
            ok=False,
            reason="early peer reads create premature consensus",
        )
    if not reviewed:
        return ControlDecision(
            action="block_unreviewed_consensus",
            ok=False,
            reason="challenge the leading answer before agreeing",
        )
    return ControlDecision(
        action="allow_deferred_review",
        ok=True,
        reason="review happens after isolated search",
    )


def _path_clears(path: Mapping[str, object]) -> bool:
    findings_raw = path.get("findings") or []
    findings = list(findings_raw) if isinstance(findings_raw, Sequence) else []
    isolation = evaluate_isolation(
        peer_reads_during_search=bool(path.get("peer_reads_during_search"))
    )
    evidence = evaluate_evidence(findings=findings)
    consensus = evaluate_consensus(
        reviewed=bool(path.get("reviewed")),
        peer_reads_during_search=bool(path.get("peer_reads_during_search")),
    )
    return isolation.ok and evidence.ok and consensus.ok


def pick_path(*, paths: Sequence[Mapping[str, object]]) -> ControlDecision:
    for raw in paths:
        path_id = str(raw.get("id") or "").strip()
        if path_id and _path_clears(raw):
            return ControlDecision(
                action="allow_isolated_path",
                ok=True,
                reason="keep one isolated path with evidence and deferred review",
                addresses=(f"path:{path_id}",),
            )
    return ControlDecision(
        action="block_no_isolated_path",
        ok=False,
        reason="no path cleared isolation, evidence, and review",
    )


def evaluate_claim(*, cite: str, addresses: Sequence[str]) -> ControlDecision:
    target = (cite or "").strip()
    if target and target in set(addresses):
        return ControlDecision(
            action="allow_on_isolation",
            ok=True,
            reason="cite is the isolated evidence path",
        )
    return ControlDecision(
        action="block_off_isolation",
        ok=False,
        reason="cite is not the isolated evidence path",
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


def require_isolation_controls(
    *,
    has_platform: bool,
    has_paths: bool,
    has_cite: bool,
) -> ControlDecision:
    if has_platform and has_paths and has_cite:
        return ControlDecision(
            action="controls_complete",
            ok=True,
            reason="platform, paths, and cite evaluated",
        )
    return ControlDecision(
        action="block_incomplete_controls",
        ok=False,
        reason="fail closed: missing platform, paths, or cite",
    )


def _load_paths(path: str) -> list[dict[str, object]]:
    if not path:
        return []
    raw = Path(path)
    if not raw.is_file():
        return []
    payload = json.loads(raw.read_text())
    items = payload.get("paths", payload) if isinstance(payload, Mapping) else payload
    return [dict(item) for item in items if isinstance(item, Mapping)]


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Local search isolation before review (no ArcticSwarm)."
    )
    parser.add_argument("--platform", default="")
    parser.add_argument("--paths", default="")
    parser.add_argument("--cite", default="")
    args = parser.parse_args()

    payload: dict[str, object] = {}
    ok = True

    has_platform = bool(args.platform)
    if has_platform:
        platform = evaluate_platform(platform=args.platform)
        payload["platform"] = {k: v for k, v in platform.__dict__.items() if k != "addresses"}
        ok = ok and platform.ok

    paths = _load_paths(args.paths)
    has_paths = bool(args.paths)
    addresses: list[str] = []
    if has_paths:
        picked = pick_path(paths=paths)
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

    completeness = require_isolation_controls(
        has_platform=has_platform,
        has_paths=has_paths,
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
