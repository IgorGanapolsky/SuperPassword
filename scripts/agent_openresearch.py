"""alphaXiv OpenResearch + HoH steal: local autoresearch loops. Fail closed. No managed compute."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

PROXY_METRICS = frozenset(
    {
        "paper_views",
        "arxiv_views",
        "digest_clicks",
        "follower_count",
        "stars",
        "tokens",
        "benchmark_only",
    }
)
MANAGED_PLATFORMS = frozenset(
    {
        "openresearch_managed_compute",
        "openresearch_cloud",
        "alphaxiv_managed",
        "orx_cloud",
        "tinker_cloud",
        "tinker_managed",
    }
)
ALLOWED_PLATFORMS = frozenset(
    {
        "local_openresearch",
        "agent_openresearch",
        "local_hoh",
        "local_autoresearch",
    }
)
ALLOWED_COMPUTE = frozenset({"local", "local_cpu", "repo_ci", "self_hosted"})
PAID_COMPUTE = frozenset(
    {"tinker_cloud", "openresearch_managed", "managed_gpu", "alphaxiv_compute"}
)
DOMAIN_METRICS = frozenset(
    {"iap_attempt", "wqtu", "timer_completed", "paywall_attempt", "domain_kpi", "posthog_domain"}
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
            action="allow_local_openresearch",
            ok=True,
            reason="run autoresearch locally under the monthly cap",
        )
    if name in MANAGED_PLATFORMS or "managed" in name or "alphaxiv" in name:
        return ControlDecision(
            action="block_managed_openresearch",
            ok=False,
            reason="managed OpenResearch / alphaXiv compute stays denied",
        )
    return ControlDecision(
        action="block_managed_openresearch",
        ok=False,
        reason="unknown OpenResearch platform is denied",
    )


def evaluate_compute(*, compute: str) -> ControlDecision:
    name = _norm(compute)
    if name in ALLOWED_COMPUTE:
        return ControlDecision(
            action="allow_local_compute",
            ok=True,
            reason="use local or self-hosted compute only",
        )
    if name in PAID_COMPUTE or "cloud" in name or "tinker" in name:
        return ControlDecision(
            action="block_paid_compute",
            ok=False,
            reason="paid cloud / Tinker compute is denied under the monthly cap",
        )
    return ControlDecision(
        action="block_paid_compute",
        ok=False,
        reason="unknown compute target is denied",
    )


def evaluate_worktree_isolation(
    *,
    isolated: bool,
    on_shared_checkout: bool,
) -> ControlDecision:
    if isolated and not on_shared_checkout:
        return ControlDecision(
            action="allow_isolated_worktree",
            ok=True,
            reason="each experiment direction gets an isolated worktree",
        )
    return ControlDecision(
        action="block_shared_checkout",
        ok=False,
        reason="do not run experiment arms on the shared user checkout",
    )


def evaluate_eval_artifact(*, has_eval_md: bool, metric: str) -> ControlDecision:
    name = _norm(metric)
    if not has_eval_md:
        return ControlDecision(
            action="block_missing_eval",
            ok=False,
            reason="EVAL.md (or equivalent evidence artifact) is required",
        )
    if name in PROXY_METRICS:
        return ControlDecision(
            action="block_proxy_eval",
            ok=False,
            reason="paper views and vanity proxies are not domain KPIs",
        )
    if name in DOMAIN_METRICS:
        return ControlDecision(
            action="allow_eval_artifact",
            ok=True,
            reason="eval artifact cites a domain KPI",
        )
    return ControlDecision(
        action="block_proxy_eval",
        ok=False,
        reason="unknown eval metric is treated as proxy and denied",
    )


def evaluate_autoresearch_loop(
    *,
    hypothesized: bool,
    changed_code: bool,
    ran_experiment: bool,
    inspected_evidence: bool,
    decided_next: bool,
) -> ControlDecision:
    if (
        hypothesized
        and changed_code
        and ran_experiment
        and inspected_evidence
        and decided_next
    ):
        return ControlDecision(
            action="allow_autoresearch_loop",
            ok=True,
            reason="hypothesis → change → run → evidence → next decision completed",
        )
    return ControlDecision(
        action="block_incomplete_autoresearch",
        ok=False,
        reason="autoresearch loop incomplete without evidence-backed next step",
    )


def evaluate_hoh_loop(
    *,
    planned: bool,
    coded: bool,
    tested: bool,
    independent_eval: bool,
    reused_skills: bool,
    repair_only: bool,
) -> ControlDecision:
    if not (planned and coded and tested):
        return ControlDecision(
            action="block_incomplete_hoh",
            ok=False,
            reason="HoH requires plan → code → test in each increment",
        )
    if not independent_eval:
        return ControlDecision(
            action="block_impl_eval_only",
            ok=False,
            reason="separate independent evaluation from implementation-time tests",
        )
    if repair_only and not reused_skills:
        return ControlDecision(
            action="block_repair_only",
            ok=False,
            reason="balance repair with capability growth and skill reuse",
        )
    return ControlDecision(
        action="allow_hoh_loop",
        ok=True,
        reason="verifiable HoH increment with independent eval",
    )


def evaluate_declarative_attention(
    *,
    declared_scope: bool,
    unbounded_context: bool,
) -> ControlDecision:
    if declared_scope and not unbounded_context:
        return ControlDecision(
            action="allow_declarative_attention",
            ok=True,
            reason="agent declares attention scope before expanding context",
        )
    return ControlDecision(
        action="block_unbounded_attention",
        ok=False,
        reason="unbounded context dump without declared scope is denied",
    )


def _experiment_clears(raw: Mapping[str, object]) -> bool:
    return evaluate_platform(platform=str(raw.get("platform") or "")).ok


def pick_experiment(
    *,
    experiments: Sequence[Mapping[str, object]],
) -> ControlDecision:
    for raw in experiments:
        experiment_id = str(raw.get("id") or "").strip()
        if experiment_id and _experiment_clears(raw):
            return ControlDecision(
                action="allow_local_experiment",
                ok=True,
                reason="local OpenResearch experiment cleared",
                addresses=(f"orx:{experiment_id}",),
            )
    return ControlDecision(
        action="block_no_local_experiment",
        ok=False,
        reason="no experiment cleared local OpenResearch gates",
    )


def evaluate_claim(*, cite: str, addresses: Sequence[str]) -> ControlDecision:
    target = (cite or "").strip()
    if target and target in set(addresses):
        return ControlDecision(
            action="allow_on_openresearch",
            ok=True,
            reason="cite is the local OpenResearch experiment address",
        )
    return ControlDecision(
        action="block_off_openresearch",
        ok=False,
        reason="cite is not the local OpenResearch address",
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


def require_openresearch_controls(
    *,
    has_platform: bool,
    has_experiments: bool,
    has_cite: bool,
) -> ControlDecision:
    if has_platform and has_experiments and has_cite:
        return ControlDecision(
            action="controls_complete",
            ok=True,
            reason="platform, experiments, and cite evaluated",
        )
    return ControlDecision(
        action="block_incomplete_controls",
        ok=False,
        reason="fail closed: missing platform, experiments, or cite",
    )


def _load_experiments(path: str) -> list[dict[str, object]]:
    if not path:
        return []
    raw = Path(path)
    if not raw.is_file():
        return []
    payload = json.loads(raw.read_text())
    items = (
        payload.get("experiments", payload) if isinstance(payload, Mapping) else payload
    )
    return [dict(item) for item in items if isinstance(item, Mapping)]


def _truthy(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Local OpenResearch + HoH controls (no managed compute)."
    )
    parser.add_argument("--platform", default="")
    parser.add_argument("--experiments", default="")
    parser.add_argument("--cite", default="")
    parser.add_argument("--compute", default="")
    parser.add_argument("--isolated", default="")
    parser.add_argument("--on-shared-checkout", default="0")
    parser.add_argument("--has-eval-md", default="")
    parser.add_argument("--metric", default="")
    parser.add_argument("--hypothesized", default="")
    parser.add_argument("--changed-code", default="0")
    parser.add_argument("--ran-experiment", default="0")
    parser.add_argument("--inspected-evidence", default="0")
    parser.add_argument("--decided-next", default="0")
    parser.add_argument("--planned", default="")
    parser.add_argument("--coded", default="0")
    parser.add_argument("--tested", default="0")
    parser.add_argument("--independent-eval", default="0")
    parser.add_argument("--reused-skills", default="0")
    parser.add_argument("--repair-only", default="0")
    parser.add_argument("--declared-scope", default="")
    parser.add_argument("--unbounded-context", default="0")
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

    experiments = _load_experiments(args.experiments)
    has_experiments = bool(args.experiments)
    addresses: list[str] = []
    if has_experiments:
        picked = pick_experiment(experiments=experiments)
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

    if args.compute:
        compute = evaluate_compute(compute=args.compute)
        payload["compute"] = {
            k: v for k, v in compute.__dict__.items() if k != "addresses"
        }
        ok = ok and compute.ok

    if args.isolated != "":
        isolation = evaluate_worktree_isolation(
            isolated=_truthy(args.isolated),
            on_shared_checkout=_truthy(args.on_shared_checkout),
        )
        payload["worktree"] = {
            k: v for k, v in isolation.__dict__.items() if k != "addresses"
        }
        ok = ok and isolation.ok

    if args.has_eval_md != "" or args.metric:
        evaluation = evaluate_eval_artifact(
            has_eval_md=_truthy(args.has_eval_md) if args.has_eval_md != "" else True,
            metric=args.metric or "iap_attempt",
        )
        payload["eval"] = {
            k: v for k, v in evaluation.__dict__.items() if k != "addresses"
        }
        ok = ok and evaluation.ok

    if args.hypothesized != "":
        loop = evaluate_autoresearch_loop(
            hypothesized=_truthy(args.hypothesized),
            changed_code=_truthy(args.changed_code),
            ran_experiment=_truthy(args.ran_experiment),
            inspected_evidence=_truthy(args.inspected_evidence),
            decided_next=_truthy(args.decided_next),
        )
        payload["autoresearch"] = {
            k: v for k, v in loop.__dict__.items() if k != "addresses"
        }
        ok = ok and loop.ok

    if args.planned != "":
        hoh = evaluate_hoh_loop(
            planned=_truthy(args.planned),
            coded=_truthy(args.coded),
            tested=_truthy(args.tested),
            independent_eval=_truthy(args.independent_eval),
            reused_skills=_truthy(args.reused_skills),
            repair_only=_truthy(args.repair_only),
        )
        payload["hoh"] = {k: v for k, v in hoh.__dict__.items() if k != "addresses"}
        ok = ok and hoh.ok

    if args.declared_scope != "":
        attention = evaluate_declarative_attention(
            declared_scope=_truthy(args.declared_scope),
            unbounded_context=_truthy(args.unbounded_context),
        )
        payload["attention"] = {
            k: v for k, v in attention.__dict__.items() if k != "addresses"
        }
        ok = ok and attention.ok

    completeness = require_openresearch_controls(
        has_platform=has_platform,
        has_experiments=has_experiments,
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
