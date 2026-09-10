# Agent Omarchy (Try Omarchy-inspired, $0)

Adapted from [try-omarchy](https://github.com/omacom/try-omarchy) / upstream [Omarchy](https://github.com/basecamp/omarchy). Steal the **method**, not a QEMU Arch desktop as Random-Timer product infra.

| Omarchy construct | Random-Timer control plane |
| --- | --- |
| Pinned revision + strict sha256 provenance | `evaluate_pin` |
| Idle release (no forever-open audio/device) | `evaluate_idle` |
| Open capture only on demand | `evaluate_lazy_open` |
| Clear dirty flag / no unconditional refresh | `evaluate_dirty_loop` |
| Loopback-only port forwards | `evaluate_forward` |
| One shared folder | `evaluate_share` |
| Typed confirmation before Reset | `evaluate_reset` |
| Local harness cite | `--cite omarchy:<id>` |

## What we deliberately did *not* copy

- Shipping Try Omarchy / QEMU / Arch guest as a dependency of the timer app.
- Treating idle CPU or GitHub stars as North Star proxies.
- Public `0.0.0.0` binds or multi-folder shared surfaces.

## Fail-closed CLI

```bash
python3 scripts/agent_omarchy.py \
  --platform local_omarchy_harness \
  --controls scripts/tests/fixtures/agent_omarchy.json \
  --cite omarchy:pin-hash-idle \
  --revision c3d48b7d \
  --sha256 aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa \
  --bind 127.0.0.1 \
  --idle 1 \
  --held-open 0 \
  --dirty 1 \
  --refreshed 1
```

Allow only when every JSON `ok` is true (process exit 0). Incomplete inputs exit 2.

## Live evidence (project 299775, trailing 7d, 2026-09-10)

WQTU `5`. Ranker puts IAP attempt path ahead of idle-CPU vanity from the Omarchy README.

`paywall_purchase_success` is telemetry, not ledger revenue.

## Source

- https://github.com/omacom/try-omarchy
- https://github.com/basecamp/omarchy
