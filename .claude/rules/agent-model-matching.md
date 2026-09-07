# Agent-Model Matching + HydraFusion Orchestration

## Why this exists

GitHub [Project HydraFusion](https://github.blog/ai-and-ml/github-copilot/project-hydrafusion-frontier-quality-via-multi-model-orchestration/)
(2026-09-04) shows frontier quality can come from **runtime orchestration**
(Single / Cascade / Critique) rather than always calling the strongest model.

This repo implements the same idea **locally at $0 incremental SaaS cost**:

```bash
python3 scripts/hydrafusion_route.py --task "…" --risk medium --files 8 \
  --capabilities code_generation,debugging
```

Agents MUST prefer the returned pattern before spawning expensive legs.

## Execution patterns (pick least complex that clears the bar)

| Pattern | When | Legs |
| :--- | :--- | :--- |
| **single** | Low-risk utility, ≤2 files, tool-only | draft |
| **cascade** | Medium implement/fix; draft cheap first | draft → quality gate → escalate if rejected |
| **critique** | High-risk / store / security / publish review | draft → isolated tool-less critic (other family) → revise once |

## Operating principles (binding)

1. **Complete accounting** — every leg (draft/critique/revise/escalate/gate) is listed with `cost_accounted: true`.
2. **Bounded execution** — each leg has `timeout_s`; cancel rather than infinite retry.
3. **Isolated review** — critique legs are tool-less and must not modify the repo.
4. **Fail-safe application** — if gate fails or workflow cancels, apply **no** incomplete patch.
5. **Validated routing** — `validate_plan()` must return `[]` before execution.

## Task categories & fallback chains

Match the right brain to the right task. HydraFusion plans reference these categories.

| Category | Description | Primary (logical) | Fallback 1 | Fallback 2 |
| :--- | :--- | :--- | :--- | :--- |
| **UltraBrain** | Planning, multi-file reasoning, coordination | Claude Sonnet-class | Gemini Pro-class | GPT-4o/5-class |
| **Deep** | Large refactor, hard bugs, store/security drafts | Claude Opus-class / GPT-5-class | Claude Sonnet-class | Gemini Pro-class |
| **Quick** | Search, scaffolding, cascade first-draft, CLI | Gemini Flash / Composer-fast | Claude Haiku-class | GPT-mini-class |
| **Visual** | UI/UX, screenshots, multimodal QA | Gemini Pro multimodal | GPT-4o-class | Claude Sonnet-class |

## Capability signals

Route using HydraFusion-style capability hints (pass into `hydrafusion_route.py`):

- `reasoning` — architecture, trade-offs, policy
- `code_generation` — implement / patch
- `debugging` — failing tests, RCA
- `tool_use` — gh/adb/browser/CLI automation

## Quality gate (Cascade)

Accept draft only when ALL are true:

- tests passed (or scoped N/A with evidence)
- evidence present (command + path + sanitized output)
- no secrets leaked
- patch validated (diff reviewed / CI green path)

Otherwise escalate once to `escalate_category`. Do not loop.

## Critique (Rubber-Duck style)

- Critic family **must differ** from draft family (Claude ↔ Gemini/GPT).
- Critic is **read-only / tool-less**.
- Drafter revises **once**, then stop (or open PR with residual risks named).

Reuse `.claude/skills/blind-review` for multi-critic PR reviews; use HydraFusion
`critique` for single independent critic on high-risk one-shot tasks.

## Resolution logic (Task tool)

1. Run `scripts/hydrafusion_route.py` (or apply the table above).
2. Map `draft_category` / `escalate_category` / `critic.category` to `Task` models.
3. Prefer environment-available providers; walk fallbacks on rate limits.
4. Record legs + gate outcome in the PR/session note (complete accounting).

## Brain personalities (prompt style)

### Claude-family
Mechanics-driven prompts, checklists, structured JSON/YAML.

### GPT-family
Intent/outcome first; autonomous exploration.

### Gemini-family
Large context + multimodal; dump relevant files and ask for global analysis.

## Budget

Hard cap **$20 USD/month** external spend. HydraFusion local routing is free.
Do not purchase Copilot HydraFusion preview seats without CEO approval.


## Day-0 OSS Bringup (Perplexity ROSE pattern)

Before spending any budget on a new open-weight model (`gpt-oss-*`, local MLX, Ollama):

1. Run `scripts/agent_rose_lite/day0.py` probes (`harmony_tokenizer`, `local_mlx_or_ollama`, `fp8_or_int4`).
2. Prefer **local zero-cost** path when available.
3. Never auto-start paid GPU serving; `estimated_monthly_usd` must stay ≤ `$20`.
4. Promote only when `tp1_smoke=ok` and `within_budget=true`.

Retrieval for agent memory uses ROSE-lite hybrid recall (`memory_manager.py --recall --query ...`) — Matryoshka hash embeddings + salience, not a paid vector DB.
