"""Semrush AI Visibility Index steal: mentions vs citations. Fail closed. $0 tools only."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

PROXY_METRICS = frozenset(
    {
        "semrush_aio_score",
        "enterprise_aio_rank",
        "universal_36_chase",
        "impressions_only",
        "follower_count",
    }
)
PAID_PLATFORMS = frozenset(
    {
        "semrush_aio",
        "semrush_enterprise_aio",
        "peec_ai",
        "profound",
        "athena_aio",
        "otterly_paid",
    }
)
ALLOWED_PLATFORMS = frozenset(
    {
        "local_ai_visibility",
        "manual_prompt_pack",
        "owned_citation_page",
        "store_listing",
        "reddit_third_party",
    }
)
CITATION_CORE = frozenset(
    {
        "reddit",
        "wikipedia",
        "youtube",
        "owned_site",
        "app_store",
        "play_store",
        "stackoverflow",
    }
)
DOMAIN_METRICS = frozenset(
    {
        "brand_mention",
        "owned_citation",
        "iap_attempt",
        "wqtu",
        "store_install",
        "category_prompt_hit",
    }
)
CANONICAL_BRAND = "random tactical timer"
IAP_WEIGHT = 10
MENTION_WEIGHT = 4
CITATION_WEIGHT = 6


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
            action="allow_local_ai_visibility",
            ok=True,
            reason="use zero-cost AI visibility controls under the monthly cap",
        )
    if name in PAID_PLATFORMS or "semrush" in name:
        return ControlDecision(
            action="block_paid_aio",
            ok=False,
            reason="Semrush AIO / paid AI visibility tools stay denied under the cap",
        )
    return ControlDecision(
        action="block_paid_aio",
        ok=False,
        reason="unknown AI visibility platform is denied",
    )


def evaluate_mention_citation_split(
    *,
    tracks_mentions: bool,
    tracks_citations: bool,
    conflates_metrics: bool,
) -> ControlDecision:
    if conflates_metrics or not (tracks_mentions and tracks_citations):
        return ControlDecision(
            action="block_conflated_visibility",
            ok=False,
            reason="mentions and citations are separate metrics; track both",
        )
    return ControlDecision(
        action="allow_mention_citation_split",
        ok=True,
        reason="mentions (category fit) and citations (content depth) tracked separately",
    )


def evaluate_brand_consistency(
    *,
    canonical_name_used: bool,
    subject_first: bool,
    pronoun_only: bool,
) -> ControlDecision:
    if pronoun_only or not canonical_name_used or not subject_first:
        return ControlDecision(
            action="block_inconsistent_brand",
            ok=False,
            reason="lead with canonical brand name as subject; AI cannot bind pronouns",
        )
    return ControlDecision(
        action="allow_consistent_brand",
        ok=True,
        reason="canonical Random Tactical Timer entity appears subject-first",
    )


def evaluate_citation_core(*, surfaces: Sequence[str]) -> ControlDecision:
    normalized = {_norm(item) for item in surfaces if str(item).strip()}
    if not normalized:
        return ControlDecision(
            action="block_empty_citation_core",
            ok=False,
            reason="place brand narrative on Citation Core surfaces AI already trusts",
        )
    if normalized & CITATION_CORE:
        return ControlDecision(
            action="allow_citation_core",
            ok=True,
            reason="brand signals land on Citation Core (owned, stores, Reddit, etc.)",
        )
    return ControlDecision(
        action="block_empty_citation_core",
        ok=False,
        reason="surfaces are outside the industry Citation Core AI defaults to",
    )


def evaluate_third_party_narrative(
    *,
    third_party_named: bool,
    owned_only: bool,
) -> ControlDecision:
    if owned_only and not third_party_named:
        return ControlDecision(
            action="block_owned_only_narrative",
            ok=False,
            reason="AI narratives lean on third-party sources; do not rely on owned pages alone",
        )
    if third_party_named:
        return ControlDecision(
            action="allow_third_party_narrative",
            ok=True,
            reason="consistent brand story across third-party + owned sources",
        )
    return ControlDecision(
        action="block_owned_only_narrative",
        ok=False,
        reason="missing third-party brand-mention plan",
    )


def evaluate_structured_summary(
    *,
    has_structured_summary: bool,
    has_faq_block: bool,
) -> ControlDecision:
    if has_structured_summary and has_faq_block:
        return ControlDecision(
            action="allow_structured_citation_page",
            ok=True,
            reason="structured summary + FAQ make the page easier for LLMs to cite",
        )
    return ControlDecision(
        action="block_unstructured_page",
        ok=False,
        reason="owned citation pages need a top summary and FAQ answers",
    )


def evaluate_platform_split_tracking(
    *,
    tracks_per_platform: bool,
    single_score_only: bool,
) -> ControlDecision:
    if tracks_per_platform and not single_score_only:
        return ControlDecision(
            action="allow_platform_split",
            ok=True,
            reason="ChatGPT/Gemini/AI Mode/Overviews citation diets differ; split tracking",
        )
    return ControlDecision(
        action="block_single_score_only",
        ok=False,
        reason="do not collapse four AI platforms into one vanity score",
    )


def evaluate_universal_36_ambition(*, chasing_universal_36: bool) -> ControlDecision:
    if chasing_universal_36:
        return ControlDecision(
            action="block_universal_36_chase",
            ok=False,
            reason="Universal 36 is a ceiling for giants; target category prompts instead",
        )
    return ControlDecision(
        action="allow_category_focus",
        ok=True,
        reason="focus on combat-timer category prompts, not displacing YouTube/Amazon",
    )


def _pack_clears(raw: Mapping[str, object]) -> bool:
    return evaluate_platform(platform=str(raw.get("platform") or "")).ok


def pick_pack(*, packs: Sequence[Mapping[str, object]]) -> ControlDecision:
    for raw in packs:
        pack_id = str(raw.get("id") or "").strip()
        if pack_id and _pack_clears(raw):
            return ControlDecision(
                action="allow_local_pack",
                ok=True,
                reason="local AI visibility pack cleared",
                addresses=(f"aiv:{pack_id}",),
            )
    return ControlDecision(
        action="block_no_local_pack",
        ok=False,
        reason="no pack cleared zero-cost AI visibility gates",
    )


def evaluate_claim(*, cite: str, addresses: Sequence[str]) -> ControlDecision:
    target = (cite or "").strip()
    if target and target in set(addresses):
        return ControlDecision(
            action="allow_on_ai_visibility",
            ok=True,
            reason="cite is the local AI visibility pack address",
        )
    return ControlDecision(
        action="block_off_ai_visibility",
        ok=False,
        reason="cite is not the local AI visibility address",
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
            mentions = float(row.get("expected_mentions") or 0)
            citations = float(row.get("expected_citations") or 0)
            score = (
                iap * IAP_WEIGHT
                + mentions * MENTION_WEIGHT
                + citations * CITATION_WEIGHT
            ) / effort
        row["score"] = score
        scored.append((score, row))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [row for _, row in scored]


def require_ai_visibility_controls(
    *,
    has_platform: bool,
    has_packs: bool,
    has_cite: bool,
) -> ControlDecision:
    if has_platform and has_packs and has_cite:
        return ControlDecision(
            action="controls_complete",
            ok=True,
            reason="platform, packs, and cite evaluated",
        )
    return ControlDecision(
        action="block_incomplete_controls",
        ok=False,
        reason="fail closed: missing platform, packs, or cite",
    )


def brand_appears_subject_first(*, text: str, brand: str = CANONICAL_BRAND) -> bool:
    lowered = (text or "").strip().lower()
    target = (brand or CANONICAL_BRAND).strip().lower()
    if not lowered or not target:
        return False
    first_sentence = lowered.split(".")[0]
    return first_sentence.lstrip().startswith(target)


def _load_packs(path: str) -> list[dict[str, object]]:
    if not path:
        return []
    raw = Path(path)
    if not raw.is_file():
        return []
    payload = json.loads(raw.read_text())
    items = payload.get("packs", payload) if isinstance(payload, Mapping) else payload
    return [dict(item) for item in items if isinstance(item, Mapping)]


def _truthy(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def _split(value: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in value.split(",") if part.strip())


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Local AI visibility controls (no Semrush AIO spend)."
    )
    parser.add_argument("--platform", default="")
    parser.add_argument("--packs", default="")
    parser.add_argument("--cite", default="")
    parser.add_argument("--tracks-mentions", default="")
    parser.add_argument("--tracks-citations", default="0")
    parser.add_argument("--conflates-metrics", default="0")
    parser.add_argument("--canonical-name-used", default="")
    parser.add_argument("--subject-first", default="0")
    parser.add_argument("--pronoun-only", default="0")
    parser.add_argument("--surfaces", default="")
    parser.add_argument("--third-party-named", default="")
    parser.add_argument("--owned-only", default="0")
    parser.add_argument("--has-structured-summary", default="")
    parser.add_argument("--has-faq-block", default="0")
    parser.add_argument("--tracks-per-platform", default="")
    parser.add_argument("--single-score-only", default="0")
    parser.add_argument("--chasing-universal-36", default="0")
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

    packs = _load_packs(args.packs)
    has_packs = bool(args.packs)
    addresses: list[str] = []
    if has_packs:
        picked = pick_pack(packs=packs)
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

    if args.tracks_mentions != "":
        split = evaluate_mention_citation_split(
            tracks_mentions=_truthy(args.tracks_mentions),
            tracks_citations=_truthy(args.tracks_citations),
            conflates_metrics=_truthy(args.conflates_metrics),
        )
        payload["mention_citation"] = {
            k: v for k, v in split.__dict__.items() if k != "addresses"
        }
        ok = ok and split.ok

    if args.canonical_name_used != "":
        brand = evaluate_brand_consistency(
            canonical_name_used=_truthy(args.canonical_name_used),
            subject_first=_truthy(args.subject_first),
            pronoun_only=_truthy(args.pronoun_only),
        )
        payload["brand"] = {k: v for k, v in brand.__dict__.items() if k != "addresses"}
        ok = ok and brand.ok

    if args.surfaces:
        core = evaluate_citation_core(surfaces=_split(args.surfaces))
        payload["citation_core"] = {
            k: v for k, v in core.__dict__.items() if k != "addresses"
        }
        ok = ok and core.ok

    if args.third_party_named != "":
        third = evaluate_third_party_narrative(
            third_party_named=_truthy(args.third_party_named),
            owned_only=_truthy(args.owned_only),
        )
        payload["third_party"] = {
            k: v for k, v in third.__dict__.items() if k != "addresses"
        }
        ok = ok and third.ok

    if args.has_structured_summary != "":
        structured = evaluate_structured_summary(
            has_structured_summary=_truthy(args.has_structured_summary),
            has_faq_block=_truthy(args.has_faq_block),
        )
        payload["structured"] = {
            k: v for k, v in structured.__dict__.items() if k != "addresses"
        }
        ok = ok and structured.ok

    if args.tracks_per_platform != "":
        platforms = evaluate_platform_split_tracking(
            tracks_per_platform=_truthy(args.tracks_per_platform),
            single_score_only=_truthy(args.single_score_only),
        )
        payload["platforms"] = {
            k: v for k, v in platforms.__dict__.items() if k != "addresses"
        }
        ok = ok and platforms.ok

    if args.chasing_universal_36 != "":
        ambition = evaluate_universal_36_ambition(
            chasing_universal_36=_truthy(args.chasing_universal_36)
        )
        payload["ambition"] = {
            k: v for k, v in ambition.__dict__.items() if k != "addresses"
        }
        ok = ok and ambition.ok

    completeness = require_ai_visibility_controls(
        has_platform=has_platform,
        has_packs=has_packs,
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
