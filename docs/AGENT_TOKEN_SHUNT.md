# Token shunt (Spotify Portal-inspired, $0)

Adapted from [Daniel San](https://x.com/dani_avila7/status/2097154860235792780) on [Portal by Spotify](https://engineering.atspotify.com/2026/9/portal-by-spotify-cut-my-claude-code-token-usage-by-90). Steal the **method**, not Portal, AiKA, or Gemini Flash.

Most agent spend is I/O, not thinking. Advisory `CLAUDE.md` routing is ignored. Enforce it.

| Spotify shunt | Random-Timer control plane |
| --- | --- |
| PreToolUse blocks Read > 350 lines | `evaluate_read_intercept` |
| Targeted offset/limit passes | `targeted=True` |
| Return a summary, not the file | `evaluate_context_return` |
| Keep frontier for reasoning | `evaluate_task_route` — debug/architecture stay on `hermes-main` |
| Delegate boilerplate | `local_slice` only — not Flash |

## What we deliberately did *not* copy

- `spotify/portal-ai-plugins`, Portal CLI, AiKA modes, Gemini 2.5 Flash as worker.
- One hosted turn is metered. Worker here is a **local slice**, not a new API.

## What Spotify found does not work (keep)

- Do not delegate **editing**. Cheap summaries lack reliable line numbers. Targeted `offset`/`limit` reads stay allowed.
- Do not delegate **reasoning**. Cheap workers miss thread-safety and architecture. Those stay on `hermes-main`.
- Advisory `CLAUDE.md` routing is ignored. The CLI is fail-closed.

## Fail-closed CLI

```bash
python3 scripts/token_shunt.py \
  --lines 800 --targeted \
  --task-kind reasoning --model hermes-main \
  --source-lines 800 --returned-lines 40
```

Allow only when every JSON `ok` is true (process exit 0). Incomplete inputs exit 2.

## Live evidence (project 299775, trailing 7d, 2026-09-08)

WQTU `3`. `timer_started` 349/48. `timer_completed` 76/18. `paywall_view` 12/6. `paywall_dismissed` 9/5. Zero IAP attempts. Ranker puts the attempt path ahead of more frontier tokens.

`paywall_purchase_success` is telemetry, not ledger revenue.

## Source

- https://x.com/dani_avila7/status/2097154860235792780
- https://engineering.atspotify.com/2026/9/portal-by-spotify-cut-my-claude-code-token-usage-by-90
