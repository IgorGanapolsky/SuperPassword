"""Databricks steal: local eval + governance before production. Fail closed."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

PROXY_METRICS = frozenset(
    {
        "multi_agent_count",
        "agent_count",
        "chatbot_count",
        "tokens",
        "database_branches",
        "generic_benchmark",
    }
)
DATABRICKS_PLATFORMS = frozenset(
    {
        "databricks",
        "databricks_cloud",
        "unity_catalog",
        "ai_gateway",
        "agent_bricks",
        "lakebase",
        "neon_databricks",
        "mosaic_ai",
    }
)
ALLOWED_PLATFORMS = frozenset(
    {
        "local_eval_governance",
        "agent_eval_governance",
        "local_production_gate",
    }
)
ALLOWED_EVALS = frozenset(
    {"domain_kpi", "wqtu", "iap_attempt", "posthog_domain", "business_kpi"}
)
BLOCKED_EVALS = frozenset(
    {"generic_benchmark", "leaderboard", "mmlu", "arena", "vibes"}
)
ALLOWED_GOV = frozenset(
    {
        "local_fail_closed",
        "repo_guards",
        "thumbgate_local",
        "ci_gates",
        "cite_required",
    }
)
PAID_GOV = frozenset(
    {"ai_gateway", "unity_catalog", "databricks_governance", "lakehouse_acl"}
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
            action="allow_local_eval_gov",
            ok=True,
            reason="run eval + governance locally under the monthly cap",
        )
    if (
        name in DATABRICKS_PLATFORMS
        or "databricks" in name
        or "unity_catalog" in name
        or "lakebase" in name
    ):
        return ControlDecision(
            action="block_databricks_cloud",
            ok=False,
            reason="Databricks AI Gateway / Agent Bricks / Lakebase stay denied under the $20 cap",
        )
    return ControlDecision(
        action="block_databricks_cloud",
        ok=False,
        reason="unknown eval-governance platform is denied",
    )


def evaluate_evaluation(*, evaluation: str) -> ControlDecision:
    name = _norm(evaluation)
    if name in ALLOWED_EVALS:
        return ControlDecision(
            action="allow_domain_eval",
            ok=True,
            reason="domain KPIs (WQTU / IAP) beat generic benchmarks",
        )
    if name in BLOCKED_EVALS or "benchmark" in name or "leaderboard" in name:
        return ControlDecision(
            action="block_generic_benchmark",
            ok=False,
            reason="generic benchmarks are not production evidence for this product",
        )
    return ControlDecision(
        action="block_generic_benchmark",
        ok=False,
        reason="unknown evaluation type is denied",
    )


def evaluate_governance(*, governance: str) -> ControlDecision:
    name = _norm(governance)
    if name in ALLOWED_GOV:
        return ControlDecision(
            action="allow_local_governance",
            ok=True,
            reason="local fail-closed guards are deployment infrastructure",
        )
    if name in PAID_GOV or "databricks" in name or "gateway" in name:
        return ControlDecision(
            action="block_paid_governance",
            ok=False,
            reason="Databricks AI Gateway / Unity Catalog stay denied",
        )
    return ControlDecision(
        action="block_paid_governance",
        ok=False,
        reason="unknown governance surface is denied",
    )


def evaluate_stage(
    *,
    stage: str,
    evaluation_ok: bool,
    governance_ok: bool,
) -> ControlDecision:
    name = _norm(stage)
    if name in {"production", "prod"} and evaluation_ok and governance_ok:
        return ControlDecision(
            action="allow_production",
            ok=True,
            reason="eval + governance cleared; production path allowed",
        )
    if name in {"production", "prod"}:
        return ControlDecision(
            action="block_production_without_controls",
            ok=False,
            reason="production requires both domain eval and local governance",
        )
    if name in {"pilot", "experiment", "demo"} and not (evaluation_ok and governance_ok):
        return ControlDecision(
            action="block_pilot_without_controls",
            ok=False,
            reason="pilots without eval + governance stall before production",
        )
    if evaluation_ok and governance_ok:
        return ControlDecision(
            action="allow_controlled_stage",
            ok=True,
            reason="controls present for this stage",
        )
    return ControlDecision(
        action="block_pilot_without_controls",
        ok=False,
        reason="stage denied without eval + governance",
    )


def _path_clears(path: Mapping[str, object]) -> bool:
    evaluation = evaluate_evaluation(evaluation=str(path.get("evaluation") or ""))
    governance = evaluate_governance(governance=str(path.get("governance") or ""))
    stage = evaluate_stage(
        stage=str(path.get("stage") or ""),
        evaluation_ok=evaluation.ok,
        governance_ok=governance.ok,
    )
    return evaluation.ok and governance.ok and stage.ok


def pick_path(*, paths: Sequence[Mapping[str, object]]) -> ControlDecision:
    for raw in paths:
        path_id = str(raw.get("id") or "").strip()
        if path_id and _path_clears(raw):
            return ControlDecision(
                action="allow_local_path",
                ok=True,
                reason="keep domain-eval + local-governance production paths",
                addresses=(f"path:{path_id}",),
            )
    return ControlDecision(
        action="block_no_local_path",
        ok=False,
        reason="no path cleared local eval + governance controls",
    )


def evaluate_claim(*, cite: str, addresses: Sequence[str]) -> ControlDecision:
    target = (cite or "").strip()
    if target and target in set(addresses):
        return ControlDecision(
            action="allow_on_path",
            ok=True,
            reason="cite is the local production path",
        )
    return ControlDecision(
        action="block_off_path",
        ok=False,
        reason="cite is not the local production path",
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


def require_eval_gov_controls(
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
        description="Local eval + governance production gate (no Databricks cloud)."
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
        payload["platform"] = {
            k: v for k, v in platform.__dict__.items() if k != "addresses"
        }
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
        payload["cite"] = {
            k: v for k, v in grounded.__dict__.items() if k != "addresses"
        }
        ok = ok and grounded.ok

    completeness = require_eval_gov_controls(
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
