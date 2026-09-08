---
name: hermes-desktop-router-policy
description: >
  Steal OpenRouter pin-vs-route and Ori tool-eval, not the paid product. Use
  when Hermes Desktop picks Copilot ACP, Fable, Gim 5.3, hermes-local 3B, or
  OpenRouter as primary, or when a tool turn babysits with fake pip/terminal
  theater. Fail closed. No ori login, no OpenRouter Analytics API.
---

# Hermes Desktop router policy (OpenRouter steal, zero-cost)

OpenRouter blog/webinar (2026-09): let a router pick a model *or* pin one;
grade your agent on *your* prompts (Ori Eval); inspect usage per agent/model.

Steal the method. Do **not** install Ori, do **not** `ori login`, and do **not**
call OpenRouter Analytics. Those are per-token / billed and blow the monthly cap.

## Does it help?

| Surface | Use OpenRouter / Ori? | Use instead |
| --- | --- | --- |
| Hermes Desktop tool turns | No as primary | Pin `hermes-main` via LiteLLM gateway |
| ACP / Fable / Gim sessions | Never | New chat + `diagnose-hermes-acp-tool-bridge` |
| Local 3B (`hermes-local`) | Never as tool primary | Route-guard ladder after `hermes-main` |
| Agent eval (tools called / avoided) | Steal assertions only | `hermes_desktop_router_policy.py` |
| Usage by model | Steal locally | `~/.hermes/litellm-logs/traffic.jsonl` |

## Pin vs route

- **Pin** `hermes-main` (`custom:litellm-gateway`) for Desktop tool turns.
- Router may pick only `nous-deepseek` → `glm-5.3` → `gpt-4o`.
- **Block** `copilot-acp`, `hermes-local` / `qwen2.5:3b`, OpenRouter-as-primary.

```bash
python3 scripts/hermes_desktop_router_policy.py \
  --provider custom:litellm-gateway --model hermes-main --intent tool
```

Allow only when JSON `route.allow` is true.

## Ori-style eval (no LLM judge)

Assert the transcript called `terminal` or `browser` directly. Fail on meta
`tool_call` without `name`, nested `tool_search`, or babysit prose
(`pip install`, `notebookLM`, `terminal()` theater).

```bash
python3 scripts/hermes_desktop_router_policy.py \
  --tools terminal --assistant-text "wrote the proof file"
```

## Local analytics

Optional parse of LiteLLM traffic JSONL. Do not call OpenRouter Analytics.

```bash
python3 scripts/hermes_desktop_router_policy.py \
  --traffic-jsonl "$HOME/.hermes/litellm-logs/traffic.jsonl"
```
