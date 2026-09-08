# Agent harness (AI Studio-inspired, $0)

Adapted from [Agents in AI Studio Playground](https://ai.google.dev/gemini-api/docs/aistudio-agents) and [Agents overview](https://ai.google.dev/gemini-api/docs/agents). Steal the **method**, not hosted Antigravity or Gemini API.

The CEO URL `https://aistudio.google.com/docs/agents` is the in-product copy of the same Playground Agents surface.

| AI Studio | Random-Timer control plane |
| --- | --- |
| Templates ship `AGENTS.md` + `SKILL.md` | `evaluate_harness_files` |
| Toggle tools; override defaults | `evaluate_tool_allowlist` |
| Network allowlist, not open egress | `evaluate_network_allowlist` |
| Name a stop condition (unbounded loops) | `evaluate_termination` |
| Ephemeral Linux sandbox | `evaluate_sandbox` — worktree only |
| Verify outputs before deploy | `evaluate_verified_execution` |

## What we deliberately did *not* copy

- Hosted Antigravity / Gemini managed agents (pay-as-you-go; one turn is typically 100k–3M tokens).
- Gemini API as primary, AI Studio Playground as a production runtime, or new metered keys.

## Fail-closed CLI

```bash
python3 scripts/studio_agent_harness.py \
  --agents-md --skill-md \
  --tools local_pytest,gh \
  --allowed-tools local_pytest,gh,posthog_sql \
  --domains api.github.com \
  --stop 'write GSD json then stop' \
  --isolation worktree \
  --tests-passed --read-back
```

Allow only when every JSON `ok` is true (process exit 0). Incomplete inputs exit 2.

## Live evidence (project 299775, trailing 7d, 2026-09-08)

WQTU `3`. `timer_started` 349/48. `timer_completed` 76/18. `paywall_view` 12/6. `paywall_dismissed` 9/5. Zero IAP attempts. Ranker puts the attempt path ahead of hosted-sandbox tokens.

`paywall_purchase_success` is telemetry, not ledger revenue.

## Source

- https://aistudio.google.com/docs/agents
- https://ai.google.dev/gemini-api/docs/aistudio-agents
- https://ai.google.dev/gemini-api/docs/agents
