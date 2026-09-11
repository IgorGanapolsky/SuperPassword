"""OpenAI Codex / MIT EQuS lab steal: calibration loops for ops. Fail closed."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

PROXY_METRICS = frozenset(
    {
        "qubit_count",
        "fridge_hours",
        "openai_ultra_tokens",
        "lab_novelty_score",
        "press_mentions",
    }
)
DENIED_PLATFORMS = frozenset(
    {
        "quantum_hardware_spend",
        "dilution_fridge_rental",
        "openai_ultra_paid_lab",
        "codex_cloud_gpu_lab",
        "equus_hardware",
    }
)
ALLOWED_PLATFORMS = frozenset(
    {
        "local_codex_lab",
        "agent_codex_lab",
        "ops_calibration_loop",
        "routine_measurement_skill",
    }
)
DOMAIN_METRICS = frozenset(
    {
        "iap_attempt",
        "wqtu",
        "timer_completed",
        "paywall_attempt",
        "store_version_verify",
        "calibration_pass",
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
            action="allow_local_codex_lab",
            ok=True,
            reason="run ops calibration loops locally under the monthly cap",
        )
    if name in DENIED_PLATFORMS or "quantum" in name or "fridge" in name:
        return ControlDecision(
            action="block_quantum_spend",
            ok=False,
            reason="quantum hardware / paid lab compute stays denied",
        )
    return ControlDecision(
        action="block_quantum_spend",
        ok=False,
        reason="unknown Codex-lab platform is denied",
    )


def evaluate_measurement_skill(
    *,
    has_skill: bool,
    has_prerequisites: bool,
    has_success_fail_criteria: bool,
    has_template: bool,
) -> ControlDecision:
    if has_skill and has_prerequisites and has_success_fail_criteria and has_template:
        return ControlDecision(
            action="allow_measurement_skill",
            ok=True,
            reason="measurement skill includes template, prerequisites, and success/fail criteria",
        )
    return ControlDecision(
        action="block_incomplete_skill",
        ok=False,
        reason="each routine measurement needs a skill with template, prereqs, and pass/fail evidence",
    )


def evaluate_interdependent_chain(
    *,
    prerequisites_complete: bool,
    result_persisted: bool,
    skipped_step: bool,
) -> ControlDecision:
    if skipped_step or not prerequisites_complete or not result_persisted:
        return ControlDecision(
            action="block_broken_calibration_chain",
            ok=False,
            reason="interdependent calibrations require completed prereqs and persisted results",
        )
    return ControlDecision(
        action="allow_calibration_chain",
        ok=True,
        reason="each measurement result feeds the next step with persisted settings",
    )


def evaluate_signal_quality(
    *,
    signal_clear: bool,
    signal_noisy: bool,
    human_escalated: bool,
) -> ControlDecision:
    if signal_clear and not signal_noisy:
        return ControlDecision(
            action="allow_autonomous_measurement",
            ok=True,
            reason="clear signals allow autonomous routine measurement",
        )
    if signal_noisy and human_escalated:
        return ControlDecision(
            action="allow_escalated_noisy_run",
            ok=True,
            reason="noisy/ambiguous signals require researcher steer before continuing",
        )
    if signal_noisy and not human_escalated:
        return ControlDecision(
            action="block_noisy_without_escalation",
            ok=False,
            reason="do not keep guessing on noisy signals without human guidance",
        )
    return ControlDecision(
        action="block_noisy_without_escalation",
        ok=False,
        reason="signal quality unknown — fail closed",
    )


def evaluate_routine_vs_novel(
    *,
    routine_workflow: bool,
    novel_experiment: bool,
    narrow_goal: bool,
) -> ControlDecision:
    if routine_workflow and not novel_experiment:
        return ControlDecision(
            action="allow_routine_autonomy",
            ok=True,
            reason="well-defined routine characterization may run with little intervention",
        )
    if novel_experiment and narrow_goal:
        return ControlDecision(
            action="allow_novel_narrow_goal",
            ok=True,
            reason="novel work needs narrower goals plus code write/test against real evidence",
        )
    if novel_experiment and not narrow_goal:
        return ControlDecision(
            action="block_unbounded_novel",
            ok=False,
            reason="do not grant broad autonomy on novel experiments",
        )
    return ControlDecision(
        action="block_unbounded_novel",
        ok=False,
        reason="classify work as routine or novel before granting autonomy",
    )


def evaluate_unattended_run(
    *,
    progress_log: bool,
    check_in_possible: bool,
    steer_hook: bool,
) -> ControlDecision:
    if progress_log and check_in_possible and steer_hook:
        return ControlDecision(
            action="allow_unattended_run",
            ok=True,
            reason="overnight/unattended runs need progress logs and a steer hook",
        )
    return ControlDecision(
        action="block_blind_unattended",
        ok=False,
        reason="unattended runs without check-in/steer are denied",
    )


def evaluate_human_focus(
    *,
    agent_owns_routine: bool,
    human_owns_design_analysis: bool,
) -> ControlDecision:
    if agent_owns_routine and human_owns_design_analysis:
        return ControlDecision(
            action="allow_researcher_pairing",
            ok=True,
            reason="agents own routine measurements; humans own design, interpretation, next steps",
        )
    return ControlDecision(
        action="block_role_inversion",
        ok=False,
        reason="do not invert roles — humans must not babysit every routine step",
    )


def _loop_clears(raw: Mapping[str, object]) -> bool:
    return evaluate_platform(platform=str(raw.get("platform") or "")).ok


def pick_loop(*, loops: Sequence[Mapping[str, object]]) -> ControlDecision:
    for raw in loops:
        loop_id = str(raw.get("id") or "").strip()
        if loop_id and _loop_clears(raw):
            return ControlDecision(
                action="allow_local_loop",
                ok=True,
                reason="local Codex-lab calibration loop cleared",
                addresses=(f"cxl:{loop_id}",),
            )
    return ControlDecision(
        action="block_no_local_loop",
        ok=False,
        reason="no loop cleared local Codex-lab gates",
    )


def evaluate_claim(*, cite: str, addresses: Sequence[str]) -> ControlDecision:
    target = (cite or "").strip()
    if target and target in set(addresses):
        return ControlDecision(
            action="allow_on_codex_lab",
            ok=True,
            reason="cite is the local Codex-lab loop address",
        )
    return ControlDecision(
        action="block_off_codex_lab",
        ok=False,
        reason="cite is not the local Codex-lab address",
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


def require_codex_lab_controls(
    *,
    has_platform: bool,
    has_loops: bool,
    has_cite: bool,
) -> ControlDecision:
    if has_platform and has_loops and has_cite:
        return ControlDecision(
            action="controls_complete",
            ok=True,
            reason="platform, loops, and cite evaluated",
        )
    return ControlDecision(
        action="block_incomplete_controls",
        ok=False,
        reason="fail closed: missing platform, loops, or cite",
    )


def _load_loops(path: str) -> list[dict[str, object]]:
    if not path:
        return []
    raw = Path(path)
    if not raw.is_file():
        return []
    payload = json.loads(raw.read_text())
    items = payload.get("loops", payload) if isinstance(payload, Mapping) else payload
    return [dict(item) for item in items if isinstance(item, Mapping)]


def _truthy(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Local Codex-lab ops calibration controls (no quantum spend)."
    )
    parser.add_argument("--platform", default="")
    parser.add_argument("--loops", default="")
    parser.add_argument("--cite", default="")
    parser.add_argument("--has-skill", default="")
    parser.add_argument("--has-prerequisites", default="0")
    parser.add_argument("--has-success-fail-criteria", default="0")
    parser.add_argument("--has-template", default="0")
    parser.add_argument("--prerequisites-complete", default="")
    parser.add_argument("--result-persisted", default="0")
    parser.add_argument("--skipped-step", default="0")
    parser.add_argument("--signal-clear", default="")
    parser.add_argument("--signal-noisy", default="0")
    parser.add_argument("--human-escalated", default="0")
    parser.add_argument("--routine-workflow", default="")
    parser.add_argument("--novel-experiment", default="0")
    parser.add_argument("--narrow-goal", default="0")
    parser.add_argument("--progress-log", default="")
    parser.add_argument("--check-in-possible", default="0")
    parser.add_argument("--steer-hook", default="0")
    parser.add_argument("--agent-owns-routine", default="")
    parser.add_argument("--human-owns-design-analysis", default="0")
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

    loops = _load_loops(args.loops)
    has_loops = bool(args.loops)
    addresses: list[str] = []
    if has_loops:
        picked = pick_loop(loops=loops)
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

    if args.has_skill != "":
        skill = evaluate_measurement_skill(
            has_skill=_truthy(args.has_skill),
            has_prerequisites=_truthy(args.has_prerequisites),
            has_success_fail_criteria=_truthy(args.has_success_fail_criteria),
            has_template=_truthy(args.has_template),
        )
        payload["skill"] = {k: v for k, v in skill.__dict__.items() if k != "addresses"}
        ok = ok and skill.ok

    if args.prerequisites_complete != "":
        chain = evaluate_interdependent_chain(
            prerequisites_complete=_truthy(args.prerequisites_complete),
            result_persisted=_truthy(args.result_persisted),
            skipped_step=_truthy(args.skipped_step),
        )
        payload["chain"] = {k: v for k, v in chain.__dict__.items() if k != "addresses"}
        ok = ok and chain.ok

    if args.signal_clear != "":
        signal = evaluate_signal_quality(
            signal_clear=_truthy(args.signal_clear),
            signal_noisy=_truthy(args.signal_noisy),
            human_escalated=_truthy(args.human_escalated),
        )
        payload["signal"] = {
            k: v for k, v in signal.__dict__.items() if k != "addresses"
        }
        ok = ok and signal.ok

    if args.routine_workflow != "":
        mode = evaluate_routine_vs_novel(
            routine_workflow=_truthy(args.routine_workflow),
            novel_experiment=_truthy(args.novel_experiment),
            narrow_goal=_truthy(args.narrow_goal),
        )
        payload["mode"] = {k: v for k, v in mode.__dict__.items() if k != "addresses"}
        ok = ok and mode.ok

    if args.progress_log != "":
        unattended = evaluate_unattended_run(
            progress_log=_truthy(args.progress_log),
            check_in_possible=_truthy(args.check_in_possible),
            steer_hook=_truthy(args.steer_hook),
        )
        payload["unattended"] = {
            k: v for k, v in unattended.__dict__.items() if k != "addresses"
        }
        ok = ok and unattended.ok

    if args.agent_owns_routine != "":
        pairing = evaluate_human_focus(
            agent_owns_routine=_truthy(args.agent_owns_routine),
            human_owns_design_analysis=_truthy(args.human_owns_design_analysis),
        )
        payload["pairing"] = {
            k: v for k, v in pairing.__dict__.items() if k != "addresses"
        }
        ok = ok and pairing.ok

    completeness = require_codex_lab_controls(
        has_platform=has_platform,
        has_loops=has_loops,
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
