# STAIR ToC retriever (IBM-inspired, $0)

Adapted from [elvis / omarsar0](https://x.com/omarsar0/status/2096648881962652046) on IBM STAIR (Kumar et al., 2026). Steal the **method**, not a fine-tuned generative index.

| STAIR | Random-Timer control plane |
| --- | --- |
| Length chunks discard hierarchy | `evaluate_chunking` — `length` fails |
| Table of contents is the address space | `extract_toc` → `path#slug` |
| Retrieve against corpus structure | `retrieve_by_toc` |
| Hallucination is the standing objection | `evaluate_grounding` — invented addresses fail |

## What we deliberately did *not* copy

- Fine-tuned Differentiable Search Index / STAIR model weights.
- Paid embedding SaaS, SearchTome training, or any new metered retrieval route.

ROSE-lite hash embeddings stay length/token bags. This plane adds the missing **ToC address**. Do not rewrite the ROSE-lite WIP tree.

## Fail-closed CLI

```bash
python3 scripts/stair_toc.py \
  --source docs/AGENT_WORK_WITHIN_REACH.md \
  --markdown-file docs/AGENT_WORK_WITHIN_REACH.md \
  --mode toc \
  --query 'live evidence WQTU' \
  --cite docs/AGENT_WORK_WITHIN_REACH.md#live-evidence
```

Allow only when every JSON `ok` is true (process exit 0). Incomplete inputs exit 2.

## Live evidence (project 299775, trailing 7d, 2026-09-08)

WQTU `3`. `timer_started` 349/48. `timer_completed` 76/18. `paywall_view` 12/6. `paywall_dismissed` 9/5. Zero IAP attempts. Ranker puts the attempt path ahead of more length-chunks.

`paywall_purchase_success` is telemetry, not ledger revenue.

## Source

- https://x.com/omarsar0/status/2096648881962652046
- https://academy.dair.ai/papers/stair-structure-aware-information-retriever-a-novel-dataset-and-llm-based-retrie-2609.03874
