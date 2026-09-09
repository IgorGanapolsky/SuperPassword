---
name: use-case-collection
description: >
  Steal Dataiku's owned-catalog + 3-question skip, not the gated PDF. Use when
  the user pastes content.dataiku.com/dataiku-ai-agent-use-case-collection,
  mentions predictive maintenance, clinical trial agents, expertise / knowledge
  / security families, or Agent Connect. Fail closed. No Dataiku.
---

# Use-case collection (steal the method)

Dataiku ships eight vertical demos behind a password PDF. We keep an owned
catalog and skip the agent when the work is simple if-then, one clean source,
or a static process.

Do **not** open the gated PDF. Do **not** sign up for Dataiku. Do **not**
stand up Agent Connect.

## Does it help?

| Surface | Use Dataiku? | Use instead |
| --- | --- | --- |
| Password PDF | No | `evaluate_source` |
| Maintenance / clinical demo | No | `evaluate_family` |
| Do we need an agent? | No | `evaluate_agent_need` |
| More agents | No | Rank IAP / WQTU, not tokens |

## Before claiming a collection case

```bash
python3 scripts/use_case_collection.py \
  --source local_catalog \
  --family iap_attempt \
  --complexity simple_if_then \
  --data single_clean \
  --process static \
  --cases scripts/tests/fixtures/use_case_collection.json \
  --cite case:iap-attempt-path
```

Allow only when every JSON `ok` is true (process exit 0).
