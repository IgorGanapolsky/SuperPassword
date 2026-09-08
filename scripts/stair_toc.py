"""IBM STAIR steal: TOC-addressed retrieval. Fail closed. No fine-tune."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Mapping, Sequence

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.M)
PAREN_RE = re.compile(r"\([^)]*\)")
NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")
TOKEN_RE = re.compile(r"[a-z0-9]+", re.I)
PROXY_METRICS = frozenset({"tokens", "pr_velocity", "daily_messages"})
IAP_WEIGHT = 10
TASK_WEIGHT = 5


@dataclass(frozen=True)
class ControlDecision:
    action: str
    ok: bool
    reason: str


def _norm(value: str) -> str:
    return (value or "").strip().lower().replace("-", "_")


def _slug(title: str) -> str:
    stripped = PAREN_RE.sub("", title or "")
    return NON_ALNUM_RE.sub("-", stripped.lower()).strip("-")


def _tokens(text: str) -> set[str]:
    return set(TOKEN_RE.findall((text or "").lower()))


def extract_toc(*, markdown: str, source: str) -> list[dict[str, object]]:
    path = (source or "").strip()
    rows: list[dict[str, object]] = []
    for match in HEADING_RE.finditer(markdown or ""):
        title = match.group(2).strip()
        slug = _slug(title)
        if not path or not slug:
            continue
        rows.append(
            {
                "level": len(match.group(1)),
                "title": title,
                "slug": slug,
                "address": f"{path}#{slug}",
            }
        )
    return rows


def evaluate_chunking(*, mode: str) -> ControlDecision:
    if _norm(mode) == "toc":
        return ControlDecision(
            action="allow_toc",
            ok=True,
            reason="address space is the document table of contents",
        )
    return ControlDecision(
        action="block_length_chunk",
        ok=False,
        reason="length chunks discard the hierarchy the corpus already has",
    )


def retrieve_by_toc(*, query: str, toc: Sequence[Mapping[str, object]]) -> ControlDecision:
    if not toc:
        return ControlDecision(
            action="block_no_structure",
            ok=False,
            reason="no table of contents to address",
        )
    q = _tokens(query)
    if not q:
        return ControlDecision(
            action="block_no_structure",
            ok=False,
            reason="empty query cannot address a heading",
        )
    scored: list[tuple[int, str]] = []
    for row in toc:
        title = str(row.get("title") or "")
        address = str(row.get("address") or "")
        overlap = len(q & _tokens(title))
        if overlap:
            scored.append((overlap, address))
    if not scored:
        return ControlDecision(
            action="block_no_structure",
            ok=False,
            reason="query matched no heading in the table of contents",
        )
    scored.sort(key=lambda item: item[0], reverse=True)
    return ControlDecision(
        action="allow_retrieve",
        ok=True,
        reason=scored[0][1],
    )


def evaluate_grounding(*, cited: str, toc: Sequence[Mapping[str, object]]) -> ControlDecision:
    addresses = {str(row.get("address") or "") for row in toc}
    if (cited or "").strip() in addresses:
        return ControlDecision(
            action="allow_grounded",
            ok=True,
            reason="cited address exists in the corpus table of contents",
        )
    return ControlDecision(
        action="block_hallucinated_address",
        ok=False,
        reason="generative retrieval must cite a real ToC address",
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


def require_stair_controls(
    *,
    has_toc: bool,
    has_chunking: bool,
    has_retrieve: bool,
    has_grounding: bool,
) -> ControlDecision:
    if has_toc and has_chunking and has_retrieve and has_grounding:
        return ControlDecision(
            action="controls_complete",
            ok=True,
            reason="ToC, chunking, retrieve, and grounding evaluated",
        )
    return ControlDecision(
        action="block_incomplete_controls",
        ok=False,
        reason="fail closed: missing ToC, chunking, retrieve, or grounding",
    )


def main() -> int:
    import argparse
    import json
    from pathlib import Path

    parser = argparse.ArgumentParser(description="STAIR-inspired ToC retriever (no SaaS).")
    parser.add_argument("--source", default="")
    parser.add_argument("--markdown-file", default="")
    parser.add_argument("--mode", default="")
    parser.add_argument("--query", default="")
    parser.add_argument("--cite", default="")
    args = parser.parse_args()

    payload: dict[str, object] = {}
    ok = True
    toc: list[dict[str, object]] = []

    has_toc = bool(args.source or args.markdown_file)
    if has_toc:
        text = ""
        if args.markdown_file:
            text = Path(args.markdown_file).read_text()
        toc = extract_toc(markdown=text, source=args.source or args.markdown_file)
        payload["toc_count"] = len(toc)
        if not toc:
            ok = False

    has_chunking = bool(args.mode)
    if has_chunking:
        chunking = evaluate_chunking(mode=args.mode)
        payload["chunking"] = chunking.__dict__
        ok = ok and chunking.ok

    has_retrieve = bool(args.query)
    if has_retrieve:
        retrieved = retrieve_by_toc(query=args.query, toc=toc)
        payload["retrieve"] = retrieved.__dict__
        ok = ok and retrieved.ok

    has_grounding = bool(args.cite)
    if has_grounding:
        grounding = evaluate_grounding(cited=args.cite, toc=toc)
        payload["grounding"] = grounding.__dict__
        ok = ok and grounding.ok

    completeness = require_stair_controls(
        has_toc=has_toc,
        has_chunking=has_chunking,
        has_retrieve=has_retrieve,
        has_grounding=has_grounding,
    )
    payload["completeness"] = completeness.__dict__
    ok = ok and completeness.ok

    print(json.dumps(payload, indent=2))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
