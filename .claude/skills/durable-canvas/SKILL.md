---
name: durable-canvas
description: >
  Steal GitHub Copilot canvas method, not the Copilot app. Use when the user
  pastes threads.com/@github/post/Dc9agX7j_w4, mentions /create-canvas,
  chat scroll vs durable workflow, or agent canvases. Fail closed. Persist
  stages and drafts locally. No Copilot Pro.
---

# Durable canvas (steal the method)

GitHub 2026: chat is intent. Canvases make work visible, steerable, and
approvable. Blueprint: named states, surfaced decisions, persisted drafts,
explicit human gates.

Do **not** open the Copilot app. Do **not** run `/create-canvas`.

## Does it help?

| Surface | Use Copilot canvas? | Use instead |
| --- | --- | --- |
| Agent chat recap | No | `evaluate_source` source=`canvas` |
| "Where are we?" | No | `persist_canvas` stages + drafts |
| More canvas UX | No | Rank IAP / WQTU, not tokens |

## Before claiming a workflow state

```bash
python3 scripts/durable_canvas.py \
  --surface local_canvas \
  --canvas scripts/tests/fixtures/durable_canvas_iap.json \
  --source canvas \
  --cite stage:iap-attempt-path
```

Allow only when every JSON `ok` is true (process exit 0).
