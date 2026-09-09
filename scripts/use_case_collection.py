"""Dataiku steal: owned catalog + 3-question skip. Fail closed. No Dataiku."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

PROXY_METRICS = frozenset({"tokens", "pr_velocity", "daily_messages", "agent_count"})
GATED_SOURCES = frozenset(
    {
        "dataiku",
        "content_dataiku_com",
        "contentdataikucom",
        "agent_connect",
        "llm_mesh",
        "pdf_gated",
        "gated_pdf",
    }
)
OWNED_FAMILIES = frozenset({"iap_attempt", "wqtu", "timer_completed", "paywall_attempt"})
COLLECTION_FAMILIES = frozenset(
    {
        "expertise",
        "knowledge_heavy",
        "security",
        "predictive_maintenance",
        "clinical_trial",
        "support_ticket",
        "invoicing",
        "personalized_sales",
        "maintenance_scheduling",
    }
)
SKIP_COMPLEXITY = frozenset({"simple_if_then", "basic_automation", "traditional_software"})
SKIP_DATA = frozenset({"single_clean", "single_source"})
SKIP_PROCESS = frozenset({"static", "same_every_time"})
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


def evaluate_source(*, source: str) -> ControlDecision:
    name = _norm(source)
    if name in {"local_catalog", "use_case_collection", "owned_catalog"}:
        return ControlDecision(
            action="allow_local_catalog",
            ok=True,
            reason="use the owned catalog, not the gated PDF",
        )
    if name in GATED_SOURCES or "dataiku" in name or "mesh" in name:
        return ControlDecision(
            action="block_gated_pdf",
            ok=False,
            reason="Dataiku collection PDF and LLM Mesh stay outside the cap",
        )
    return ControlDecision(
        action="block_gated_pdf",
        ok=False,
        reason="unknown collection source is denied",
    )


def evaluate_family(*, family: str) -> ControlDecision:
    name = _norm(family)
    if name in OWNED_FAMILIES:
        return ControlDecision(
            action="allow_owned_family",
            ok=True,
            reason="family is a live Random Timer problem",
        )
    if name in COLLECTION_FAMILIES:
        return ControlDecision(
            action="block_collection_family",
            ok=False,
            reason="do not copy Dataiku collection verticals",
        )
    return ControlDecision(
        action="block_collection_family",
        ok=False,
        reason="unknown family is denied",
    )


def evaluate_agent_need(*, complexity: str, data: str, process: str) -> ControlDecision:
    if (
        _norm(complexity) in SKIP_COMPLEXITY
        or _norm(data) in SKIP_DATA
        or _norm(process) in SKIP_PROCESS
    ):
        return ControlDecision(
            action="skip_agent",
            ok=True,
            reason="simple if-then work is product code, not an agent",
        )
    return ControlDecision(
        action="block_agent_theater",
        ok=False,
        reason="do not stand up a collection-style agent for this product",
    )


def pick_owned(*, cases: Sequence[Mapping[str, object]], family: str) -> ControlDecision:
    wanted = _norm(family)
    owned: list[str] = []
    for raw in cases:
        case_id = str(raw.get("id") or "").strip()
        if not case_id:
            continue
        if raw.get("owned") is not True:
            continue
        if _norm(str(raw.get("family") or "")) != wanted:
            continue
        if wanted not in OWNED_FAMILIES:
            continue
        owned.append(f"case:{case_id}")
    if owned:
        return ControlDecision(
            action="allow_owned_case",
            ok=True,
            reason="cite an owned catalog case, not a collection demo",
            addresses=(owned[0],),
        )
    return ControlDecision(
        action="block_off_catalog",
        ok=False,
        reason="no owned case matches the family",
    )


def evaluate_claim(*, cite: str, addresses: Sequence[str]) -> ControlDecision:
    target = (cite or "").strip()
    if target and target in set(addresses):
        return ControlDecision(
            action="allow_on_catalog",
            ok=True,
            reason="cite is the owned catalog case",
        )
    return ControlDecision(
        action="block_off_catalog",
        ok=False,
        reason="cite is not an owned catalog case",
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


def require_collection_controls(
    *,
    has_source: bool,
    has_family: bool,
    has_need: bool,
    has_cases: bool,
    has_cite: bool,
) -> ControlDecision:
    if has_source and has_family and has_need and has_cases and has_cite:
        return ControlDecision(
            action="controls_complete",
            ok=True,
            reason="source, family, 3-question test, cases, and cite evaluated",
        )
    return ControlDecision(
        action="block_incomplete_controls",
        ok=False,
        reason="fail closed: missing source, family, 3-question test, cases, or cite",
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

    parser = argparse.ArgumentParser(description="Owned use-case catalog (no Dataiku).")
    parser.add_argument("--source", default="")
    parser.add_argument("--family", default="")
    parser.add_argument("--complexity", default="")
    parser.add_argument("--data", default="")
    parser.add_argument("--process", default="")
    parser.add_argument("--cases", default="")
    parser.add_argument("--cite", default="")
    args = parser.parse_args()

    payload: dict[str, object] = {}
    ok = True

    has_source = bool(args.source)
    if has_source:
        source = evaluate_source(source=args.source)
        payload["source"] = {k: v for k, v in source.__dict__.items() if k != "addresses"}
        ok = ok and source.ok

    has_family = bool(args.family)
    if has_family:
        family = evaluate_family(family=args.family)
        payload["family"] = {k: v for k, v in family.__dict__.items() if k != "addresses"}
        ok = ok and family.ok

    has_need = bool(args.complexity or args.data or args.process)
    if has_need:
        need = evaluate_agent_need(
            complexity=args.complexity,
            data=args.data,
            process=args.process,
        )
        payload["need"] = {k: v for k, v in need.__dict__.items() if k != "addresses"}
        ok = ok and need.ok

    cases = _load_cases(args.cases)
    has_cases = bool(args.cases)
    addresses: list[str] = []
    if has_cases:
        picked = pick_owned(cases=cases, family=args.family)
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

    completeness = require_collection_controls(
        has_source=has_source,
        has_family=has_family,
        has_need=has_need,
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
