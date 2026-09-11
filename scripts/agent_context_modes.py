"""LangChain multi-agent context-mode steal: isolated vs fork subagents. Fail closed."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

PROXY_METRICS = frozenset(
    {
        "subagent_count",
        "langsmith_spans",
        "press_mentions",
        "blog_claps",
        "context_window_tokens_vanity",
    }
)
DENIED_PLATFORMS = frozenset(
    {
        "langsmith_paid_seat",
        "langchain_cloud_spend",
        "deepagents_hosted_over_cap",
        "always_fork_everything",
        "always_isolate_everything",
    }
)
ALLOWED_PLATFORMS = frozenset(
    {
        "local_context_modes",
        "agent_context_modes",
        "supervisor_subagent_harness",
        "fork_or_isolated_gate",
        "ops_context_routing",
    }
)
DOMAIN_METRICS = frozenset(
    {
        "iap_attempt",
        "wqtu",
        "timer_completed",
        "paywall_attempt",
        "store_version_verify",
        "context_reuse",
        "review_independence",
        "handoff_routed",
    }
)
WORKER_ROLES = frozenset({"worker", "fixer", "implementer", "continuator"})
VERIFIER_ROLES = frozenset({"verifier", "reviewer", "critic"})
RESEARCHER_ROLES = frozenset({"researcher", "investigator", "scout"})
MEMORY_ROLES = frozenset({"memory", "memorizer", "retainer"})
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
            action="allow_local_context_modes",
            ok=True,
            reason="run isolated/fork context-mode gates locally under the monthly cap",
        )
    if name in DENIED_PLATFORMS or "langsmith" in name or "langchain_cloud" in name:
        return ControlDecision(
            action="block_vendor_spend",
            ok=False,
            reason="LangSmith / hosted Deep Agents seats stay denied under the monthly cap",
        )
    return ControlDecision(
        action="block_vendor_spend",
        ok=False,
        reason="unknown context-mode platform is denied",
    )


def evaluate_context_mode(*, role: str, mode: str) -> ControlDecision:
    role_n = _norm(role)
    mode_n = _norm(mode)
    if mode_n not in {"isolated", "fork"}:
        return ControlDecision(
            action="block_unknown_mode",
            ok=False,
            reason='context mode must be "isolated" or "fork"',
        )
    if role_n in WORKER_ROLES:
        if mode_n == "fork":
            return ControlDecision(
                action="allow_worker_fork",
                ok=True,
                reason="workers continue diagnosed work — fork reuses supervisor context",
            )
        return ControlDecision(
            action="block_worker_isolated",
            ok=False,
            reason="isolating a worker forces rediscovery of evidence the supervisor already gathered",
        )
    if role_n in VERIFIER_ROLES:
        if mode_n == "isolated":
            return ControlDecision(
                action="allow_verifier_isolated",
                ok=True,
                reason="verifiers need independent judgment — isolate to avoid supervisor anchoring",
            )
        return ControlDecision(
            action="block_verifier_fork",
            ok=False,
            reason="forking a verifier anchors it to the supervisor’s diagnosis",
        )
    if role_n in RESEARCHER_ROLES:
        if mode_n == "isolated":
            return ControlDecision(
                action="allow_researcher_isolated",
                ok=True,
                reason="self-contained research questions stay isolated (especially in parallel)",
            )
        return ControlDecision(
            action="block_researcher_fork",
            ok=False,
            reason="forking parallel researchers duplicates supervisor history without need",
        )
    if role_n in MEMORY_ROLES:
        if mode_n == "fork":
            return ControlDecision(
                action="allow_memory_fork",
                ok=True,
                reason="memory agents need the conversation itself — fork the thread",
            )
        return ControlDecision(
            action="block_memory_isolated",
            ok=False,
            reason="isolated memory agents cannot see the conversation to retain",
        )
    return ControlDecision(
        action="block_unknown_role",
        ok=False,
        reason="unknown subagent role — classify as worker/verifier/researcher/memory",
    )


def evaluate_waste(
    *,
    supervisor_already_gathered_context: bool,
    mode: str,
    role: str,
) -> ControlDecision:
    mode_n = _norm(mode)
    role_n = _norm(role)
    if (
        supervisor_already_gathered_context
        and mode_n == "isolated"
        and role_n in WORKER_ROLES
    ):
        return ControlDecision(
            action="block_context_waste",
            ok=False,
            reason="isolated worker would redo file reads / context gathering already done",
        )
    return ControlDecision(
        action="allow_no_waste",
        ok=True,
        reason="context mode does not force redundant rediscovery for this role",
    )


def evaluate_return_shape(
    *,
    supervisor_receives_final_only: bool,
    intermediate_reasoning_leaked: bool,
) -> ControlDecision:
    if supervisor_receives_final_only and not intermediate_reasoning_leaked:
        return ControlDecision(
            action="allow_outcome_only",
            ok=True,
            reason="supervisor receives the subagent outcome without intermediate pollution",
        )
    return ControlDecision(
        action="block_context_pollution",
        ok=False,
        reason="do not dump subagent intermediate reasoning into the supervisor window",
    )


def evaluate_parallel_research(*, parallel_count: int, mode: str) -> ControlDecision:
    mode_n = _norm(mode)
    if int(parallel_count) > 1 and mode_n == "fork":
        return ControlDecision(
            action="block_parallel_fork_duplication",
            ok=False,
            reason="parallel forked researchers duplicate supervisor history — use isolated",
        )
    if int(parallel_count) >= 1 and mode_n == "isolated":
        return ControlDecision(
            action="allow_parallel_isolated",
            ok=True,
            reason="parallel researchers stay isolated on self-contained questions",
        )
    return ControlDecision(
        action="block_parallel_fork_duplication",
        ok=False,
        reason="parallel research requires isolated context mode",
    )


def evaluate_permissions(
    *,
    write_paths_restricted: bool,
    role: str,
) -> ControlDecision:
    role_n = _norm(role)
    if role_n in MEMORY_ROLES and not write_paths_restricted:
        return ControlDecision(
            action="block_unrestricted_memory_writes",
            ok=False,
            reason="memory agents need restricted write paths (specialize permissions)",
        )
    if write_paths_restricted or role_n not in MEMORY_ROLES:
        return ControlDecision(
            action="allow_specialized_permissions",
            ok=True,
            reason="subagent permissions match role specialization",
        )
    return ControlDecision(
        action="block_unrestricted_memory_writes",
        ok=False,
        reason="specialize permissions for the subagent role",
    )


def evaluate_monoculture(*, force_all_fork: bool, force_all_isolated: bool) -> ControlDecision:
    if force_all_fork or force_all_isolated:
        return ControlDecision(
            action="block_mode_monoculture",
            ok=False,
            reason="do not force all-fork or all-isolated — match mode to role relationship",
        )
    return ControlDecision(
        action="allow_mode_by_role",
        ok=True,
        reason="context mode chosen per subagent relationship to the work",
    )


def _harness_clears(raw: Mapping[str, object]) -> bool:
    return evaluate_platform(platform=str(raw.get("platform") or "")).ok


def pick_harness(*, harnesses: Sequence[Mapping[str, object]]) -> ControlDecision:
    for raw in harnesses:
        hid = str(raw.get("id") or "").strip()
        if hid and _harness_clears(raw):
            return ControlDecision(
                action="allow_local_harness",
                ok=True,
                reason="local context-mode harness cleared",
                addresses=(f"acm:{hid}",),
            )
    return ControlDecision(
        action="block_no_local_harness",
        ok=False,
        reason="no harness cleared local context-mode gates",
    )


def evaluate_claim(*, cite: str, addresses: Sequence[str]) -> ControlDecision:
    target = (cite or "").strip()
    if target and target in set(addresses):
        return ControlDecision(
            action="allow_on_context_modes",
            ok=True,
            reason="cite is the local context-mode harness address",
        )
    return ControlDecision(
        action="block_off_context_modes",
        ok=False,
        reason="cite is not the local context-mode address",
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


def require_context_mode_controls(
    *,
    has_platform: bool,
    has_harnesses: bool,
    has_cite: bool,
) -> ControlDecision:
    if has_platform and has_harnesses and has_cite:
        return ControlDecision(
            action="controls_complete",
            ok=True,
            reason="platform, harnesses, and cite evaluated",
        )
    return ControlDecision(
        action="block_incomplete_controls",
        ok=False,
        reason="fail closed: missing platform, harnesses, or cite",
    )


def _load_harnesses(path: str) -> list[dict[str, object]]:
    if not path:
        return []
    raw = Path(path)
    if not raw.is_file():
        return []
    payload = json.loads(raw.read_text())
    items = payload.get("harnesses", payload) if isinstance(payload, Mapping) else payload
    return [dict(item) for item in items if isinstance(item, Mapping)]


def _truthy(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def _payload(d: ControlDecision) -> dict[str, object]:
    return {"action": d.action, "ok": d.ok, "reason": d.reason}


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Local isolated/fork context-mode controls (no LangSmith seats)."
    )
    parser.add_argument("--platform", default="")
    parser.add_argument("--harnesses", default="")
    parser.add_argument("--cite", default="")
    parser.add_argument("--role", default="")
    parser.add_argument("--mode", default="")
    parser.add_argument("--supervisor-already-gathered-context", default="")
    parser.add_argument("--supervisor-receives-final-only", default="")
    parser.add_argument("--intermediate-reasoning-leaked", default="0")
    parser.add_argument("--parallel-count", default="")
    parser.add_argument("--write-paths-restricted", default="")
    parser.add_argument("--force-all-fork", default="0")
    parser.add_argument("--force-all-isolated", default="0")
    args = parser.parse_args()

    payload: dict[str, object] = {}
    ok = True

    has_platform = bool(args.platform)
    if has_platform:
        platform = evaluate_platform(platform=args.platform)
        payload["platform"] = _payload(platform)
        ok = ok and platform.ok

    harnesses = _load_harnesses(args.harnesses)
    has_harnesses = bool(args.harnesses)
    addresses: list[str] = []
    if has_harnesses:
        picked = pick_harness(harnesses=harnesses)
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
        payload["cite"] = _payload(grounded)
        ok = ok and grounded.ok

    if args.role != "" and args.mode != "":
        pairing = evaluate_context_mode(role=args.role, mode=args.mode)
        payload["pairing"] = _payload(pairing)
        ok = ok and pairing.ok

        if args.supervisor_already_gathered_context != "":
            waste = evaluate_waste(
                supervisor_already_gathered_context=_truthy(
                    args.supervisor_already_gathered_context
                ),
                mode=args.mode,
                role=args.role,
            )
            payload["waste"] = _payload(waste)
            ok = ok and waste.ok

        if args.write_paths_restricted != "":
            perms = evaluate_permissions(
                write_paths_restricted=_truthy(args.write_paths_restricted),
                role=args.role,
            )
            payload["permissions"] = _payload(perms)
            ok = ok and perms.ok

    if args.supervisor_receives_final_only != "":
        ret = evaluate_return_shape(
            supervisor_receives_final_only=_truthy(args.supervisor_receives_final_only),
            intermediate_reasoning_leaked=_truthy(args.intermediate_reasoning_leaked),
        )
        payload["return_shape"] = _payload(ret)
        ok = ok and ret.ok

    if args.parallel_count != "":
        parallel = evaluate_parallel_research(
            parallel_count=int(args.parallel_count),
            mode=args.mode or "isolated",
        )
        payload["parallel"] = _payload(parallel)
        ok = ok and parallel.ok

    monoculture = evaluate_monoculture(
        force_all_fork=_truthy(args.force_all_fork),
        force_all_isolated=_truthy(args.force_all_isolated),
    )
    payload["monoculture"] = _payload(monoculture)
    ok = ok and monoculture.ok

    completeness = require_context_mode_controls(
        has_platform=has_platform,
        has_harnesses=has_harnesses,
        has_cite=has_cite,
    )
    payload["completeness"] = _payload(completeness)
    ok = ok and completeness.ok
    print(json.dumps(payload, indent=2))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
