"""OpenAI Friar steal: completed-task ROI. Fail closed. No SaaS."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

MONTHLY_CAP_USD = 20
COMPLETED_TASK_METRICS = frozenset(
    {"wqtu", "timer_completed", "iap_attempt", "paywall_attempt_success"}
)
PROXY_METRICS = frozenset(
    {"tokens", "pr_velocity", "daily_messages", "weekly_active_users"}
)
ALLOWED_SERVICES = frozenset(
    {"hermes_main", "local_pytest", "github_actions_minutes", "local_gist"}
)
METERED_SERVICES = frozenset(
    {
        "gpt6_astra",
        "jalapeno",
        "ori",
        "openrouter_primary",
        "foundry_model_router",
        "openai_api_primary",
    }
)
WEAK_MODEL_MARKERS = ("hermes-local", "qwen2.5:3b", "3b-hermes", "muse-spark")
IAP_WEIGHT = 10
TASK_WEIGHT = 5


@dataclass(frozen=True)
class ControlDecision:
    action: str
    ok: bool
    reason: str


def _norm(value: str) -> str:
    return (value or "").strip().lower().replace("-", "_")


def _is_weak(model: str) -> bool:
    lowered = (model or "").strip().lower()
    return any(marker in lowered for marker in WEAK_MODEL_MARKERS)


def evaluate_completed_task(*, metric: str) -> ControlDecision:
    name = _norm(metric)
    if name in COMPLETED_TASK_METRICS:
        return ControlDecision(
            action="allow_completed_task",
            ok=True,
            reason="result is a finished user or IAP task, not tokens",
        )
    return ControlDecision(
        action="block_proxy_output",
        ok=False,
        reason="tokens and PR velocity are not the completed task",
    )


def evaluate_attempt_efficiency(*, attempts: int, completed: int) -> ControlDecision:
    if int(completed) >= 1:
        return ControlDecision(
            action="allow_efficient",
            ok=True,
            reason="at least one attempt reached a finished task",
        )
    return ControlDecision(
        action="block_attempts_without_finish",
        ok=False,
        reason="more attempts without a finish is not more work within reach",
    )


def evaluate_capital_discipline(
    *,
    service: str,
    monthly_usd: float,
    month_to_date_usd: float,
    demand: str,
    days_to_productive: float,
) -> ControlDecision:
    name = _norm(service)
    remaining = MONTHLY_CAP_USD - float(month_to_date_usd)
    if float(monthly_usd) > remaining:
        return ControlDecision(
            action="block_over_cap",
            ok=False,
            reason="returns do not justify capital above the monthly cap",
        )
    if name in METERED_SERVICES:
        return ControlDecision(
            action="block_metered",
            ok=False,
            reason="new metered models and chips are outside the cap",
        )
    if name not in ALLOWED_SERVICES or not (demand or "").strip():
        return ControlDecision(
            action="block_metered",
            ok=False,
            reason="unknown service or unnamed demand is denied",
        )
    if float(days_to_productive) > 14:
        return ControlDecision(
            action="block_over_cap",
            ok=False,
            reason="too slow to become productive under capital discipline",
        )
    return ControlDecision(
        action="allow_capital",
        ok=True,
        reason="local or already-paid capacity, named demand, fast to productive",
    )


def evaluate_workload_fit(*, task_kind: str, model: str) -> ControlDecision:
    kind = _norm(task_kind)
    if kind == "tool_turn" and _is_weak(model):
        return ControlDecision(
            action="block_weak_route",
            ok=False,
            reason="tool turns need a capable route, not a 3B babysit",
        )
    if kind == "tool_turn" and "hermes" in (model or "").strip().lower() and "main" in (model or "").strip().lower():
        return ControlDecision(
            action="allow_fit",
            ok=True,
            reason="interactive tool work uses the capable stack",
        )
    if kind == "classify" and _is_weak(model):
        return ControlDecision(
            action="allow_fit",
            ok=True,
            reason="cheap local is enough for classify-only work",
        )
    if kind == "tool_turn":
        return ControlDecision(
            action="block_weak_route",
            ok=False,
            reason="unknown tool-turn model is denied",
        )
    return ControlDecision(
        action="allow_fit",
        ok=True,
        reason="workload matches a cheap capable route",
    )


def evaluate_discovery_to_paid(
    *,
    timer_completed: int,
    paywall_shown: bool,
) -> ControlDecision:
    if paywall_shown and int(timer_completed) < 1:
        return ControlDecision(
            action="block_premature_wall",
            ok=False,
            reason="free discovery must finish a training session before the wall",
        )
    return ControlDecision(
        action="allow_earned_wall",
        ok=True,
        reason="wall follows a completed task, or no wall yet",
    )


def evaluate_human_judgment(
    *,
    human_role: str,
    priority_set: bool,
    result_judged: bool,
) -> ControlDecision:
    if _norm(human_role) == "judgment" and priority_set and result_judged:
        return ControlDecision(
            action="allow_judgment",
            ok=True,
            reason="humans set priorities and judge; agents execute",
        )
    return ControlDecision(
        action="block_human_cleanup",
        ok=False,
        reason="agents take specialist time; humans do not mop up",
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


def require_reach_controls(
    *,
    has_task: bool,
    has_efficiency: bool,
    has_capital: bool,
    has_fit: bool,
    has_discovery: bool,
) -> ControlDecision:
    if has_task and has_efficiency and has_capital and has_fit and has_discovery:
        return ControlDecision(
            action="controls_complete",
            ok=True,
            reason="completed-task, efficiency, capital, fit, and discovery evaluated",
        )
    return ControlDecision(
        action="block_incomplete_controls",
        ok=False,
        reason="fail closed: missing completed-task, efficiency, capital, fit, or discovery",
    )


def main() -> int:
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Work within reach control plane (no SaaS).")
    parser.add_argument("--metric", default="")
    parser.add_argument("--attempts", default="")
    parser.add_argument("--completed", default="")
    parser.add_argument("--service", default="")
    parser.add_argument("--monthly-usd", default="0")
    parser.add_argument("--mtd-usd", default="0")
    parser.add_argument("--demand", default="")
    parser.add_argument("--days-to-productive", default="0")
    parser.add_argument("--task-kind", default="")
    parser.add_argument("--model", default="")
    parser.add_argument("--timer-completed", default="")
    parser.add_argument("--paywall-shown", action="store_true")
    args = parser.parse_args()

    payload: dict[str, object] = {}
    ok = True

    has_task = bool(args.metric)
    if has_task:
        task = evaluate_completed_task(metric=args.metric)
        payload["task"] = task.__dict__
        ok = ok and task.ok

    has_efficiency = args.attempts != "" or args.completed != ""
    if has_efficiency:
        efficiency = evaluate_attempt_efficiency(
            attempts=int(args.attempts or 0),
            completed=int(args.completed or 0),
        )
        payload["efficiency"] = efficiency.__dict__
        ok = ok and efficiency.ok

    has_capital = bool(args.service or args.demand)
    if has_capital:
        capital = evaluate_capital_discipline(
            service=args.service,
            monthly_usd=float(args.monthly_usd or 0),
            month_to_date_usd=float(args.mtd_usd or 0),
            demand=args.demand,
            days_to_productive=float(args.days_to_productive or 0),
        )
        payload["capital"] = capital.__dict__
        ok = ok and capital.ok

    has_fit = bool(args.task_kind or args.model)
    if has_fit:
        fit = evaluate_workload_fit(task_kind=args.task_kind, model=args.model)
        payload["fit"] = fit.__dict__
        ok = ok and fit.ok

    has_discovery = args.timer_completed != "" or args.paywall_shown
    if has_discovery:
        discovery = evaluate_discovery_to_paid(
            timer_completed=int(args.timer_completed or 0),
            paywall_shown=bool(args.paywall_shown),
        )
        payload["discovery"] = discovery.__dict__
        ok = ok and discovery.ok

    completeness = require_reach_controls(
        has_task=has_task,
        has_efficiency=has_efficiency,
        has_capital=has_capital,
        has_fit=has_fit,
        has_discovery=has_discovery,
    )
    payload["completeness"] = completeness.__dict__
    ok = ok and completeness.ok

    print(json.dumps(payload, indent=2))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
