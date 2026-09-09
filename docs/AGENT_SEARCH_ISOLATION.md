# Search isolation (ArcticSwarm-inspired, $0)

Adapted from [Rohan Paul's ArcticSwarm summary](https://x.com/rohanpaul_ai/status/2097089066579988968) and [arXiv:2609.01870](https://arxiv.org/abs/2609.01870). Steal the **method**, not ArcticSwarm, Qwen-as-primary, or more agents.

Premature consensus happens when agents read peers during search and converge on the first plausible idea. Isolate searches, gather findings, then review.

| ArcticSwarm | Random-Timer control plane |
| --- | --- |
| Gated isolation during search | `evaluate_isolation` |
| Evidence before collaboration | `evaluate_evidence` |
| Structured review before agree | `evaluate_consensus` |
| Cite one cleared path | `pick_path` |

## What we deliberately did *not* copy

- ArcticSwarm / MiroFlow stacks.
- Spawning more agents for majority voting.
- Qwen or GPT as a new primary model.

## Fail-closed CLI

```bash
python3 scripts/search_isolation.py \
  --platform local_isolation \
  --paths scripts/tests/fixtures/search_isolation.json \
  --cite path:iap-attempt-path
```

Allow only when every JSON `ok` is true (process exit 0). Incomplete inputs exit 2.

## Live evidence (project 299775, trailing 7d, 2026-09-09)

WQTU `5`. `timer_started` 370/53. `timer_completed` 84/21. `paywall_viewed` 20/10. `paywall_view` 12/6. `paywall_dismissed` 9/5. Zero IAP attempts. Ranker puts the attempt path ahead of more agents.

`paywall_purchase_success` is telemetry, not ledger revenue.

## Source

- https://x.com/rohanpaul_ai/status/2097089066579988968
- https://arxiv.org/abs/2609.01870
