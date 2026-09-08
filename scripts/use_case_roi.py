"""Dataiku steal: score use cases, pick one. Fail closed. No Dataiku."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

PROXY_METRICS = frozenset({"tokens", "pr_velocity", "daily_messages", "agent_count"})
METERED_PLATFORMS = frozenset(
    {"dataiku", "llm_mesh", "agent_hub", "dataiku_govern", "agent_management"}
)
BUSINESS_PROBLEMS = frozenset({"iap_attempt", "wqtu", "timer_completed", "paywall_attempt"})
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
    if name in {"local_score", "use_case_roi", "scorecard"}:
        return ControlDecision(
            action="allow_local_score",
            ok=True,
            reason="score ROI, complexity, and readiness on a local card",
        )
    if name in METERED_PLATFORMS or "dataiku" in name or "mesh" in name:
        return ControlDecision(
            action="block_metered",
            ok=False,
            reason="Dataiku and LLM Mesh are outside the monthly cap",
        )
    return ControlDecision(
        action="block_metered",
        ok=False,
        reason="unknown use-case platform is denied",
    )


def evaluate_problem(*, problem: str) -> ControlDecision:
    name = _norm(problem)
    if name in BUSINESS_PROBLEMS:
        return ControlDecision(
            action="allow_business_problem",
            ok=True,
            reason="start from a live business problem, not a demo",
        )
    return ControlDecision(
        action="block_tech_first",
        ok=False,
        reason="do not pick a use case to showcase an agent platform",
    )


def _clamp(value: object) -> float:
    try:
        return max(1.0, min(3.0, float(value)))
    except (TypeError, ValueError):
        return 1.0


def score_use_case(*, case: Mapping[str, object]) -> ControlDecision:
    case_id = str(case.get("id") or "").strip()
    roi = _clamp(case.get("roi"))
    complexity = _clamp(case.get("complexity"))
    readiness = _clamp(case.get("readiness"))
    if case_id and roi >= 2 and complexity <= 2 and readiness >= 2:
        return ControlDecision(
            action="allow_sweet_spot",
            ok=True,
            reason="high value, easier implementation, users ready",
            addresses=(f"case:{case_id}",),
        )
    return ControlDecision(
        action="block_low_roi",
        ok=False,
        reason="low value or hard first-wave work stays parked",
    )


def pick_one(*, cases: Sequence[Mapping[str, object]]) -> ControlDecision:
    scored: list[tuple[float, str]] = []
    for raw in cases:
        decision = score_use_case(case=raw)
        if not decision.ok:
            continue
        case_id = str(raw.get("id") or "").strip()
        roi = _clamp(raw.get("roi"))
        complexity = _clamp(raw.get("complexity"))
        readiness = _clamp(raw.get("readiness"))
        score = (roi * readiness) / complexity
        scored.append((score, f"case:{case_id}"))
    scored.sort(key=lambda item: item[0], reverse=True)
    if scored:
        return ControlDecision(
            action="allow_pick_one",
            ok=True,
            reason="ship one sweet-spot use case, then scale",
            addresses=(scored[0][1],),
        )
    return ControlDecision(
        action="block_no_pick",
        ok=False,
        reason="no use case cleared the sweet-spot score",
    )


def evaluate_claim(*, cite: str, addresses: Sequence[str]) -> ControlDecision:
    target = (cite or "").strip()
    if target and target in set(addresses):
        return ControlDecision(
            action="allow_on_score",
            ok=True,
            reason="cite is the picked use case",
        )
    return ControlDecision(
        action="block_off_score",
        ok=False,
        reason="cite is not the scored pick",
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


def require_use_case_controls(
    *,
    has_platform: bool,
    has_problem: bool,
    has_cases: bool,
    has_cite: bool,
) -> ControlDecision:
    if has_platform and has_problem and has_cases and has_cite:
        return ControlDecision(
            action="controls_complete",
            ok=True,
            reason="platform, problem, cases, and cite evaluated",
        )
    return ControlDecision(
        action="block_incomplete_controls",
        ok=False,
        reason="fail closed: missing platform, problem, cases, or cite",
    )


def _load_cases(path: str) -> list[dict[str, object]]:
    if not path:
        return []
    raw = Path(path)
    if not raw.is_file():
        return []
    payload = json.loads(raw.read_text())
    items = payload.get("cases", payload) if isinstance(payload, Mapping) else payload
    return [dict(item) for item in items if isinstance(item, Mapping)]


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Local use-case ROI score (no Dataiku).")
    parser.add_argument("--platform", default="")
    parser.add_argument("--problem", default="")
    parser.add_argument("--cases", default="")
    parser.add_argument("--cite", default="")
    args = parser.parse_args()

    payload: dict[str, object] = {}
    ok = True

    has_platform = bool(args.platform)
    if has_platform:
        platform = evaluate_platform(platform=args.platform)
        payload["platform"] = {k: v for k, v in platform.__dict__.items() if k != "addresses"}
        ok = ok and platform.ok

    has_problem = bool(args.problem)
    if has_problem:
        problem = evaluate_problem(problem=args.problem)
        payload["problem"] = {k: v for k, v in problem.__dict__.items() if k != "addresses"}
        ok = ok and problem.ok

    cases = _load_cases(args.cases)
    has_cases = bool(args.cases)
    addresses: list[str] = []
    if has_cases:
        picked = pick_one(cases=cases)
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

    completeness = require_use_case_controls(
        has_platform=has_platform,
        has_problem=has_problem,
        has_cases=has_cases,
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
