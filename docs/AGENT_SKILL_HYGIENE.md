# Skill hygiene (pvncher-inspired, $0)

Adapted from [Eric Provencher's GPT-6 Astra guidance](https://x.com/pvncher/status/2095991462416490862). Steal the **method**, not GPT-6 Astra or OpenAI-as-primary.

Too many bloated skills burn context and pull the wrong instructions. Keep descriptions short, use progressive disclosure, keep always-on docs lean, and define completion before starting.

| pvncher / Astra | Random-Timer control plane |
| --- | --- |
| Short skill descriptions | `evaluate_description` |
| Progressive disclosure router | `evaluate_disclosure` |
| Lean AGENTS.md | `evaluate_always_on` |
| Define completion | `evaluate_completion` |
| Pick one hygienic skill | `pick_hygiene` |

## What we deliberately did *not* copy

- GPT-6 Astra as primary model.
- OpenAI/Codex upgrade spend.
- Downloading more skills into every repo.

## Fail-closed CLI

```bash
python3 scripts/skill_hygiene.py \
  --platform local_hygiene \
  --skills scripts/tests/fixtures/skill_hygiene.json \
  --cite skill:iap-attempt-path
```

Allow only when every JSON `ok` is true (process exit 0). Incomplete inputs exit 2.

## Live evidence (project 299775, trailing 7d, 2026-09-09)

WQTU `5`. `timer_started` 370/53. `timer_completed` 84/21. `paywall_viewed` 20/10. `paywall_view` 12/6. `paywall_dismissed` 9/5. Zero IAP attempts. Ranker puts the attempt path ahead of more skills.

`paywall_purchase_success` is telemetry, not ledger revenue.

## Source

- https://x.com/pvncher/status/2095991462416490862
