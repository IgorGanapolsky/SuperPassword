# Durable canvas (GitHub-inspired, $0)

Adapted from [GitHub on Threads](https://www.threads.com/@github/post/Dc9agX7j_w4) and [How canvases make agentic workflows visible](https://github.blog/ai-and-ml/github-copilot/how-canvases-make-agentic-workflows-visible-steerable-and-cost-efficient/). Steal the **method**, not the Copilot app.

Chat is for intent. Once work starts, a transcript is a bad data structure. Persist stages, drafts, and approval points on a file. Cite that file. Do not reconstruct status from scrollback.

| GitHub Copilot canvas | Random-Timer control plane |
| --- | --- |
| Define workflow states | `persist_canvas` stages |
| Persist drafts immediately | `drafts` keys |
| Explicit approval points | `approvals` |
| Cite the surface, not chat | `evaluate_source` + `evaluate_claim` |

## What we deliberately did *not* copy

- `/create-canvas` in the Copilot app.
- Copilot Pro / Pro+ credits, awesome-copilot extensions, Java Modernization Studio.

## Fail-closed CLI

```bash
python3 scripts/durable_canvas.py \
  --surface local_canvas \
  --canvas scripts/tests/fixtures/durable_canvas_iap.json \
  --source canvas \
  --cite stage:iap-attempt-path
```

Allow only when every JSON `ok` is true (process exit 0). Incomplete inputs exit 2.

## Live evidence (project 299775, trailing 7d, 2026-09-08)

WQTU `3`. `timer_started` 349/48. `timer_completed` 76/18. `paywall_viewed` 19/9. `paywall_view` 12/6. `paywall_dismissed` 9/5. Zero IAP attempts. Ranker puts the attempt path ahead of more canvas UX.

`paywall_purchase_success` is telemetry, not ledger revenue.

## Source

- https://www.threads.com/@github/post/Dc9agX7j_w4
- https://github.blog/ai-and-ml/github-copilot/how-canvases-make-agentic-workflows-visible-steerable-and-cost-efficient/
