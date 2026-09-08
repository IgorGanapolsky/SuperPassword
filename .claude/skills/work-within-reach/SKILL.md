---
name: work-within-reach
description: >
  Steal OpenAI Friar 2026-09-08 methods, not GPT-6 or ads. Use when the user
  pastes "The Work Now Within Reach", mentions completed-task ROI, attempt
  efficiency, capital discipline, or consumer/enterprise flywheels. Fail closed.
  No OpenAI API primary, no Jalapeno, no new metered models.
---

# Work within reach (steal the method)

Friar 2026-09-08: the result that matters is the **completed task**. Better
routes finish in fewer attempts. Capital is judged by demand served, time to
productive, and whether returns justify the spend. People set priorities and
judge; agents take specialist time.

Do **not** subscribe to GPT‑6 Astra. Do **not** add OpenAI API as primary.

## Does it help?

| Surface | Use the paid product? | Use instead |
| --- | --- | --- |
| Tokens / PR velocity | No | `evaluate_completed_task` — WQTU / timer / IAP |
| More agent retries | No | `evaluate_attempt_efficiency` |
| New model or chip | No | `evaluate_capital_discipline` under `$20/mo` |
| Tool turns on 3B | No | `evaluate_workload_fit` → hermes-main |
| Paywall on first open | No | `evaluate_discovery_to_paid` after a finish |

## Before claiming work is within reach

```bash
python3 scripts/work_within_reach.py \
  --metric wqtu \
  --attempts 3 --completed 1 \
  --service hermes_main --demand 'tool turns' --monthly-usd 0 --mtd-usd 0 \
  --task-kind tool_turn --model hermes-main \
  --timer-completed 1 --paywall-shown
```

Allow only when every JSON `ok` is true (process exit 0).
