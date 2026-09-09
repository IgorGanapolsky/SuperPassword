# Use-case collection (Dataiku-inspired, $0)

Adapted from the [gated collection](https://content.dataiku.com/dataiku-ai-agent-use-case-collection) and the public [8-case landing page](https://pages.dataiku.com/the-ultimate-guide-to-ai-agent-use-cases). Steal the **method**, not the password PDF, Dataiku, or LLM Mesh.

Do not copy the eight vertical demos. Keep an owned catalog. Run the 3-question test. Skip the agent when the work is simple if-then.

| Dataiku | Random-Timer control plane |
| --- | --- |
| Gated PDF / Agent Connect | `evaluate_source` |
| Expertise / knowledge / security families | `evaluate_family` |
| 3-question agent test | `evaluate_agent_need` |
| Cite a collection case | `pick_owned` + `evaluate_claim` |

## What we deliberately did *not* copy

- The password-protected PDF at content.dataiku.com.
- Predictive-maintenance, clinical-trial, support-ticket, invoicing, or sales agents.
- Dataiku Agent Connect, LLM Mesh, or a multi-agent orchestrator.

## Fail-closed CLI

```bash
python3 scripts/use_case_collection.py \
  --source local_catalog \
  --family iap_attempt \
  --complexity simple_if_then \
  --data single_clean \
  --process static \
  --cases scripts/tests/fixtures/use_case_collection.json \
  --cite case:iap-attempt-path
```

Allow only when every JSON `ok` is true (process exit 0). Incomplete inputs exit 2.

## Live evidence (project 299775, trailing 7d, 2026-09-09)

WQTU `5`. `timer_started` 370/53. `timer_completed` 84/21. `paywall_viewed` 20/10. `paywall_view` 12/6. `paywall_dismissed` 9/5. Zero IAP attempts. Ranker puts the attempt path ahead of more agents.

`paywall_purchase_success` is telemetry, not ledger revenue.

## Source

- https://content.dataiku.com/dataiku-ai-agent-use-case-collection
- https://pages.dataiku.com/the-ultimate-guide-to-ai-agent-use-cases
- https://www.dataiku.com/blog/how-to-select-high-impact-ai-agent-use-cases
