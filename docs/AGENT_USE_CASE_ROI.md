# Use-case ROI (Dataiku-inspired, $0)

Adapted from [Dataiku’s agent use-case guide](https://pages.dataiku.com/the-ultimate-guide-to-ai-agent-use-cases) and the [5-step selection framework](https://www.dataiku.com/blog/how-to-select-high-impact-ai-agent-use-cases). Steal the **method**, not Dataiku or LLM Mesh.

Do not build agents that will not scale. Start from a business problem. Score ROI, complexity, and readiness. Pick **one** sweet-spot case.

| Dataiku | Random-Timer control plane |
| --- | --- |
| Start with business problems | `evaluate_problem` |
| Score ROI / complexity / readiness | `score_use_case` |
| Pick one and scale | `pick_one` |
| Cite the scored pick | `evaluate_claim` |

## What we deliberately did *not* copy

- Dataiku Agent Hub, LLM Mesh, Govern, or the gated PDF.
- Predictive-maintenance or clinical-trial agents that are not our product.

## Fail-closed CLI

```bash
python3 scripts/use_case_roi.py \
  --platform local_score \
  --problem iap_attempt \
  --cases scripts/tests/fixtures/use_case_roi.json \
  --cite case:iap-attempt-path
```

Allow only when every JSON `ok` is true (process exit 0). Incomplete inputs exit 2.

## Live evidence (project 299775, trailing 7d, 2026-09-08)

WQTU `3`. `timer_started` 352/49. `timer_completed` 78/19. `paywall_viewed` 19/9. `paywall_view` 12/6. `paywall_dismissed` 9/5. Zero IAP attempts. Ranker puts the attempt path ahead of more agents.

`paywall_purchase_success` is telemetry, not ledger revenue.

## Source

- https://pages.dataiku.com/the-ultimate-guide-to-ai-agent-use-cases
- https://www.dataiku.com/blog/how-to-select-high-impact-ai-agent-use-cases
