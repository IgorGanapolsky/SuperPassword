# Agent datapack (Meko-inspired, $0)

Adapted from [Meko](https://mekodata.ai/) / [docs](https://docs.mekodata.ai/). Steal the **method**, not [cloud.mekodata.ai](https://cloud.mekodata.ai/signup) signup, `mcp.mekodata.ai`, or hosted Yugabyte.

Meko’s useful pattern is a **datapack**: one isolation unit for memory, knowledge, conversations, and decision traces, with promote-only-when-verified and recall-before-reprocess. We keep that as local JSON under the **$20/month** hard cap.

| Meko construct | Random-Timer control plane |
| --- | --- |
| Datapack | `evaluate_platform` → `local_datapack` |
| Memory / knowledge / traces | `evaluate_layer` + local JSON storage |
| Promote learnings → knowledge | `evaluate_promote` (verified only) |
| Query before re-burning tokens | `evaluate_recall` |
| Decision cite | `--cite pack:<id>` |

## What we deliberately did *not* copy

- Signup at cloud.mekodata.ai / remote MCP endpoint.
- Hosted mem0 + Yugabyte as a paid data plane.
- “15x fewer tokens” as a North Star proxy (tokens are not WQTU / IAP).
- Treating unverified chat memory as shared truth.

## Fail-closed CLI

```bash
python3 scripts/agent_datapack.py \
  --platform local_datapack \
  --packs scripts/tests/fixtures/agent_datapack.json \
  --cite pack:iap-attempt-path \
  --queried-local 1
```

Allow only when every JSON `ok` is true (process exit 0). Incomplete inputs exit 2.

## Live evidence (project 299775, trailing 7d, 2026-09-09)

WQTU `5`. `timer_started` 370/53. `timer_completed` 84/21. `paywall_viewed` 20/10. `paywall_view` 12/6. `paywall_dismissed` 9/5. Zero IAP attempts. Ranker puts the attempt path ahead of Meko token-savings claims.

`paywall_purchase_success` is telemetry, not ledger revenue.

## Source

- https://mekodata.ai/
- https://docs.mekodata.ai/
- https://cloud.mekodata.ai/signup
