---
name: skill-hygiene
description: >
  Steal pvncher skill/prompt hygiene, not GPT-6 Astra. Use when the user pastes
  the Astra skills article, mentions bloated skills, AGENTS.md bloat, or pick-me
  descriptions. Fail closed. No OpenAI-as-primary.
---

# Skill hygiene (steal the method)

Short descriptions. Progressive disclosure. Lean always-on docs. Define
completion before starting.

Do **not** switch to GPT-6 Astra. Do **not** download more skills.

## Before claiming a skill is the pick

```bash
python3 scripts/skill_hygiene.py \
  --platform local_hygiene \
  --skills scripts/tests/fixtures/skill_hygiene.json \
  --cite skill:iap-attempt-path
```

Allow only when every JSON `ok` is true (process exit 0).
