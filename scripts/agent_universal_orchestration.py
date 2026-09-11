"""Decisions Universal Orchestration steal: control layer for multi-agent ops. Fail closed."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

PROXY_METRICS = frozenset(
    {
        "agent_count",
        "workflow_count",
        "ebook_downloads",
        "demo_requests",
        "g2_badge_score",
        "press_mentions",
    }
)
DENIED_PLATFORMS = frozenset(
    {
        "decisions_saas_paid",
        "decisions_enterprise_license",
        "bpm_platform_spend",
        "orchestration_vendor_demo_funnel",
        "low_code_enterprise_seat",
    }
)
ALLOWED_PLATFORMS = frozenset(
    {
        "local_universal_orchestration",
        "agent_universal_orchestration",
        "ops_control_layer",
        "rules_first_gate",
        "governed_agent_handoff",
    }
)
DOMAIN_METRICS = frozenset(
    {
        "iap_attempt",
        "wqtu",
        "timer_completed",
        "paywall_attempt",
        "store_version_verify",
        "audit_trail_complete",
        "handoff_routed",
        "exception_resolved",
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
    if name in ALLOWED_PLATFORMS:
        return ControlDecision(
            action="allow_local_orchestration",
            ok=True,
            reason="run universal orchestration controls locally under the monthly cap",
        )
    if name in DENIED_PLATFORMS or "decisions" in name and "paid" in name:
        return ControlDecision(
            action="block_vendor_spend",
            ok=False,
            reason="Decisions SaaS / enterprise BPM seats stay denied under the monthly cap",
        )
    if name in DENIED_PLATFORMS or "bpm_platform" in name or "enterprise_seat" in name:
        return ControlDecision(
            action="block_vendor_spend",
            ok=False,
            reason="paid orchestration vendor spend is denied",
        )
    return ControlDecision(
        action="block_vendor_spend",
        ok=False,
        reason="unknown orchestration platform is denied",
    )


def evaluate_control_layer(
    *,
    has_control_layer: bool,
    agent_sprawl: bool,
) -> ControlDecision:
    if has_control_layer and not agent_sprawl:
        return ControlDecision(
            action="allow_control_layer",
            ok=True,
            reason="agents and automation sit under one governed control layer",
        )
    return ControlDecision(
        action="block_agent_sprawl",
        ok=False,
        reason="uncoordinated agent sprawl without a control layer is denied",
    )


def evaluate_rules_first(
    *,
    deterministic_policy: bool,
    prompt_only: bool,
) -> ControlDecision:
    if deterministic_policy and not prompt_only:
        return ControlDecision(
            action="allow_rules_first",
            ok=True,
            reason="final decisions lock to deterministic policy, not prompt-only outcomes",
        )
    return ControlDecision(
        action="block_prompt_only",
        ok=False,
        reason="prompt-only agent decisions without policy rules are not defensible",
    )


def evaluate_guardrails(
    *,
    authorized_actions_defined: bool,
    unauthorized_blocked: bool,
) -> ControlDecision:
    if authorized_actions_defined and unauthorized_blocked:
        return ControlDecision(
            action="allow_guardrails",
            ok=True,
            reason="each agent has explicit allow/deny boundaries that prompts cannot override",
        )
    return ControlDecision(
        action="block_unguarded_agent",
        ok=False,
        reason="agents without explicit authorized-action guardrails are denied",
    )


def evaluate_human_in_loop(
    *,
    irreversible_action: bool,
    approval_point: bool,
    escalated: bool,
) -> ControlDecision:
    if not irreversible_action:
        return ControlDecision(
            action="allow_reversible_autonomy",
            ok=True,
            reason="reversible work may proceed without human approval",
        )
    if irreversible_action and (approval_point or escalated):
        return ControlDecision(
            action="allow_hitl_gate",
            ok=True,
            reason="irreversible actions require approval/escalation before execute",
        )
    return ControlDecision(
        action="block_late_oversight",
        ok=False,
        reason="human oversight must gate irreversible actions before they complete",
    )


def evaluate_audit_trail(
    *,
    rules_logged: bool,
    inputs_logged: bool,
    outputs_logged: bool,
    handoffs_logged: bool,
) -> ControlDecision:
    if rules_logged and inputs_logged and outputs_logged and handoffs_logged:
        return ControlDecision(
            action="allow_audit_ready",
            ok=True,
            reason="audit trail covers rules, inputs, outputs, and handoffs",
        )
    return ControlDecision(
        action="block_audit_gaps",
        ok=False,
        reason="incomplete audit trails (rules/inputs/outputs/handoffs) are denied",
    )


def evaluate_handoff(
    *,
    next_step_routed: bool,
    result_persisted: bool,
) -> ControlDecision:
    if next_step_routed and result_persisted:
        return ControlDecision(
            action="allow_governed_handoff",
            ok=True,
            reason="results route to the next governed step with persisted context",
        )
    return ControlDecision(
        action="block_handoff_black_hole",
        ok=False,
        reason="agent completion without routed next step is a handoff black hole",
    )


def evaluate_readiness(
    *,
    complexity_signals: bool,
    readiness_assessed: bool,
    focused_first_use_case: bool,
) -> ControlDecision:
    if complexity_signals and readiness_assessed and focused_first_use_case:
        return ControlDecision(
            action="allow_focused_start",
            ok=True,
            reason="start with one high-value use case after readiness assessment",
        )
    if not focused_first_use_case:
        return ControlDecision(
            action="block_boil_ocean",
            ok=False,
            reason="do not transform everything at once — pick a focused first use case",
        )
    return ControlDecision(
        action="block_unready_scale",
        ok=False,
        reason="assess complexity signals and readiness before scaling orchestration",
    )


def evaluate_shadow_test(
    *,
    shadow_tested: bool,
    going_live: bool,
) -> ControlDecision:
    if going_live and not shadow_tested:
        return ControlDecision(
            action="block_untested_live",
            ok=False,
            reason="shadow-test agent behavior against rules before going live",
        )
    if shadow_tested or not going_live:
        return ControlDecision(
            action="allow_shadow_or_draft",
            ok=True,
            reason="shadow-tested or still draft — safe under rules-first gate",
        )
    return ControlDecision(
        action="block_untested_live",
        ok=False,
        reason="live orchestration without shadow test is denied",
    )


def evaluate_visibility(
    *,
    real_time_observability: bool,
    exceptions_surfaced: bool,
) -> ControlDecision:
    if real_time_observability and exceptions_surfaced:
        return ControlDecision(
            action="allow_visible_orchestration",
            ok=True,
            reason="processes are observable with exceptions surfaced for action",
        )
    return ControlDecision(
        action="block_blind_orchestration",
        ok=False,
        reason="orchestration without observability/exception surfacing is denied",
    )


def _flow_clears(raw: Mapping[str, object]) -> bool:
    return evaluate_platform(platform=str(raw.get("platform") or "")).ok


def pick_flow(*, flows: Sequence[Mapping[str, object]]) -> ControlDecision:
    for raw in flows:
        fid = str(raw.get("id") or "").strip()
        if fid and _flow_clears(raw):
            return ControlDecision(
                action="allow_local_flow",
                ok=True,
                reason="local universal-orchestration flow cleared",
                addresses=(f"uor:{fid}",),
            )
    return ControlDecision(
        action="block_no_local_flow",
        ok=False,
        reason="no flow cleared local universal-orchestration gates",
    )


def evaluate_claim(*, cite: str, addresses: Sequence[str]) -> ControlDecision:
    target = (cite or "").strip()
    if target and target in set(addresses):
        return ControlDecision(
            action="allow_on_universal_orchestration",
            ok=True,
            reason="cite is the local universal-orchestration flow address",
        )
    return ControlDecision(
        action="block_off_universal_orchestration",
        ok=False,
        reason="cite is not the local universal-orchestration address",
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


def require_universal_orchestration_controls(
    *,
    has_platform: bool,
    has_flows: bool,
    has_cite: bool,
) -> ControlDecision:
    if has_platform and has_flows and has_cite:
        return ControlDecision(
            action="controls_complete",
            ok=True,
            reason="platform, flows, and cite evaluated",
        )
    return ControlDecision(
        action="block_incomplete_controls",
        ok=False,
        reason="fail closed: missing platform, flows, or cite",
    )


def _load_flows(path: str) -> list[dict[str, object]]:
    if not path:
        return []
    raw = Path(path)
    if not raw.is_file():
        return []
    payload = json.loads(raw.read_text())
    items = payload.get("flows", payload) if isinstance(payload, Mapping) else payload
    return [dict(item) for item in items if isinstance(item, Mapping)]


def _truthy(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Local universal orchestration controls (no vendor SaaS spend)."
    )
    parser.add_argument("--platform", default="")
    parser.add_argument("--flows", default="")
    parser.add_argument("--cite", default="")
    parser.add_argument("--has-control-layer", default="")
    parser.add_argument("--agent-sprawl", default="0")
    parser.add_argument("--deterministic-policy", default="")
    parser.add_argument("--prompt-only", default="0")
    parser.add_argument("--authorized-actions-defined", default="")
    parser.add_argument("--unauthorized-blocked", default="0")
    parser.add_argument("--irreversible-action", default="")
    parser.add_argument("--approval-point", default="0")
    parser.add_argument("--escalated", default="0")
    parser.add_argument("--rules-logged", default="")
    parser.add_argument("--inputs-logged", default="0")
    parser.add_argument("--outputs-logged", default="0")
    parser.add_argument("--handoffs-logged", default="0")
    parser.add_argument("--next-step-routed", default="")
    parser.add_argument("--result-persisted", default="0")
    parser.add_argument("--complexity-signals", default="")
    parser.add_argument("--readiness-assessed", default="0")
    parser.add_argument("--focused-first-use-case", default="0")
    parser.add_argument("--shadow-tested", default="")
    parser.add_argument("--going-live", default="0")
    parser.add_argument("--real-time-observability", default="")
    parser.add_argument("--exceptions-surfaced", default="0")
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

    flows = _load_flows(args.flows)
    has_flows = bool(args.flows)
    addresses: list[str] = []
    if has_flows:
        picked = pick_flow(flows=flows)
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

    if args.has_control_layer != "":
        layer = evaluate_control_layer(
            has_control_layer=_truthy(args.has_control_layer),
            agent_sprawl=_truthy(args.agent_sprawl),
        )
        payload["control_layer"] = {
            k: v for k, v in layer.__dict__.items() if k != "addresses"
        }
        ok = ok and layer.ok

    if args.deterministic_policy != "":
        rules = evaluate_rules_first(
            deterministic_policy=_truthy(args.deterministic_policy),
            prompt_only=_truthy(args.prompt_only),
        )
        payload["rules_first"] = {
            k: v for k, v in rules.__dict__.items() if k != "addresses"
        }
        ok = ok and rules.ok

    if args.authorized_actions_defined != "":
        guard = evaluate_guardrails(
            authorized_actions_defined=_truthy(args.authorized_actions_defined),
            unauthorized_blocked=_truthy(args.unauthorized_blocked),
        )
        payload["guardrails"] = {
            k: v for k, v in guard.__dict__.items() if k != "addresses"
        }
        ok = ok and guard.ok

    if args.irreversible_action != "":
        hitl = evaluate_human_in_loop(
            irreversible_action=_truthy(args.irreversible_action),
            approval_point=_truthy(args.approval_point),
            escalated=_truthy(args.escalated),
        )
        payload["hitl"] = {k: v for k, v in hitl.__dict__.items() if k != "addresses"}
        ok = ok and hitl.ok

    if args.rules_logged != "":
        audit = evaluate_audit_trail(
            rules_logged=_truthy(args.rules_logged),
            inputs_logged=_truthy(args.inputs_logged),
            outputs_logged=_truthy(args.outputs_logged),
            handoffs_logged=_truthy(args.handoffs_logged),
        )
        payload["audit"] = {k: v for k, v in audit.__dict__.items() if k != "addresses"}
        ok = ok and audit.ok

    if args.next_step_routed != "":
        handoff = evaluate_handoff(
            next_step_routed=_truthy(args.next_step_routed),
            result_persisted=_truthy(args.result_persisted),
        )
        payload["handoff"] = {
            k: v for k, v in handoff.__dict__.items() if k != "addresses"
        }
        ok = ok and handoff.ok

    if args.complexity_signals != "":
        ready = evaluate_readiness(
            complexity_signals=_truthy(args.complexity_signals),
            readiness_assessed=_truthy(args.readiness_assessed),
            focused_first_use_case=_truthy(args.focused_first_use_case),
        )
        payload["readiness"] = {
            k: v for k, v in ready.__dict__.items() if k != "addresses"
        }
        ok = ok and ready.ok

    if args.shadow_tested != "":
        shadow = evaluate_shadow_test(
            shadow_tested=_truthy(args.shadow_tested),
            going_live=_truthy(args.going_live),
        )
        payload["shadow"] = {
            k: v for k, v in shadow.__dict__.items() if k != "addresses"
        }
        ok = ok and shadow.ok

    if args.real_time_observability != "":
        vis = evaluate_visibility(
            real_time_observability=_truthy(args.real_time_observability),
            exceptions_surfaced=_truthy(args.exceptions_surfaced),
        )
        payload["visibility"] = {
            k: v for k, v in vis.__dict__.items() if k != "addresses"
        }
        ok = ok and vis.ok

    completeness = require_universal_orchestration_controls(
        has_platform=has_platform,
        has_flows=has_flows,
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
