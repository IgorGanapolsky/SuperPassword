# Agent Open-Weight Cost (episode-inspired, $0-first)

Adapted from “How to Know When Open-Weight AI Models Actually Save You Money” ([YouTube Music](https://music.youtube.com/watch?v=9DRXbonRtyA)). Steal the **unit-economics + routing method**, not ideology-driven GPU fleets.

| Source construct | Random-Timer control plane |
| --- | --- |
| Baseline spend/tokens/latency/errors/review | `evaluate_baseline` |
| Stable high-volume + quality bar | `evaluate_workload_fit` |
| Apples-to-apples real eval | `evaluate_apples_to_apples` |
| Fully loaded cost / successful task | `evaluate_fully_loaded_cost` |
| Hybrid routing | `evaluate_routing` |
| Strategic leverage (not vendor vanity) | `evaluate_strategic_leverage` |
| Pilot gates + API fallback | `evaluate_pilot` |
| API-first until TCO justifies | `evaluate_exploration_vs_commit` |

Formula enforced:

`fully_loaded_cost_per_success = monthly_operating_cost_usd / successful_tasks_per_month`

Operating cost must stay within the **$20/month** hard cap.

## Mapped to our product

Example: IAP catalog / paywall diagnosis agent traffic

1. Baseline: Cursor/Claude tokens by task, latency, retries, human review minutes
2. Fit: repeatable extract/classify steps with a schema quality bar
3. Eval: real PostHog/store failure cases, not leaderboard Elo
4. Route: local/cheap first-pass → escalate low-confidence to stronger hosted model
5. Pilot 30–60d with API fallback; commit only if utilization + TCO clear the gates

## What we deliberately did *not* copy

- Self-host GPU fleets for “vendor independence” under the monthly cap.
- Benchmark-only model swaps.
- All-open or all-proprietary monoculture.

## Fail-closed CLI

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

## Live evidence (project 299775, trailing 7d, 2026-09-11)

WQTU `5`. Ranker puts IAP/cost-per-success routing ahead of vendor-independence vanity.

`paywall_purchase_success` is telemetry, not ledger revenue.

## Source

- https://music.youtube.com/watch?v=9DRXbonRtyA
