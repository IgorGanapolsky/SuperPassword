# Ops context (local Era Context steal)

Source inspiration (ideas only): Era founder nurture email about Context
(2026-09-11) — MoM category moves, recurring inventory, silent increase rules.

We do **not** connect Era/Context SaaS. Local ledger + Python guards under the
hard **$20/month** operating cap.

## What we took

| Era Context idea | Local harness |
|---|---|
| MoM category comparison + why | `compare_categories` |
| List recurring + monthly total + forgotten | `inventory_recurring` |
| Rule: flag silent price increases | `apply_increase_rules` |
| Give assistants real financial context | `assistant_prompt_recipes` + ledger JSON |
| Vendor-independent | `era_app` / Context cloud denied |

## Ledger

`marketing/data/operating_budget_ledger.json` — operator-maintained category
months + recurring rows. Treat as a labeled proxy until live bank feeds exist.

## Smoke

```bash
PYTHONPATH=scripts python3 -m unittest scripts.tests.test_agent_era_context -v
```

## Prompt recipes (for Claude / ChatGPT / Cursor)

1. MoM: "Am I above last month on operating outlay? Which categories went up?"
2. Inventory: "List every active recurring charge. Monthly total? Forgotten?"
3. Rule: "Flag any watched recurring charge that increased since last month."
