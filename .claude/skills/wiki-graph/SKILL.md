---
name: wiki-graph
description: >
  Steal Karpathy/Neo4j wiki-graph navigation, not Aura or ki. Use when the user
  pastes neo4j/status/2097003261718896819, mentions ki knowledge-index,
  Wikipedia-style hops vs vector-only RAG, or NICD graph precision. Fail closed.
  No Neo4j. Do not rewrite ROSE-lite WIP.
---

# Wiki graph (steal the method)

Karpathy 2026: persist a wiki, don't re-synthesize from raw files every query.
Neo4j 2026: the wiki is a graph. Vector search has no hop. NICD agents that
walked article links beat vector-only on precision, truthfulness, and relevancy.

Do **not** install `ki`. Do **not** open Aura. Do **not** add embeddings.

## Does it help?

| Surface | Use Aura / ki? | Use instead |
| --- | --- | --- |
| Flat vector dump | No | `evaluate_index` engine=`local_graph` |
| "The docs say…" | No | `navigate` then `evaluate_walk` |
| One file's headings | No | STAIR ToC (`scripts/stair_toc.py`) |
| More Neo4j hops | No | Rank IAP / WQTU, not tokens |

## Before claiming a retrieval walked the wiki

```bash
python3 scripts/wiki_graph.py \
  --engine local_graph \
  --pages docs/AGENT_TOKEN_SHUNT.md,docs/AGENT_STAIR_TOC.md \
  --query 'token shunt live evidence WQTU' \
  --cite docs/AGENT_TOKEN_SHUNT.md#live-evidence
```

Allow only when every JSON `ok` is true (process exit 0).
