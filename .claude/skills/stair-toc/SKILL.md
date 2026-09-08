---
name: stair-toc
description: >
  Steal IBM STAIR table-of-contents retrieval, not a fine-tuned index. Use when
  the user pastes omarsar0 STAIR, mentions ToC addressing, length-chunk RAG
  throwing away hierarchy, or generative-retrieval hallucination. Fail closed.
  No paid embeddings. Do not rewrite ROSE-lite WIP.
---

# STAIR ToC (steal the method)

IBM STAIR 2026: retrievers that split by length discard the hierarchy a table of
contents already encodes. Ground the address space in that ToC so claims cite a
real heading path. Hallucination stays the standing objection to generative IR.

Do **not** fine-tune DSI/STAIR. Do **not** add paid embedding APIs.

## Does it help?

| Surface | Use STAIR product? | Use instead |
| --- | --- | --- |
| Flat 512-token chunks | No | `evaluate_chunking` mode=`toc` |
| "The docs say…" | No | `evaluate_grounding` against `path#slug` |
| Lost-in-the-middle dump | No | `retrieve_by_toc` |
| More embedding dims | No | Rank IAP / WQTU, not tokens |

## Before claiming a retrieval is grounded

```bash
python3 scripts/stair_toc.py \
  --source docs/AGENT_WORK_WITHIN_REACH.md \
  --markdown-file docs/AGENT_WORK_WITHIN_REACH.md \
  --mode toc \
  --query 'live evidence WQTU' \
  --cite docs/AGENT_WORK_WITHIN_REACH.md#live-evidence
```

Allow only when every JSON `ok` is true (process exit 0).
