# Agent AI Visibility (Semrush Index-inspired, $0)

Adapted from the [Semrush AI Visibility Index 2026 Study](https://ai-visibility-index.semrush.com/reports/ai-visibility-index-2026-study-h1) (126M prompts). Steal the **measurement model and content tactics**, not Semrush Enterprise AIO ($99+/mo).

| Source construct | Random-Timer control / asset |
| --- | --- |
| Mentions ≠ citations | `evaluate_mention_citation_split` |
| Citation Core (Reddit, owned, stores) | `evaluate_citation_core` + `marketing/site/ai-visibility/` |
| Consistent third-party narrative | Reddit drafts + store FAQ |
| Structured summary + FAQ | owned FAQ page + store listings |
| Platform-split tracking | manual prompt pack (per LLM) |
| Universal 36 is a ceiling | `evaluate_universal_36_ambition` deny |

## How this brands Random Tactical Timer better

1. **Mentions:** AI must *name* “Random Tactical Timer” in category answers — subject-first copy on stores, Reddit, support.
2. **Citations:** AI must have a deep, structured owned page to quote — `/ai-visibility/` FAQ + `llms.txt`.
3. **Category fit:** Prompt pack targets boxing/MMA/BJJ/HIIT queries, not chasing YouTube/Amazon (Universal 36).
4. **Honesty:** This is a long-game discovery lever. It does **not** replace IAP attempt repair. WQTU remains the product NSM.

## Fail-closed CLI

```bash
python3 scripts/agent_ai_visibility.py \
  --platform manual_prompt_pack \
  --packs scripts/tests/fixtures/agent_ai_visibility.json \
  --cite aiv:category-prompt-pack \
  --tracks-mentions 1 --tracks-citations 1 \
  --canonical-name-used 1 --subject-first 1 \
  --surfaces reddit,owned_site,play_store,app_store \
  --third-party-named 1 \
  --has-structured-summary 1 --has-faq-block 1 \
  --tracks-per-platform 1 \
  --chasing-universal-36 0
```

## Live evidence (project 299775, trailing 7d, 2026-09-10)

WQTU `5`. Ranker prefers owned-citation / category prompt work over Semrush AIO vanity scores.

`paywall_purchase_success` is telemetry, not ledger revenue.

## Sources

- https://ai-visibility-index.semrush.com/reports/ai-visibility-index-2026-study-h1
- https://www.semrush.com/news/463141-semrush-releases-expanded-2026-ai-visibility-index-analyzing-126-million-ai-search-prompts/
- https://www.semrush.com/blog/ai-visibility/
