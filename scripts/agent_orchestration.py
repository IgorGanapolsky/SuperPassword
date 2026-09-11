"""Local multi-agent orchestration patterns for Random Timer (zero external cost)."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any, Literal, Mapping, Sequence

Pattern = Literal["sequential", "concurrent", "group_chat", "handoff", "hierarchical"]

ALLOWED_PLATFORMS = frozenset(
    {
        "local_agent_orchestration",
        "agent_orchestration",
        "local_multi_agent",
    }
)
DENIED_MARKERS = (
    "enterprise_agent_cloud",
    "agent_mesh_saas",
    "external_orchestration_vendor",
)
DEFAULT_MAX_HANDOFFS = 3
DEFAULT_MIN_CONFIDENCE = 0.7
DEFAULT_MAX_DISCUSSION_TURNS = 6


@dataclass(frozen=True)
class ControlDecision:
    action: str
    ok: bool
    reason: str


@dataclass(frozen=True)
class StepSpec:
    agent: str
    requires_gate: bool
    role: str = "worker"


@dataclass(frozen=True)
class WorkflowPlan:
    intent: str
    pattern: Pattern
    steps: tuple[StepSpec, ...]
    inter_step_validation: bool
    max_handoffs: int
    conflict_method: str
    reason: str


@dataclass(frozen=True)
class ReconcileResult:
    ok: bool
    action: str
    winner: dict[str, Any] | None
    reason: str


def _norm(value: str) -> str:
    return (
        (value or "")
        .strip()
        .lower()
        .replace("-", "_")
        .replace(".", "_")
        .replace(" ", "_")
    )


def evaluate_platform(*, platform: str) -> ControlDecision:
    name = _norm(platform)
    if name in ALLOWED_PLATFORMS:
        return ControlDecision(
            action="allow_local_orchestration",
            ok=True,
            reason="local orchestration under operating cap",
        )
    if any(marker in name for marker in DENIED_MARKERS):
        return ControlDecision(
            action="block_external_orchestration_vendor",
            ok=False,
            reason="external orchestration vendor denied",
        )
    return ControlDecision(
        action="block_external_orchestration_vendor",
        ok=False,
        reason="unknown platform denied",
    )


def choose_pattern(
    *,
    intent: str,
    needs_parallel: bool = False,
    unknown_route: bool = False,
    needs_debate: bool = False,
    needs_supervisor: bool = False,
) -> Pattern:
    _ = intent
    if needs_supervisor:
        return "hierarchical"
    if needs_debate:
        return "group_chat"
    if unknown_route:
        return "handoff"
    if needs_parallel:
        return "concurrent"
    return "sequential"


def validate_step_gate(
    *,
    confidence: float,
    min_confidence: float = DEFAULT_MIN_CONFIDENCE,
    output_ok: bool = True,
) -> ControlDecision:
    if not output_ok:
        return ControlDecision(
            action="block_error_propagation",
            ok=False,
            reason="bad prior output",
        )
    if confidence < min_confidence:
        return ControlDecision(
            action="escalate_human_or_supervisor",
            ok=False,
            reason=f"confidence {confidence:.2f} < {min_confidence:.2f}",
        )
    return ControlDecision(
        action="allow_next_step",
        ok=True,
        reason="gate passed",
    )


def validate_handoff(
    *,
    from_agent: str,
    to_agent: str,
    handoff_count: int,
    max_handoffs: int = DEFAULT_MAX_HANDOFFS,
    recent_path: Sequence[str] = (),
) -> ControlDecision:
    path = tuple(recent_path) + (from_agent, to_agent)
    if len(path) >= 3:
        for i in range(len(path) - 2):
            if path[i] == path[i + 2] and path[i] != path[i + 1]:
                return ControlDecision(
                    action="block_handoff_loop",
                    ok=False,
                    reason="loop detected",
                )
    if handoff_count >= max_handoffs:
        return ControlDecision(
            action="escalate_after_max_handoffs",
            ok=False,
            reason="max handoffs reached",
        )
    if _norm(from_agent) == _norm(to_agent):
        return ControlDecision(
            action="block_handoff_loop",
            ok=False,
            reason="self-handoff refused",
        )
    return ControlDecision(
        action="allow_handoff",
        ok=True,
        reason=f"{from_agent}->{to_agent}",
    )


def validate_group_chat(
    *,
    discussion_turns: int,
    max_turns: int = DEFAULT_MAX_DISCUSSION_TURNS,
    converged: bool = False,
) -> ControlDecision:
    if converged:
        return ControlDecision(
            action="allow_group_chat_result",
            ok=True,
            reason="discussion converged",
        )
    if discussion_turns >= max_turns:
        return ControlDecision(
            action="escalate_after_max_discussion_turns",
            ok=False,
            reason="max discussion turns reached",
        )
    return ControlDecision(
        action="continue_group_chat",
        ok=True,
        reason="discussion may continue",
    )


def reconcile_concurrent(
    *,
    outputs: Sequence[Mapping[str, Any]],
    method: str = "confidence",
) -> ReconcileResult:
    rows = [dict(item) for item in outputs]
    if not rows:
        return ReconcileResult(
            ok=False,
            action="escalate_unresolvable_conflict",
            winner=None,
            reason="no outputs",
        )
    if method == "confidence":
        winner = max(rows, key=lambda row: float(row.get("confidence") or 0.0))
        return ReconcileResult(
            ok=True,
            action="select_highest_confidence",
            winner=winner,
            reason="confidence winner",
        )
    counts = Counter(str(row.get("conclusion")) for row in rows)
    top, top_n = counts.most_common(1)[0]
    tied = [conclusion for conclusion, count in counts.items() if count == top_n]
    if len(tied) > 1:
        return ReconcileResult(
            ok=False,
            action="escalate_unresolvable_conflict",
            winner=None,
            reason=f"tie {tied}",
        )
    winners = [row for row in rows if str(row.get("conclusion")) == top]
    winner = max(winners, key=lambda row: float(row.get("confidence") or 0.0))
    return ReconcileResult(
        ok=True,
        action="select_majority",
        winner=winner,
        reason=f"majority {top}",
    )


def plan_workflow(
    *,
    intent: str,
    agents: Sequence[str],
    needs_parallel: bool = False,
    unknown_route: bool = False,
    needs_debate: bool = False,
    needs_supervisor: bool = False,
) -> WorkflowPlan:
    pattern = choose_pattern(
        intent=intent,
        needs_parallel=needs_parallel,
        unknown_route=unknown_route,
        needs_debate=needs_debate,
        needs_supervisor=needs_supervisor,
    )
    names = tuple(agent for agent in agents if agent) or ("triage",)
    if pattern == "concurrent":
        steps = tuple(
            StepSpec(agent=agent, requires_gate=False, role="parallel_worker")
            for agent in names
        )
        return WorkflowPlan(
            intent=intent,
            pattern=pattern,
            steps=steps,
            inter_step_validation=False,
            max_handoffs=DEFAULT_MAX_HANDOFFS,
            conflict_method="confidence",
            reason="parallel then reconcile",
        )
    if pattern == "handoff":
        steps = (StepSpec(agent=names[0], requires_gate=True, role="triage"),) + tuple(
            StepSpec(agent=agent, requires_gate=True, role="specialist")
            for agent in names[1:]
        )
        return WorkflowPlan(
            intent=intent,
            pattern=pattern,
            steps=steps,
            inter_step_validation=True,
            max_handoffs=DEFAULT_MAX_HANDOFFS,
            conflict_method="confidence",
            reason="runtime handoffs",
        )
    if pattern == "group_chat":
        steps = tuple(
            StepSpec(agent=agent, requires_gate=False, role="discussant")
            for agent in names
        )
        return WorkflowPlan(
            intent=intent,
            pattern=pattern,
            steps=steps,
            inter_step_validation=True,
            max_handoffs=DEFAULT_MAX_HANDOFFS,
            conflict_method="confidence",
            reason="shared thread with turn cap",
        )
    if pattern == "hierarchical":
        supervisor = names[0]
        workers = names[1:] or ("worker",)
        steps = (StepSpec(agent=supervisor, requires_gate=True, role="supervisor"),) + tuple(
            StepSpec(agent=agent, requires_gate=True, role="worker") for agent in workers
        )
        return WorkflowPlan(
            intent=intent,
            pattern=pattern,
            steps=steps,
            inter_step_validation=True,
            max_handoffs=DEFAULT_MAX_HANDOFFS,
            conflict_method="confidence",
            reason="supervisor directs workers",
        )
    steps = tuple(
        StepSpec(agent=agent, requires_gate=(index < len(names) - 1), role="pipeline")
        for index, agent in enumerate(names)
    )
    return WorkflowPlan(
        intent=intent,
        pattern="sequential",
        steps=steps,
        inter_step_validation=True,
        max_handoffs=DEFAULT_MAX_HANDOFFS,
        conflict_method="confidence",
        reason="sequential with gates",
    )


__all__ = [
    "ControlDecision",
    "ReconcileResult",
    "StepSpec",
    "WorkflowPlan",
    "choose_pattern",
    "evaluate_platform",
    "plan_workflow",
    "reconcile_concurrent",
    "validate_group_chat",
    "validate_handoff",
    "validate_step_gate",
]
