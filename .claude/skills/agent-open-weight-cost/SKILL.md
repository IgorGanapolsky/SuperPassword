---
name: agent-open-weight-cost
description: Fail-closed unit-economics and hybrid routing controls for when open-weight models actually save money. Deny ideology GPU fleets and benchmark-only swaps.
---

# Agent Open-Weight Cost

Use when choosing models for agent/tool workloads, estimating inference cost, or deciding API vs local/open-weight under the monthly cap.

## Instructions

1. **Baseline** spend, tokens by task, latency, error/retry, human review.
2. Prefer open weights only for **stable high-volume** tasks with a measurable quality bar.
3. Run **apples-to-apples** evals on real prompts/failures (not leaderboards alone).
4. Compute **fully loaded cost per successful task** including hosting/ops/review.
5. Use **hybrid routing**: cheap first-pass → escalate low-confidence/high-stakes.
6. Require **strategic leverage** (locality, fine-tune, edge, predictable marginal cost)—not vendor-independence vanity.
7. **Pilot** 30–60 days with quality/latency/savings gates and an API fallback.
8. Stay **API-first** for exploration until utilization + TCO justify commit.
9. Deny GPU fleets / over-cap self-host under the $20/month hard cap.

```bash
python3 scripts/agent_open_weight_cost.py \
  --platform hybrid_model_routing \
  --workloads scripts/tests/fixtures/agent_open_weight_cost.json \
  --cite owc:iap-extract-routing \
  --monthly-api-spend-known 1 --tokens-by-task-known 1 \
  --latency-known 1 --error-retry-known 1 --human-review-known 1 \
  --stable-high-volume 1 --quality-bar-measurable 1 \
  --real-prompts 1 --real-failure-cases 1 \
  --measured-task-success 1 --measured-schema-adherence 1 \
  --measured-human-intervention 1 \
  --monthly-operating-cost-usd 5 --successful-tasks-per-month 50 \
  --includes-hosting-ops-review 1 --utilization-adequate 1 \
  --cheap-first-pass 1 --escalate-low-confidence 1 \
  --data-locality 1 \
  --quality-within-tolerance 1 --latency-meets-ux 1 \
  --savings-exceed-ops-cost 1 --review-window-days 45 --api-fallback 1 \
  --exploration-phase 0 --utilization-justifies 1 --tco-justifies 1
```

## Examples

- Allow: hybrid route for repeatable IAP extract with TCO $5/mo and API fallback.
- Deny: “rent A100 to be open-source pure”; “swap model on Elo alone”.

## Performance Notes

- Zero-cost path first; hard monthly cap $20.
- Ranker zeros vendor-independence / parameter-count vanity.

## Troubleshooting

- Exit `2`: inspect `baseline`, `tco`, `routing`, `pilot`, `phase` keys.
- See `docs/AGENT_OPEN_WEIGHT_COST.md`.
