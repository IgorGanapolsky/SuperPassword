---
name: agent-ai-visibility
description: Fail-closed AI visibility controls from Semrush Index 2026 — mentions vs citations, Citation Core, subject-first brand entity, deny paid Semrush AIO under the monthly cap.
---

# Agent AI Visibility

Use when writing store copy, Reddit drafts, FAQ pages, or ranking discovery work for Random Tactical Timer.

## Instructions

1. Track **mentions** and **citations** separately (never one vanity score).
2. Lead sentences with **Random Tactical Timer** as the grammatical subject.
3. Place narrative on Citation Core surfaces: owned FAQ, App Store, Play, Reddit, Stack Overflow.
4. Ship structured summary + FAQ on owned pages (`/ai-visibility/`).
5. Use `marketing/data/ai_visibility_prompt_pack.json` for free per-platform checks.
6. Deny Semrush/Peec/Profound AIO spend under the **$20/month** cap.
7. Do not chase the Universal 36; win category prompts (boxing/MMA/BJJ/HIIT).

## Examples

- Allow: owned FAQ + Reddit draft that names the brand + store FAQ block.
- Deny: “buy Semrush AIO” or “I built an app” with no brand entity.

## Performance Notes

- Zero external spend; long-game discovery hygiene.
- Does not close IAP; pair with paywall work for revenue.

## Troubleshooting

- Exit `2`: inspect JSON keys (`mention_citation`, `brand`, `citation_core`).
- See `docs/AGENT_AI_VISIBILITY.md`.
