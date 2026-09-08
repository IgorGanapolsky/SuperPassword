---
name: aistudio-harness
description: >
  Steal Google AI Studio Agents methods, not hosted Antigravity or Gemini API.
  Use when the user pastes aistudio.google.com/docs/agents, mentions managed
  agents, AGENTS.md plus SKILL.md templates, tool toggles, network allowlists,
  or unbounded token loops. Fail closed. No Gemini API primary.
---

# AI Studio harness (steal the method)

AI Studio Playground Agents: templates mount `AGENTS.md` + `SKILL.md`, toggle
tools, lock an ephemeral sandbox, and require an explicit network allowlist.
A single prompt can loop until you name a stop condition. Humans verify
outputs before deploy.

Do **not** create a Gemini managed agent. Do **not** run production work in
AI Studio Playground (one turn is typically 100k–3M tokens).

## Does it help?

| Surface | Use hosted Agents? | Use instead |
| --- | --- | --- |
| Persona + workflow | No | `evaluate_harness_files` — AGENTS.md + SKILL.md |
| All tools on | No | `evaluate_tool_allowlist` |
| Open sandbox egress | No | `evaluate_network_allowlist` |
| "Just keep going" | No | `evaluate_termination` |
| Write on checkout | No | `evaluate_sandbox` — worktree |
| Claim done | No | `evaluate_verified_execution` |

## Before claiming the harness is ready

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

Allow only when every JSON `ok` is true (process exit 0).
