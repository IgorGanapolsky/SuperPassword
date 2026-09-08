---
name: token-shunt
description: >
  Steal Spotify Portal/shunt token routing, not Portal or Gemini Flash. Use when
  the user pastes dani_avila7, mentions 90% Claude token cut, PreToolUse large
  file intercepts, or bulk-reader delegation. Fail closed. No Portal plugin.
---

# Token shunt (steal the method)

Spotify 2026-09: most coding-agent tokens are I/O. PreToolUse blocks untargeted
Read above 350 lines. Targeted offset/limit passes. Return a slice to the
frontier model. Do not delegate debug or architecture to a cheap worker.

Do **not** install `shunt@portal`. Do **not** add Gemini Flash as a worker.
Do **not** delegate editing or reasoning to a cheap worker.

## Does it help?

| Surface | Use Portal? | Use instead |
| --- | --- | --- |
| Whole-file Read of 800 lines | No | Cursor `preToolUse` rewrites to `limit=80` |
| Bare `cat` of a large file | No | `beforeShellExecution` denies; pipe to grep |
| Dump the file back into chat | No | `evaluate_context_return` |
| Tests/config/boilerplate | No | `local_slice`, not Flash |
| Thread-safety / architecture | No | `hermes-main` only |

## Before claiming tokens were shunted

```bash
python3 scripts/token_shunt.py \
  --lines 800 --targeted \
  --task-kind reasoning --model hermes-main \
  --source-lines 800 --returned-lines 40
```

Allow only when every JSON `ok` is true (process exit 0).
