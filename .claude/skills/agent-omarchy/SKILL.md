---
name: agent-omarchy
description: >
  Steal Try Omarchy pin+hash, idle release, lazy open, and loopback methods
  locally. Use when the user asks about Omarchy, try-omarchy, QEMU desktop
  packaging, or idle resource holds. Fail closed under the $20 cap.
---

# Agent Omarchy (steal the method)

Local harness only. Pin revisions with sha256. Release idle holds. Open on demand.
Loopback binds only. Do **not** install Try Omarchy / QEMU as product infra.

## Before claiming Omarchy-style controls

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

Allow only when every JSON `ok` is true (process exit 0).
