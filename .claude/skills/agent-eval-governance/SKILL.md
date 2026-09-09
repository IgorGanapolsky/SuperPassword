---
name: agent-eval-governance
description: >
  Steal Databricks State of AI Agents eval+governance method locally, not
  Databricks cloud. Use when the user asks about AI Gateway, Unity Catalog,
  Agent Bricks, Lakebase, or why pilots fail to reach production. Fail closed
  under the $20 cap.
---

# Agent eval + governance (steal the method)

Domain KPI evals + local fail-closed governance before claiming production.
Do **not** adopt Databricks AI Gateway / Agent Bricks as the control plane.

## Before claiming an agent is production-ready

```bash
python3 scripts/agent_eval_governance.py \
  --platform local_eval_governance \
  --paths scripts/tests/fixtures/agent_eval_governance.json \
  --cite path:iap-attempt-path
```

Allow only when every JSON `ok` is true (process exit 0).
