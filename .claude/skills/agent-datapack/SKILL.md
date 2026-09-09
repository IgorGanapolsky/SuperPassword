---
name: agent-datapack
description: >
  Steal Meko datapack + decision-trace method locally, not cloud.mekodata.ai.
  Use when the user asks about Meko, collective memory, shared agent knowledge,
  or mcp.mekodata.ai. Fail closed under the $20 cap.
---

# Agent datapack (steal the method)

Local JSON packs. Verified promote only. Query local memory before reprocessing.
Do **not** sign up for Meko cloud. Do **not** wire `mcp.mekodata.ai`.

## Before claiming shared agent memory

```bash
python3 scripts/agent_datapack.py \
  --platform local_datapack \
  --packs scripts/tests/fixtures/agent_datapack.json \
  --cite pack:iap-attempt-path \
  --queried-local 1
```

Allow only when every JSON `ok` is true (process exit 0).
