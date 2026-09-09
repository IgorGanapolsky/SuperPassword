# Agent eval + governance (Databricks-inspired, $0)

Adapted from the [2026 State of AI Agents](https://www.databricks.com/resources/ebook/state-of-ai-agents) report. Steal the **method**, not Databricks AI Gateway, Unity Catalog, Agent Bricks, or Lakebase.

Databricks’ useful finding: companies using **evaluation tools** get ~**6x** more AI projects into production; companies using **AI governance** get ~**12x** more. Treat eval + governance as deployment infrastructure, not paperwork. Tie evals to **domain KPIs** (WQTU / IAP), not generic benchmarks. Keep that as a local fail-closed CLI under the **$20/month** hard cap.

| Databricks finding | Random-Timer control plane |
| --- | --- |
| Eval tools → production | `evaluate_evaluation` → `domain_kpi` |
| Governance → production | `evaluate_governance` → `local_fail_closed` |
| Pilot → production gap | `evaluate_stage` requires both |
| Multi-agent growth vanity | ranked as proxy (`multi_agent_count` = 0) |

## What we deliberately did *not* copy

- Databricks Data Intelligence Platform / AI Gateway / Unity Catalog.
- Agent Bricks / Lakebase / Neon-hosted agent DB sprawl as a paid plane.
- Generic leaderboard benchmarks as ship evidence.
- Multi-agent count as a North Star proxy.

## Fail-closed CLI

```bash
python3 scripts/agent_eval_governance.py \
  --platform local_eval_governance \
  --paths scripts/tests/fixtures/agent_eval_governance.json \
  --cite path:iap-attempt-path
```

Allow only when every JSON `ok` is true (process exit 0). Incomplete inputs exit 2.

## Live evidence (project 299775, trailing 7d, 2026-09-09)

WQTU `5`. `timer_started` 371/54. `timer_completed` and paywall funnel still show views without IAP attempts. Ranker puts the attempt path ahead of multi-agent vanity.

`paywall_purchase_success` is telemetry, not ledger revenue.

## Source

- https://www.databricks.com/resources/ebook/state-of-ai-agents
- https://www.databricks.com/sites/default/files/2026-01/State-of-AI-Agents-2026-Final.pdf
- https://www.databricks.com/blog/enterprise-ai-agent-trends-top-use-cases-governance-evaluations-and-more
