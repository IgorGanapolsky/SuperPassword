# DeepSeek V4 router (harness)

## Why this exists

DeepSeek emailed API users (Sep 11, 2026): **V4 Pro API continues after Sep 14, 2026**.

Official pricing docs add the high-ROI detail: from **2026-09-14 04:00 UTC**, `deepseek-v4-pro` is served by **V4.1 Flash** and billed at **Flash** rates. Flash already beats Pro on cost/performance — so the harness prefers Flash always.

## Policy

| Rule | Behavior |
|---|---|
| Default model | `deepseek-flash` |
| Interactive + Pro requested | Still route to Flash (ROI) |
| Background during peak | `defer_off_peak` until next off-peak |
| Month spend ≥ $10 | `failover_local` → `local/hermes-cheap` |
| Fleet cap | $20/mo total external; DeepSeek sub-cap $10 |

Peak (Mon–Fri UTC): `01:00–04:00` and `06:00–10:00`. All other hours off-peak (50% off).

## Commands

```bash
PYTHONPATH=scripts python3 scripts/agent_deepseek_v4_router.py doctor
PYTHONPATH=scripts python3 scripts/agent_deepseek_v4_router.py route "nightly eval" --background
PYTHONPATH=scripts python3 -m unittest scripts.tests.test_agent_deepseek_v4_router -v
```

## Sources

- Email: DeepSeek support → iganapolsky@gmail.com, “Continuation of the DeepSeek V4 Pro API Service”
- https://api-docs.deepseek.com/quick_start/pricing
