"""Spotify shunt steal: intercept large reads. Fail closed. No Portal."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

DEFAULT_MIN_LINES = 350
REASONING_KINDS = frozenset({"reasoning", "debug", "architecture", "safety"})
DELEGABLE_KINDS = frozenset({"boilerplate", "config", "test_scaffold", "large_read"})
METERED_WORKERS = frozenset(
    {"gemini-2.5-flash", "gemini_2_5_flash", "gemini_flash", "portal", "aika"}
)
PROXY_METRICS = frozenset({"tokens", "pr_velocity", "daily_messages"})
IAP_WEIGHT = 10
TASK_WEIGHT = 5


@dataclass(frozen=True)
class ControlDecision:
    action: str
    ok: bool
    reason: str


def _norm(value: str) -> str:
    return (value or "").strip().lower().replace("-", "_").replace(".", "_")


def evaluate_read_intercept(
    *,
    line_count: int,
    targeted: bool,
    threshold: int = DEFAULT_MIN_LINES,
) -> ControlDecision:
    if int(line_count) > int(threshold) and not targeted:
        return ControlDecision(
            action="block_full_read",
            ok=False,
            reason="untargeted large reads burn frontier tokens; slice or target first",
        )
    return ControlDecision(
        action="allow_read",
        ok=True,
        reason="small file or targeted offset/limit",
    )


def evaluate_task_route(*, task_kind: str, model: str) -> ControlDecision:
    kind = _norm(task_kind)
    worker = _norm(model)
    if kind in REASONING_KINDS:
        if worker in METERED_WORKERS or "flash" in worker or "local_slice" in worker:
            return ControlDecision(
                action="block_delegate_reason",
                ok=False,
                reason="do not delegate debugging or architecture to a cheap worker",
            )
        if "hermes" in worker and "main" in worker:
            return ControlDecision(
                action="allow_frontier",
                ok=True,
                reason="reasoning stays on the capable route",
            )
        return ControlDecision(
            action="block_delegate_reason",
            ok=False,
            reason="reasoning needs hermes-main",
        )
    if kind in DELEGABLE_KINDS:
        if worker in METERED_WORKERS:
            return ControlDecision(
                action="block_metered",
                ok=False,
                reason="Portal and Gemini Flash are outside the monthly cap",
            )
        if worker == "local_slice":
            return ControlDecision(
                action="allow_delegate",
                ok=True,
                reason="boilerplate and large reads use a local slice, not a frontier dump",
            )
    return ControlDecision(
        action="block_metered",
        ok=False,
        reason="unknown task or worker is denied",
    )


def evaluate_context_return(*, source_lines: int, returned_lines: int) -> ControlDecision:
    if int(source_lines) > DEFAULT_MIN_LINES and int(returned_lines) >= int(source_lines):
        return ControlDecision(
            action="block_full_dump",
            ok=False,
            reason="return only the relevant slice to the frontier model",
        )
    return ControlDecision(
        action="allow_slice",
        ok=True,
        reason="frontier context is a slice, not the whole file",
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


def require_shunt_controls(
    *,
    has_read: bool,
    has_route: bool,
    has_return: bool,
) -> ControlDecision:
    if has_read and has_route and has_return:
        return ControlDecision(
            action="controls_complete",
            ok=True,
            reason="read intercept, route, and slice evaluated",
        )
    return ControlDecision(
        action="block_incomplete_controls",
        ok=False,
        reason="fail closed: missing read intercept, route, or slice",
    )


def main() -> int:
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Spotify-inspired token shunt (no Portal).")
    parser.add_argument("--lines", default="")
    parser.add_argument("--targeted", action="store_true")
    parser.add_argument("--threshold", default=str(DEFAULT_MIN_LINES))
    parser.add_argument("--task-kind", default="")
    parser.add_argument("--model", default="")
    parser.add_argument("--source-lines", default="")
    parser.add_argument("--returned-lines", default="")
    args = parser.parse_args()

    payload: dict[str, object] = {}
    ok = True

    has_read = args.lines != ""
    if has_read:
        read = evaluate_read_intercept(
            line_count=int(args.lines or 0),
            targeted=bool(args.targeted),
            threshold=int(args.threshold or DEFAULT_MIN_LINES),
        )
        payload["read"] = read.__dict__
        ok = ok and read.ok

    has_route = bool(args.task_kind or args.model)
    if has_route:
        route = evaluate_task_route(task_kind=args.task_kind, model=args.model)
        payload["route"] = route.__dict__
        ok = ok and route.ok

    has_return = args.source_lines != "" or args.returned_lines != ""
    if has_return:
        returned = evaluate_context_return(
            source_lines=int(args.source_lines or 0),
            returned_lines=int(args.returned_lines or 0),
        )
        payload["return"] = returned.__dict__
        ok = ok and returned.ok

    completeness = require_shunt_controls(
        has_read=has_read,
        has_route=has_route,
        has_return=has_return,
    )
    payload["completeness"] = completeness.__dict__
    ok = ok and completeness.ok

    print(json.dumps(payload, indent=2))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
