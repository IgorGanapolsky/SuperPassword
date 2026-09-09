---
name: operator-capabilities
description: >
  Steal Astra operator patterns locally, not ChatGPT Pro. Use when the user asks
  how to use GPT-6 Astra, King Mode, computer use, or Codex-in-ChatGPT for max
  capabilities. Fail closed under the $20 cap.
---

# Operator capabilities (steal the method)

Reusable local CLIs. BrowserOS for screen control. Medium effort by default.
Do **not** buy ChatGPT Pro. Do **not** set `gpt-6-astra` as primary.

## Before claiming an Astra-style capability

```bash
python3 scripts/operator_capabilities.py \
  --platform local_operator \
  --capabilities scripts/tests/fixtures/operator_capabilities.json \
  --cite cap:iap-attempt-path
```

Allow only when every JSON `ok` is true (process exit 0).
