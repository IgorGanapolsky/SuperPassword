"""Intent router + scored brief for ROSE-lite autowire.

Turns raw memory cells into an agent decision: intent, ranked risks,
and one next action. Stdlib only. Never asks the CEO to run recall.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from agent_rose_lite.embeddings import MatryoshkaEmbedder, cosine_similarity

_UTC = timezone.utc
_TOKEN_RE = re.compile(r"[a-z0-9]+", re.I)
_STOP = frozenset(
    {
        "a", "an", "and", "the", "to", "it", "its", "of", "for", "on", "in",
        "is", "are", "be", "this", "that", "please", "more", "make", "with",
        "from", "into", "our", "we", "you", "your",
    }
)

_INTENT_LEXICON: dict[str, tuple[str, tuple[str, ...]]] = {
    "debug": (
        "debugging",
        (
            "crash", "fail", "failed", "error", "exception", "stack",
            "robolectric", "jdk", "red", "regress", "bug", "diagnose",
        ),
    ),
    "ship": (
        "store-publishing",
        (
            "play", "testflight", "store", "listing", "submit", "release",
            "fastlane", "production", "review",
        ),
    ),
    "monetize": (
        "automation",
        (
            "paywall", "purchase", "iap", "pro", "wqtu", "revenue",
            "convert", "funnel",
        ),
    ),
    "test": (
        "testing",
        ("test", "assert", "maestro", "espresso", "xctest", "coverage"),
    ),
    "credentials": (
        "credentials",
        ("secret", "token", "key", "auth", "credential", "2fa"),
    ),
    "automate": (
        "automation",
        ("hook", "workflow", "autowire", "ci", "agent", "automat"),
    ),
}

_TYPE_BOOST = {
    "debug": {"risk": 0.22, "pattern": 0.10, "decision": 0.04},
    "ship": {"decision": 0.16, "risk": 0.12, "preference": 0.04},
    "monetize": {"decision": 0.14, "pattern": 0.10, "risk": 0.08},
    "test": {"pattern": 0.12, "risk": 0.10},
    "credentials": {"risk": 0.24, "preference": 0.08},
    "automate": {"decision": 0.12, "pattern": 0.08},
    "general": {"risk": 0.06},
}

_NEXT_ACTION = {
    "debug": "Reproduce the failing check, then patch the gate premise with evidence.",
    "ship": "Read back store state before claiming uploaded/submitted.",
    "monetize": "Query live PostHog paywall attempt→success before changing product.",
    "test": "Write the failing test first; do not ship untested production code.",
    "credentials": "Verify env + CI secret names before reporting a blocker.",
    "automate": "Wire the path into hooks/CI; never hand the CEO a shell command.",
    "general": "Act from live evidence; mark unknown if memory is empty.",
}

_CONFIDENCE_FLOOR = 0.28


@dataclass(frozen=True)
class IntentDecision:
    intent: str
    scene: Optional[str]
    confidence: float
    query: str


def _tokens(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text or "")]


def synthesize_query(raw: str, branch_hint: str = "") -> str:
    kept = [t for t in _tokens(raw) if t not in _STOP and len(t) > 1]
    if len(kept) < 3:
        kept.extend(t for t in _tokens(branch_hint) if t not in _STOP)
    if not kept:
        return (raw or branch_hint or "random timer session").strip()[:500]
    # Preserve order, drop dupes.
    seen: set[str] = set()
    ordered: list[str] = []
    for tok in kept:
        if tok not in seen:
            seen.add(tok)
            ordered.append(tok)
    return " ".join(ordered)[:500]


def _lexicon_hit(word: str, tokens: set[str]) -> bool:
    if word in tokens:
        return True
    # Prefix match only for longer stems (avoid "play" ⊂ "paywall").
    if len(word) >= 4:
        return any(t.startswith(word) or word.startswith(t) and len(t) >= 4 for t in tokens)
    return False


def classify_intent(query: str) -> IntentDecision:
    tokens = set(_tokens(query))
    if not tokens:
        return IntentDecision("general", None, 0.15, query)
    best = "general"
    best_hits = 0
    for intent, (_scene, words) in _INTENT_LEXICON.items():
        hits = sum(1 for w in words if _lexicon_hit(w, tokens))
        if hits > best_hits:
            best_hits = hits
            best = intent
    if best_hits == 0:
        return IntentDecision("general", None, 0.22, query)
    scene = _INTENT_LEXICON[best][0]
    conf = min(0.95, 0.35 + 0.15 * best_hits)
    return IntentDecision(best, scene, round(conf, 3), query)


def _parse_ts(value: str) -> Optional[datetime]:
    try:
        return datetime.strptime(value.replace("Z", "+0000"), "%Y-%m-%dT%H:%M:%S%z")
    except (ValueError, TypeError, AttributeError):
        return None


def _recency(cell: dict, now: datetime) -> float:
    last = _parse_ts(str(cell.get("last_seen") or ""))
    if last is None:
        return 0.2
    if last.tzinfo is None:
        last = last.replace(tzinfo=_UTC)
    age_days = max(0.0, (now - last).total_seconds() / 86400)
    return math.exp(-age_days / 14.0)


def _score_cell(
    cell: dict,
    decision: IntentDecision,
    qv: list[float],
    emb: MatryoshkaEmbedder,
    now: datetime,
    embed_dim: int,
) -> dict:
    boosts = _TYPE_BOOST.get(decision.intent, _TYPE_BOOST["general"])
    content = str(cell.get("content") or "")
    cosine = cosine_similarity(qv, emb.embed(content, dim=embed_dim))
    evidence = min(1.0, 0.15 * math.log1p(float(cell.get("evidence_count") or 1)))
    scene_boost = 0.12 if decision.scene and cell.get("scene") == decision.scene else 0.0
    score = (
        0.40 * cosine
        + 0.22 * float(cell.get("salience") or 0)
        + 0.16 * _recency(cell, now)
        + evidence
        + boosts.get(str(cell.get("cell_type") or ""), 0.0)
        + scene_boost
    )
    row = dict(cell)
    row["score"] = round(score, 4)
    return row


def _diversify(scored: list[dict], limit: int) -> list[dict]:
    picked: list[dict] = []
    scene_counts: dict[str, int] = {}
    for cell in scored:
        scene = str(cell.get("scene") or "general")
        if scene_counts.get(scene, 0) >= 3:
            continue
        scene_counts[scene] = scene_counts.get(scene, 0) + 1
        picked.append(cell)
        if len(picked) >= limit:
            break
    return picked


def rank_cells(
    cells: list[dict],
    decision: IntentDecision,
    *,
    now_iso: str,
    limit: int = 5,
    embed_dim: int = 64,
) -> list[dict]:
    now = _parse_ts(now_iso) or datetime.now(tz=_UTC)
    emb = MatryoshkaEmbedder(dims=(max(embed_dim, 64), 64, 32, 16))
    qv = emb.embed(decision.query or "", dim=embed_dim)
    scored = [_score_cell(c, decision, qv, emb, now, embed_dim) for c in cells]
    scored.sort(key=lambda c: c["score"], reverse=True)
    return _diversify(scored, limit)


def render_brief(decision: IntentDecision, ranked: list[dict]) -> str:
    top = ranked[0]["score"] if ranked else 0.0
    verified = bool(ranked) and top >= _CONFIDENCE_FLOOR and decision.confidence >= 0.3
    lines = [
        f"ROSE-lite brief intent={decision.intent} scene={decision.scene or 'mixed'} "
        f"confidence={decision.confidence:.2f} query={decision.query!r}.",
        "Agents must act from this brief; never ask the CEO to run recall/ingest.",
    ]
    if not verified:
        lines.append("Memory match not verified — treat recommendations as unknown.")
        return "\n".join(lines)
    risks = [c for c in ranked if c.get("cell_type") == "risk"][:2]
    facts = [c for c in ranked if c.get("cell_type") != "risk"][:2]
    if risks:
        lines.append("Risks:")
        for cell in risks:
            lines.append(f"- ({cell['score']:.2f}) {cell.get('content', '')[:160]}")
    if facts:
        lines.append("Signals:")
        for cell in facts:
            lines.append(f"- ({cell['score']:.2f}) {cell.get('content', '')[:160]}")
    lines.append(f"Next: {_NEXT_ACTION.get(decision.intent, _NEXT_ACTION['general'])}")
    return "\n".join(lines)


def should_reuse_prior(prior: Optional[dict], query: str, threshold: float = 0.82) -> bool:
    if not prior or not isinstance(prior, dict):
        return False
    old = str(prior.get("query") or "").strip()
    if not old or not query.strip():
        return False
    old_toks = set(_tokens(old))
    new_toks = set(_tokens(query))
    if old_toks and new_toks:
        jaccard = len(old_toks & new_toks) / len(old_toks | new_toks)
        if jaccard >= 0.85:
            return True
    emb = MatryoshkaEmbedder(dims=(64, 32))
    return cosine_similarity(emb.embed(old, dim=32), emb.embed(query, dim=32)) >= threshold
