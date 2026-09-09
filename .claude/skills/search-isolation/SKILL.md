---
name: search-isolation
description: >
  Steal ArcticSwarm isolation-before-consensus, not the swarm. Use when the user
  pastes premature consensus, ArcticSwarm, or multi-agent research that chats
  too early. Fail closed. No more agents.
---

# Search isolation (steal the method)

Block peer reads during search. Gather findings first. Review before agreeing.
Do **not** spawn more agents. Do **not** install ArcticSwarm.

## Before claiming a research path

```bash
python3 scripts/search_isolation.py \
  --platform local_isolation \
  --paths scripts/tests/fixtures/search_isolation.json \
  --cite path:iap-attempt-path
```

Allow only when every JSON `ok` is true (process exit 0).
