# Agent ROSE-lite (Perplexity-inspired, $0)

Adapted from Perplexity engineering posts (Sept 2025–2026):

| Perplexity | Random-Timer ROSE-lite |
| --- | --- |
| Ivy (Rust HTTP: tokenize, template, chunk) | `scripts/agent_rose_lite/ivy.py` |
| Tulip (token-budget batching; ~512 tokens saturate) | `scripts/agent_rose_lite/tulip_batch.py` |
| ROSE (CUDA graphs, LazyTensor, unified LLM+embed) | `scripts/agent_rose_lite/embeddings.py` + hybrid `memory_manager.recall(query=...)` |
| CuTeDSL specialization (JIT specialize hot kernels) | Scene filters + Matryoshka dim knobs (64/32/16) without rebuild |
| GPT-OSS Day-0 (weight map → TP=1 → parallelism → cost) | `scripts/agent_rose_lite/day0.py` under **$20/mo** hard cap |

## What we deliberately did *not* copy

- Paid Hopper/Blackwell GPU fleets, FlashInfer, DeepGEMM, CuTeDSL kernels — outside budget.
- Separate embedding microservice — Perplexity’s key insight is **reuse one stack**; we reuse `memory_manager`.

## Usage

```bash
# Hybrid semantic recall (stdlib hash embeddings)
python3 .claude/scripts/memory/memory_manager.py --recall --query "Play API 36 Robolectric"

# Day-0 bringup gate for a new OSS model (no spend)
python3 -c "from agent_rose_lite.day0 import run_day0_bringup; print(run_day0_bringup('gpt-oss-20b', {'harmony_tokenizer': True, 'local_mlx_or_ollama': False, 'fp8_or_int4': True}).to_dict())"
```

## Sources

- https://www.perplexity.ai/hub/blog/fast-embeddings-on-gpus
- https://www.perplexity.ai/hub/blog/cutedsl-at-perplexity
- https://www.perplexity.ai/hub/blog/gpt-oss-on-day-0
