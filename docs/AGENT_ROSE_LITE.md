# Agent ROSE-lite (Perplexity-inspired, $0)

Adapted from Perplexity engineering posts (Sept 2025–2026):

| Perplexity | Random-Timer ROSE-lite |
| --- | --- |
| Ivy (Rust HTTP: tokenize, template, chunk) | `scripts/agent_rose_lite/ivy.py` |
| Tulip (token-budget batching; ~512 tokens saturate) | `scripts/agent_rose_lite/tulip_batch.py` |
| ROSE (CUDA graphs, LazyTensor, unified LLM+embed) | `embeddings.py` + hybrid `memory_manager.recall(query=...)` |
| CuTeDSL specialization (JIT specialize hot kernels) | Scene filters + Matryoshka dim knobs (64/32/16) without rebuild |
| GPT-OSS Day-0 (weight map → TP=1 → parallelism → cost) | `day0.py` under **$20/mo** hard cap |

## What we deliberately did *not* copy

- Paid Hopper/Blackwell GPU fleets, FlashInfer, DeepGEMM, CuTeDSL kernels — outside budget.
- Separate embedding microservice — Perplexity’s key insight is **reuse one stack**; we reuse `memory_manager`.

## Automation (no human CLI)

ROSE-lite is wired into the agent runtime. Agents must never ask the CEO to run recall/ingest.

| Path | Trigger | Entrypoint |
| --- | --- | --- |
| Claude Code | `SessionStart` / `UserPromptSubmit` via tracked `scripts/agent_rose_lite/claude_hooks.json` (applied into `.claude/settings.json` by `apply_claude_hooks.py`) | `autowire.py --mode session-start\|prompt-context` |
| Cursor | `.cursor/hooks.json` → `sessionStart` / `beforeSubmitPrompt` | same `autowire.py` |
| GitHub Actions | `.github/workflows/rose-lite-autowire.yml` daily cron | `autowire.py --mode ci` → `marketing/data/rose_lite_autowire.json` |

Session artifacts land in `.claude/memory/rose_lite_session.json` (gitignored). CI GSD snapshot is tracked under `marketing/data/`.

## Sources

- https://www.perplexity.ai/hub/blog/fast-embeddings-on-gpus
- https://www.perplexity.ai/hub/blog/cutedsl-at-perplexity
- https://www.perplexity.ai/hub/blog/gpt-oss-on-day-0
