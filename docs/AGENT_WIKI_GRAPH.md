# Wiki graph (Karpathy / Neo4j-inspired, $0)

Adapted from [Neo4j on X](https://x.com/neo4j/status/2097003261718896819) and [Scaling Karpathy’s LLM wiki](https://neo4j.com/blog/agentic-ai/scaling-karpathy-llm-wiki-graph/). Steal the **method**, not Aura, `ki`, or a Podman Neo4j.

A folder of markdown already is a graph: documents, heading sections (`HAS`), and links (`LINKS_TO`). Vector search gives similarity, not shape. NICD at Newcastle walked a Wikipedia-style graph and beat vector-only agents. Do that on our docs. Do not stand up a graph database.

| Neo4j / ki | Random-Timer control plane |
| --- | --- |
| Vault → Document → Section | `build_graph` |
| `LINKS_TO` hops | `navigate` BFS |
| Cite a URI from outline/search | `evaluate_walk` |
| No embeddings at index time | local parse only |
| Disposable index | rebuild from `--pages` |

## What we deliberately did *not* copy

- `curl … knowledge-index.ai/install.sh`, `ki configure`, Aura, Podman `neo4j:latest`.
- Cypher, Graph Data Science, paid embeddings.

STAIR ToC (`scripts/stair_toc.py`) still addresses one file. This module walks **across** files.

## Fail-closed CLI

```bash
python3 scripts/wiki_graph.py \
  --engine local_graph \
  --pages docs/AGENT_TOKEN_SHUNT.md,docs/AGENT_STAIR_TOC.md \
  --query 'token shunt live evidence WQTU' \
  --cite docs/AGENT_TOKEN_SHUNT.md#live-evidence
```

Allow only when every JSON `ok` is true (process exit 0). Incomplete inputs exit 2.

## Live evidence (project 299775, trailing 7d, 2026-09-08)

WQTU `3`. `timer_started` 349/48. `timer_completed` 76/18. `paywall_viewed` 19/9. `paywall_view` 12/6. `paywall_dismissed` 9/5. Zero IAP attempts. Ranker puts the attempt path ahead of more graph hops.

`paywall_purchase_success` is telemetry, not ledger revenue.

## Source

- https://x.com/neo4j/status/2097003261718896819
- https://neo4j.com/blog/agentic-ai/scaling-karpathy-llm-wiki-graph/
