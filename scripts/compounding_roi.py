"""PlayerZero steal: compounding ROI control plane. Fail closed. No SaaS."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

LIFECYCLE_STAGES = (
    "planning",
    "coding",
    "review",
    "docs",
    "quality",
    "triage",
    "sre",
)

VANITY_METRICS = frozenset(
    {
        "pr_velocity",
        "tokens_consumed",
        "deploy_frequency",
        "sprint_completion",
    }
)
HAWK_METRICS = frozenset(
    {
        "wqtu",
        "paywall_attempt_success",
        "incident_recurrence",
        "defect_escape_rate",
        "mttr",
        "time_to_first_hypothesis",
        "escalations_per_ticket",
        "engineering_capacity_reclaimed",
    }
)
REQUIRED_WORLD_SOURCES = ("code", "telemetry", "deploys", "resolution_history")
CYCLE_LINKS = (
    "quality_to_simulation",
    "simulation_to_prevention",
    "prevention_to_triage",
    "triage_to_knowledge",
    "knowledge_to_simulation",
)
PAYWALL_WEIGHT = 10
WQTU_WEIGHT = 5


@dataclass(frozen=True)
class ControlDecision:
    action: str
    ok: bool
    reason: str


def _norm(value: str) -> str:
    return (value or "").strip().lower()


def evaluate_lifecycle_handoff(
    *,
    source_stage: str,
    target_stages: Iterable[str],
    shared_context_id: str,
) -> ControlDecision:
    source = _norm(source_stage)
    targets = [_norm(item) for item in target_stages if str(item).strip()]
    context = (shared_context_id or "").strip()
    if source not in LIFECYCLE_STAGES:
        return ControlDecision(
            action="block_unknown_stage",
            ok=False,
            reason="handoffs must use a mapped SDLC stage",
        )
    known_targets = [item for item in targets if item in LIFECYCLE_STAGES]
    if not known_targets or not context:
        return ControlDecision(
            action="block_single_player",
            ok=False,
            reason="intelligence reset at handoff; mice stay in their maze",
        )
    return ControlDecision(
        action="allow_multiplayer",
        ok=True,
        reason="shared context id flows to at least one other stage",
    )


def evaluate_hawk_metrics(*, metrics: Iterable[str]) -> ControlDecision:
    names = {_norm(item).replace("-", "_") for item in metrics if str(item).strip()}
    if names & HAWK_METRICS:
        return ControlDecision(
            action="allow_hawk_metrics",
            ok=True,
            reason="prevention or customer-outcome metrics are present",
        )
    return ControlDecision(
        action="block_velocity_proxy",
        ok=False,
        reason="PR velocity and tokens do not prove the org is getting smarter",
    )


def evaluate_prevention_recipe(
    *,
    resolved: bool,
    pattern: str,
    gate: str,
) -> ControlDecision:
    if not resolved:
        return ControlDecision(
            action="block_unresolved",
            ok=False,
            reason="unresolved incidents cannot claim a prevention recipe",
        )
    if not (pattern or "").strip() or not (gate or "").strip():
        return ControlDecision(
            action="block_recovery_only",
            ok=False,
            reason="a local fix without a watch is recovery, not prevention",
        )
    return ControlDecision(
        action="allow_prevention",
        ok=True,
        reason="escaped defect encoded as a reusable gate",
    )


def evaluate_compounding_cycle(*, links: Mapping[str, object]) -> ControlDecision:
    missing = [
        key
        for key in CYCLE_LINKS
        if not bool(links.get(key))
    ]
    if missing:
        return ControlDecision(
            action="block_linear_gains",
            ok=False,
            reason="cycle broken; single-player gains do not compound",
        )
    return ControlDecision(
        action="allow_compounding",
        ok=True,
        reason="quality, simulation, prevention, triage, and knowledge feed each other",
    )


def evaluate_world_model(
    *,
    sources: Iterable[str],
    persists: bool,
) -> ControlDecision:
    have = {_norm(item) for item in sources if str(item).strip()}
    missing = [item for item in REQUIRED_WORLD_SOURCES if item not in have]
    if missing or not persists:
        return ControlDecision(
            action="block_session_reset",
            ok=False,
            reason="session-only memory evaporates; Phase 2 needs a persistent graph",
        )
    return ControlDecision(
        action="allow_world_model",
        ok=True,
        reason="code, telemetry, deploys, and resolutions persist across sessions",
    )


def evaluate_judgment_handoff(
    *,
    root_cause: str,
    blast_radius: str,
    decision: str,
    human_role: str,
) -> ControlDecision:
    role = _norm(human_role)
    cause = (root_cause or "").strip()
    blast = (blast_radius or "").strip()
    call = (decision or "").strip()
    if role != "judgment" or not cause or cause.lower() == "unknown" or not blast or not call:
        return ControlDecision(
            action="block_human_cleanup",
            ok=False,
            reason="agents reconstruct context; humans judge, they do not mop up",
        )
    return ControlDecision(
        action="allow_judgment",
        ok=True,
        reason="investigation assembled; human is spun in for the call only",
    )


def rank_work(*, candidates: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    scored: list[tuple[float, dict[str, object]]] = []
    for raw in candidates:
        row = dict(raw)
        metric = _norm(str(row.get("metric", "")))
        effort = max(float(row.get("effort") or 1), 1.0)
        if metric in VANITY_METRICS:
            score = 0.0
        else:
            paywall = float(row.get("expected_paywall_attempts") or 0)
            wqtu = float(row.get("expected_wqtu_delta") or 0)
            score = (paywall * PAYWALL_WEIGHT + wqtu * WQTU_WEIGHT) / effort
        row["score"] = score
        scored.append((score, row))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [row for _, row in scored]


def require_compounding_controls(
    *,
    has_lifecycle: bool,
    has_metrics: bool,
    has_prevention: bool,
    has_cycle: bool,
    has_world_model: bool,
) -> ControlDecision:
    if has_lifecycle and has_metrics and has_prevention and has_cycle and has_world_model:
        return ControlDecision(
            action="controls_complete",
            ok=True,
            reason="lifecycle, hawk metrics, prevention, cycle, and world model evaluated",
        )
    return ControlDecision(
        action="block_incomplete_controls",
        ok=False,
        reason="fail closed: missing lifecycle, metrics, prevention, cycle, or world model",
    )


def main() -> int:
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Compounding ROI control plane (no SaaS call).")
    parser.add_argument("--source-stage", default="")
    parser.add_argument("--target-stages", default="")
    parser.add_argument("--context-id", default="")
    parser.add_argument("--metrics", default="")
    parser.add_argument("--resolved", action="store_true")
    parser.add_argument("--pattern", default="")
    parser.add_argument("--gate", default="")
    parser.add_argument("--cycle", default="")
    parser.add_argument("--sources", default="")
    parser.add_argument("--persists", action="store_true")
    args = parser.parse_args()

    payload: dict[str, object] = {}
    ok = True

    has_lifecycle = bool(args.source_stage or args.target_stages or args.context_id)
    if has_lifecycle:
        lifecycle = evaluate_lifecycle_handoff(
            source_stage=args.source_stage,
            target_stages=[part.strip() for part in args.target_stages.split(",") if part.strip()],
            shared_context_id=args.context_id,
        )
        payload["lifecycle"] = lifecycle.__dict__
        ok = ok and lifecycle.ok

    has_metrics = bool(args.metrics)
    if has_metrics:
        metrics = evaluate_hawk_metrics(
            metrics=[part.strip() for part in args.metrics.split(",") if part.strip()]
        )
        payload["metrics"] = metrics.__dict__
        ok = ok and metrics.ok

    has_prevention = bool(args.resolved or args.pattern or args.gate)
    if has_prevention:
        prevention = evaluate_prevention_recipe(
            resolved=bool(args.resolved),
            pattern=args.pattern,
            gate=args.gate,
        )
        payload["prevention"] = prevention.__dict__
        ok = ok and prevention.ok

    has_cycle = bool(args.cycle)
    if has_cycle:
        links = {
            key: True
            for key in (part.strip() for part in args.cycle.split(",") if part.strip())
        }
        cycle = evaluate_compounding_cycle(links=links)
        payload["cycle"] = cycle.__dict__
        ok = ok and cycle.ok

    has_world_model = bool(args.sources or args.persists)
    if has_world_model:
        world = evaluate_world_model(
            sources=[part.strip() for part in args.sources.split(",") if part.strip()],
            persists=bool(args.persists),
        )
        payload["world_model"] = world.__dict__
        ok = ok and world.ok

    completeness = require_compounding_controls(
        has_lifecycle=has_lifecycle,
        has_metrics=has_metrics,
        has_prevention=has_prevention,
        has_cycle=has_cycle,
        has_world_model=has_world_model,
    )
    payload["completeness"] = completeness.__dict__
    ok = ok and completeness.ok

    print(json.dumps(payload, indent=2))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
