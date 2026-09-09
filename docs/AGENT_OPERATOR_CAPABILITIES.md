# Operator capabilities (Astra-inspired, $0)

Adapted from [OpenAI GPT-6 Astra](https://openai.com/index/gpt-6-astra/) capability guidance. Steal the **method**, not ChatGPT Pro, Astra Desktop, or `gpt-6-astra` API as primary.

API list price is about **$10 / $50 per million tokens** — that alone can blow the **$20/month** hard cap. Treat the agent as a local computer operator via reusable CLIs + BrowserOS, default to medium effort, and keep product work on the IAP attempt path.

| Astra / “King Mode” tip | Random-Timer control plane |
| --- | --- |
| ChatGPT Pro / Codex app | `evaluate_surface` → local CLI |
| Computer Use desktop | `evaluate_harness` → BrowserOS |
| Medium reasoning default | `evaluate_effort` |
| Build reusable CLIs | allow `local_cli` |

## What we deliberately did *not* copy

- ChatGPT Pro / Business / Enterprise upgrades.
- `gpt-6-astra` API as primary model.
- Blender / Unreal “single-prompt game” demos as product work.
- Max/xhigh reasoning as the default.

## Fail-closed CLI

```bash
python3 scripts/operator_capabilities.py \
  --platform local_operator \
  --capabilities scripts/tests/fixtures/operator_capabilities.json \
  --cite cap:iap-attempt-path
```

Allow only when every JSON `ok` is true (process exit 0). Incomplete inputs exit 2.

## Live evidence (project 299775, trailing 7d, 2026-09-09)

WQTU `5`. `timer_started` 370/53. `timer_completed` 84/21. `paywall_viewed` 20/10. `paywall_view` 12/6. `paywall_dismissed` 9/5. Zero IAP attempts. Ranker puts the attempt path ahead of an Astra upgrade.

`paywall_purchase_success` is telemetry, not ledger revenue.

## Source

- https://openai.com/index/gpt-6-astra/
- https://developers.openai.com/api/docs/models/gpt-6-astra
