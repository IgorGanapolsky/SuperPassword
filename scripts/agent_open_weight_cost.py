"""Open-weight cost episode steal: unit economics + routing for model choice. Fail closed."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

PROXY_METRICS = frozenset(
    {
        "open_source_purity",
        "vendor_independence_score",
        "leaderboard_elo",
        "parameter_count",
        "press_mentions",
        "hacker_news_upvotes",
    }
)
DENIED_PLATFORMS = frozenset(
    {
        "gpu_fleet_ideology_spend",
        "a100_self_host_vanity",
        "open_weight_cloud_over_cap",
        "always_self_host_policy",
        "benchmark_only_swap",
    }
)
ALLOWED_PLATFORMS = frozenset(
    {
        "local_open_weight_cost",
        "agent_open_weight_cost",
        "hybrid_model_routing",
        "api_first_exploration",
        "ops_unit_economics",
    }
)
DOMAIN_METRICS = frozenset(
    {
        "iap_attempt",
        "wqtu",
        "timer_completed",
        "paywall_attempt",
        "store_version_verify",
        "successful_task",
        "cost_per_success",
        "human_review_minutes",
    }
)
IAP_WEIGHT = 10
TASK_WEIGHT = 5
MONTHLY_CAP_USD = 20.0


@dataclass(frozen=True)
class ControlDecision:
    action: str
    ok: bool
    reason: str
    addresses: tuple[str, ...] = ()
    value: float | None = None


def _norm(value: str) -> str:
    return (value or "").strip().lower().replace("-", "_").replace(".", "_")


def evaluate_platform(*, platform: str) -> ControlDecision:
    name = _norm(platform)
    if name in ALLOWED_PLATFORMS:
        return ControlDecision(
            action="allow_local_open_weight_cost",
            ok=True,
            reason="run open-weight unit-economics gates locally under the monthly cap",
        )
    if name in DENIED_PLATFORMS or "ideology" in name or "vanity" in name:
        return ControlDecision(
            action="block_ideology_spend",
            ok=False,
            reason="self-host GPU fleets for ideology/vendor-independence vanity stay denied",
        )
    return ControlDecision(
        action="block_ideology_spend",
        ok=False,
        reason="unknown open-weight cost platform is denied",
    )


def evaluate_baseline(
    *,
    monthly_api_spend_known: bool,
    tokens_by_task_known: bool,
    latency_known: bool,
    error_retry_known: bool,
    human_review_known: bool,
) -> ControlDecision:
    if (
        monthly_api_spend_known
        and tokens_by_task_known
        and latency_known
        and error_retry_known
        and human_review_known
    ):
        return ControlDecision(
            action="allow_baseline",
            ok=True,
            reason="workload baseline covers spend, tokens, latency, errors, and human review",
        )
    return ControlDecision(
        action="block_missing_baseline",
        ok=False,
        reason="capture monthly spend, tokens by task, latency, error/retry, and human-review time first",
    )


def evaluate_workload_fit(
    *,
    stable_high_volume: bool,
    quality_bar_measurable: bool,
    sporadic_low_volume: bool,
) -> ControlDecision:
    if sporadic_low_volume and not stable_high_volume:
        return ControlDecision(
            action="block_sporadic_self_host",
            ok=False,
            reason="open-weight self-host ROI is weak for sporadic low-volume demand",
        )
    if stable_high_volume and quality_bar_measurable:
        return ControlDecision(
            action="allow_open_weight_candidate",
            ok=True,
            reason="stable high-volume task with a measurable quality bar is an open-weight candidate",
        )
    return ControlDecision(
        action="block_unfit_workload",
        ok=False,
        reason="need stable volume plus a measurable quality bar before open-weight commit",
    )


def evaluate_apples_to_apples(
    *,
    real_prompts: bool,
    real_failure_cases: bool,
    measured_task_success: bool,
    measured_schema_adherence: bool,
    measured_human_intervention: bool,
    benchmark_only: bool,
) -> ControlDecision:
    if benchmark_only:
        return ControlDecision(
            action="block_benchmark_only",
            ok=False,
            reason="leaderboard scores alone are not an apples-to-apples evaluation",
        )
    if (
        real_prompts
        and real_failure_cases
        and measured_task_success
        and measured_schema_adherence
        and measured_human_intervention
    ):
        return ControlDecision(
            action="allow_real_eval",
            ok=True,
            reason="eval uses real prompts/failures with success, schema, and intervention metrics",
        )
    return ControlDecision(
        action="block_incomplete_eval",
        ok=False,
        reason="measure task success, schema adherence, and human intervention on real workloads",
    )


def fully_loaded_cost_per_success(
    *,
    monthly_operating_cost_usd: float,
    successful_tasks_per_month: float,
) -> float | None:
    if successful_tasks_per_month <= 0:
        return None
    return float(monthly_operating_cost_usd) / float(successful_tasks_per_month)


def evaluate_fully_loaded_cost(
    *,
    monthly_operating_cost_usd: float,
    successful_tasks_per_month: float,
    includes_hosting_ops_review: bool,
    utilization_adequate: bool,
) -> ControlDecision:
    unit = fully_loaded_cost_per_success(
        monthly_operating_cost_usd=monthly_operating_cost_usd,
        successful_tasks_per_month=successful_tasks_per_month,
    )
    if unit is None:
        return ControlDecision(
            action="block_zero_success",
            ok=False,
            reason="cannot compute fully loaded cost with zero successful tasks",
            value=None,
        )
    if not includes_hosting_ops_review:
        return ControlDecision(
            action="block_incomplete_tco",
            ok=False,
            reason="TCO must include hosting, infra, observability, on-call, and review time",
            value=unit,
        )
    if not utilization_adequate:
        return ControlDecision(
            action="block_low_utilization",
            ok=False,
            reason="self-host is not cheaper when utilization is low or failures inflate review cost",
            value=unit,
        )
    if monthly_operating_cost_usd > MONTHLY_CAP_USD:
        return ControlDecision(
            action="block_over_monthly_cap",
            ok=False,
            reason=f"operating cost exceeds ${MONTHLY_CAP_USD:.0f}/month hard cap",
            value=unit,
        )
    return ControlDecision(
        action="allow_tco_computed",
        ok=True,
        reason="fully loaded cost per successful task computed with adequate utilization",
        value=unit,
    )


def evaluate_routing(
    *,
    cheap_first_pass: bool,
    escalate_low_confidence: bool,
    all_open_forced: bool,
    all_proprietary_forced: bool,
) -> ControlDecision:
    if all_open_forced or all_proprietary_forced:
        return ControlDecision(
            action="block_monoculture",
            ok=False,
            reason="all-open or all-proprietary standardization usually loses to hybrid routing",
        )
    if cheap_first_pass and escalate_low_confidence:
        return ControlDecision(
            action="allow_hybrid_routing",
            ok=True,
            reason="routine first-pass on inexpensive models; escalate low-confidence/high-stakes",
        )
    return ControlDecision(
        action="block_no_routing",
        ok=False,
        reason="require cheap first-pass plus escalation path for complex/high-stakes work",
    )


def evaluate_strategic_leverage(
    *,
    data_locality: bool,
    custom_finetune: bool,
    offline_edge: bool,
    predictable_marginal_cost: bool,
    vendor_independence_only: bool,
) -> ControlDecision:
    if vendor_independence_only and not any(
        (data_locality, custom_finetune, offline_edge, predictable_marginal_cost)
    ):
        return ControlDecision(
            action="block_vendor_independence_vanity",
            ok=False,
            reason="do not self-host merely to avoid vendor dependence when APIs are cheaper/more reliable",
        )
    if data_locality or custom_finetune or offline_edge or predictable_marginal_cost:
        return ControlDecision(
            action="allow_strategic_open_weight",
            ok=True,
            reason="open weights justified by locality, fine-tune, edge, or predictable marginal cost",
        )
    return ControlDecision(
        action="block_no_strategic_leverage",
        ok=False,
        reason="open-weight commit needs strategic leverage beyond ideology",
    )


def evaluate_pilot(
    *,
    quality_within_tolerance: bool,
    latency_meets_ux: bool,
    savings_exceed_ops_cost: bool,
    review_window_days: int,
    api_fallback: bool,
) -> ControlDecision:
    if not (30 <= int(review_window_days) <= 60):
        return ControlDecision(
            action="block_bad_review_window",
            ok=False,
            reason="pilot needs a 30–60 day review window with clear gates",
        )
    if not api_fallback:
        return ControlDecision(
            action="block_no_fallback",
            ok=False,
            reason="retain an API fallback during the open-weight pilot",
        )
    if quality_within_tolerance and latency_meets_ux and savings_exceed_ops_cost:
        return ControlDecision(
            action="allow_pilot_pass",
            ok=True,
            reason="pilot gates met: quality, latency, and savings exceed ongoing ops cost",
        )
    return ControlDecision(
        action="block_pilot_gates",
        ok=False,
        reason="quality, latency, or savings-vs-ops gates failed — keep API path",
    )


def evaluate_exploration_vs_commit(
    *,
    exploration_phase: bool,
    utilization_justifies: bool,
    tco_justifies: bool,
) -> ControlDecision:
    if exploration_phase and not (utilization_justifies and tco_justifies):
        return ControlDecision(
            action="allow_api_first",
            ok=True,
            reason="use APIs for exploration and variable demand until utilization and TCO justify open weights",
        )
    if utilization_justifies and tco_justifies:
        return ControlDecision(
            action="allow_open_weight_commit",
            ok=True,
            reason="utilization and fully loaded cost modeling justify moving repeatable volume to open weights",
        )
    return ControlDecision(
        action="block_premature_commit",
        ok=False,
        reason="do not commit to open weights before utilization and TCO evidence",
    )


def _workload_clears(raw: Mapping[str, object]) -> bool:
    return evaluate_platform(platform=str(raw.get("platform") or "")).ok


def pick_workload(*, workloads: Sequence[Mapping[str, object]]) -> ControlDecision:
    for raw in workloads:
        wid = str(raw.get("id") or "").strip()
        if wid and _workload_clears(raw):
            return ControlDecision(
                action="allow_local_workload",
                ok=True,
                reason="local open-weight cost workload cleared",
                addresses=(f"owc:{wid}",),
            )
    return ControlDecision(
        action="block_no_local_workload",
        ok=False,
        reason="no workload cleared local open-weight cost gates",
    )


def evaluate_claim(*, cite: str, addresses: Sequence[str]) -> ControlDecision:
    target = (cite or "").strip()
    if target and target in set(addresses):
        return ControlDecision(
            action="allow_on_open_weight_cost",
            ok=True,
            reason="cite is the local open-weight cost workload address",
        )
    return ControlDecision(
        action="block_off_open_weight_cost",
        ok=False,
        reason="cite is not the local open-weight cost address",
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


def require_open_weight_cost_controls(
    *,
    has_platform: bool,
    has_workloads: bool,
    has_cite: bool,
) -> ControlDecision:
    if has_platform and has_workloads and has_cite:
        return ControlDecision(
            action="controls_complete",
            ok=True,
            reason="platform, workloads, and cite evaluated",
        )
    return ControlDecision(
        action="block_incomplete_controls",
        ok=False,
        reason="fail closed: missing platform, workloads, or cite",
    )


def _load_workloads(path: str) -> list[dict[str, object]]:
    if not path:
        return []
    raw = Path(path)
    if not raw.is_file():
        return []
    payload = json.loads(raw.read_text())
    items = payload.get("workloads", payload) if isinstance(payload, Mapping) else payload
    return [dict(item) for item in items if isinstance(item, Mapping)]


def _truthy(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def _decision_payload(d: ControlDecision) -> dict[str, object]:
    out: dict[str, object] = {
        "action": d.action,
        "ok": d.ok,
        "reason": d.reason,
    }
    if d.value is not None:
        out["value"] = d.value
    return out


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Open-weight unit-economics controls (no ideology GPU fleets)."
    )
    parser.add_argument("--platform", default="")
    parser.add_argument("--workloads", default="")
    parser.add_argument("--cite", default="")
    parser.add_argument("--monthly-api-spend-known", default="")
    parser.add_argument("--tokens-by-task-known", default="0")
    parser.add_argument("--latency-known", default="0")
    parser.add_argument("--error-retry-known", default="0")
    parser.add_argument("--human-review-known", default="0")
    parser.add_argument("--stable-high-volume", default="")
    parser.add_argument("--quality-bar-measurable", default="0")
    parser.add_argument("--sporadic-low-volume", default="0")
    parser.add_argument("--real-prompts", default="")
    parser.add_argument("--real-failure-cases", default="0")
    parser.add_argument("--measured-task-success", default="0")
    parser.add_argument("--measured-schema-adherence", default="0")
    parser.add_argument("--measured-human-intervention", default="0")
    parser.add_argument("--benchmark-only", default="0")
    parser.add_argument("--monthly-operating-cost-usd", default="")
    parser.add_argument("--successful-tasks-per-month", default="0")
    parser.add_argument("--includes-hosting-ops-review", default="0")
    parser.add_argument("--utilization-adequate", default="0")
    parser.add_argument("--cheap-first-pass", default="")
    parser.add_argument("--escalate-low-confidence", default="0")
    parser.add_argument("--all-open-forced", default="0")
    parser.add_argument("--all-proprietary-forced", default="0")
    parser.add_argument("--data-locality", default="")
    parser.add_argument("--custom-finetune", default="0")
    parser.add_argument("--offline-edge", default="0")
    parser.add_argument("--predictable-marginal-cost", default="0")
    parser.add_argument("--vendor-independence-only", default="0")
    parser.add_argument("--quality-within-tolerance", default="")
    parser.add_argument("--latency-meets-ux", default="0")
    parser.add_argument("--savings-exceed-ops-cost", default="0")
    parser.add_argument("--review-window-days", default="0")
    parser.add_argument("--api-fallback", default="0")
    parser.add_argument("--exploration-phase", default="")
    parser.add_argument("--utilization-justifies", default="0")
    parser.add_argument("--tco-justifies", default="0")
    args = parser.parse_args()

    payload: dict[str, object] = {}
    ok = True

    has_platform = bool(args.platform)
    if has_platform:
        platform = evaluate_platform(platform=args.platform)
        payload["platform"] = _decision_payload(platform)
        ok = ok and platform.ok

    workloads = _load_workloads(args.workloads)
    has_workloads = bool(args.workloads)
    addresses: list[str] = []
    if has_workloads:
        picked = pick_workload(workloads=workloads)
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
        payload["cite"] = _decision_payload(grounded)
        ok = ok and grounded.ok

    if args.monthly_api_spend_known != "":
        baseline = evaluate_baseline(
            monthly_api_spend_known=_truthy(args.monthly_api_spend_known),
            tokens_by_task_known=_truthy(args.tokens_by_task_known),
            latency_known=_truthy(args.latency_known),
            error_retry_known=_truthy(args.error_retry_known),
            human_review_known=_truthy(args.human_review_known),
        )
        payload["baseline"] = _decision_payload(baseline)
        ok = ok and baseline.ok

    if args.stable_high_volume != "":
        fit = evaluate_workload_fit(
            stable_high_volume=_truthy(args.stable_high_volume),
            quality_bar_measurable=_truthy(args.quality_bar_measurable),
            sporadic_low_volume=_truthy(args.sporadic_low_volume),
        )
        payload["workload_fit"] = _decision_payload(fit)
        ok = ok and fit.ok

    if args.real_prompts != "":
        eval_d = evaluate_apples_to_apples(
            real_prompts=_truthy(args.real_prompts),
            real_failure_cases=_truthy(args.real_failure_cases),
            measured_task_success=_truthy(args.measured_task_success),
            measured_schema_adherence=_truthy(args.measured_schema_adherence),
            measured_human_intervention=_truthy(args.measured_human_intervention),
            benchmark_only=_truthy(args.benchmark_only),
        )
        payload["eval"] = _decision_payload(eval_d)
        ok = ok and eval_d.ok

    if args.monthly_operating_cost_usd != "":
        tco = evaluate_fully_loaded_cost(
            monthly_operating_cost_usd=float(args.monthly_operating_cost_usd),
            successful_tasks_per_month=float(args.successful_tasks_per_month),
            includes_hosting_ops_review=_truthy(args.includes_hosting_ops_review),
            utilization_adequate=_truthy(args.utilization_adequate),
        )
        payload["tco"] = _decision_payload(tco)
        ok = ok and tco.ok

    if args.cheap_first_pass != "":
        routing = evaluate_routing(
            cheap_first_pass=_truthy(args.cheap_first_pass),
            escalate_low_confidence=_truthy(args.escalate_low_confidence),
            all_open_forced=_truthy(args.all_open_forced),
            all_proprietary_forced=_truthy(args.all_proprietary_forced),
        )
        payload["routing"] = _decision_payload(routing)
        ok = ok and routing.ok

    if args.data_locality != "":
        leverage = evaluate_strategic_leverage(
            data_locality=_truthy(args.data_locality),
            custom_finetune=_truthy(args.custom_finetune),
            offline_edge=_truthy(args.offline_edge),
            predictable_marginal_cost=_truthy(args.predictable_marginal_cost),
            vendor_independence_only=_truthy(args.vendor_independence_only),
        )
        payload["leverage"] = _decision_payload(leverage)
        ok = ok and leverage.ok

    if args.quality_within_tolerance != "":
        pilot = evaluate_pilot(
            quality_within_tolerance=_truthy(args.quality_within_tolerance),
            latency_meets_ux=_truthy(args.latency_meets_ux),
            savings_exceed_ops_cost=_truthy(args.savings_exceed_ops_cost),
            review_window_days=int(args.review_window_days or 0),
            api_fallback=_truthy(args.api_fallback),
        )
        payload["pilot"] = _decision_payload(pilot)
        ok = ok and pilot.ok

    if args.exploration_phase != "":
        phase = evaluate_exploration_vs_commit(
            exploration_phase=_truthy(args.exploration_phase),
            utilization_justifies=_truthy(args.utilization_justifies),
            tco_justifies=_truthy(args.tco_justifies),
        )
        payload["phase"] = _decision_payload(phase)
        ok = ok and phase.ok

    completeness = require_open_weight_cost_controls(
        has_platform=has_platform,
        has_workloads=has_workloads,
        has_cite=has_cite,
    )
    payload["completeness"] = _decision_payload(completeness)
    ok = ok and completeness.ok
    print(json.dumps(payload, indent=2))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
