# Agent work within reach (Friar/OpenAI-inspired, $0)

Adapted from Sarah Friar, *The Work Now Within Reach* (OpenAI, 2026-09-08). Steal the **method**, not GPT‑6, Jalapeño, or ads.

| Friar | Random-Timer control plane |
| --- | --- |
| Completed task is the result | WQTU / `timer_completed` / IAP attempt — not tokens |
| Fewer attempts to finish | `evaluate_attempt_efficiency` |
| Capital discipline | Named demand, fast to productive, stay under `$20/mo` |
| Best system per workload | Tool turns on `hermes-main`; 3B babysit denied |
| Free discovery then paid value | Wall only after a finished training session |
| Humans set priorities and judge | Agents take specialist time; no human cleanup |

## What we deliberately did *not* copy

- GPT‑6 Astra, OpenAI API as primary, Jalapeño, advertising, or any new metered route.

## Fail-closed CLI

```bash
python3 scripts/work_within_reach.py \
  --metric wqtu \
  --attempts 3 --completed 1 \
  --service hermes_main --demand 'tool turns' --monthly-usd 0 --mtd-usd 0 \
  --task-kind tool_turn --model hermes-main \
  --timer-completed 1 --paywall-shown
```

Allow only when every JSON `ok` is true (process exit 0). Incomplete inputs exit 2.

## Live evidence (project 299775, trailing 7d, 2026-09-08)

WQTU `3`. `timer_started` 349/48 users. `timer_completed` 76/18. `paywall_view` 12/6. `paywall_dismissed` 9/5. Zero IAP attempts. Ranker puts the attempt path ahead of more tokens.

`paywall_purchase_success` is telemetry, not ledger revenue.

## Source

https://openai.com/index/the-work-now-within-reach/
