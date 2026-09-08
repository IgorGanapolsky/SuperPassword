---
name: infoq-agent-control-plane
description: >
  Steal InfoQ Sep 8 2026 control-plane methods, not the webinar or paid SaaS.
  Use when the user pastes an InfoQ newsletter, mentions Gisting, KYAML,
  Copilot Review billing, Foundry/HCP control planes, Airbnb auth, DoorDash
  Flux, or Workload Identity. Fail closed. No Harness/Ori/Copilot-review spend.
---

# InfoQ agent control plane (steal the method)

InfoQ 2026-09-08: agents can open PRs, but production still needs tests, security,
approvals, and rollback. Shopify Gisting, context engineering, billed Copilot
review, Foundry/HCP routers, Workload Identity, and "skip peer review on low-risk
PRs" are the transferable bits.

Do **not** attend the Harness webinar as the deliverable. Do **not** buy Moderne,
Tiger Data, Copilot Code Review, Ori, or Foundry Model Router.

## Does it help?

| Surface | Use the paid product? | Use instead |
| --- | --- | --- |
| Hermes Desktop routing | No Foundry/OpenRouter primary | `hermes_desktop_router_policy.py` + this SPOF check |
| Context dumps / Gisting | No Redis/Shopify tokens | `gist_context` keeps in/out + two ACs |
| Copilot review (billed, 2d lag) | Never | Existing CI Claude review |
| Native Android/iOS diffs | No AI-only merge | `require_device_e2e` |
| Scripts/skills-only diffs | Yes, AI approve after tests | `allow_ai_approve` |
| GCP SA JSON in repo | Never | GitHub OIDC |

## Before claiming a delivery path is allowed

```bash
python3 scripts/infoq_agent_control_plane.py \
  --primary-model hermes-main \
  --fallbacks nous-deepseek,glm-5.3 \
  --in-scope 'pin Desktop tool turns' \
  --out-scope 'ori login' \
  --acs 'tests pass|CLI fail-closed' \
  --service local_pytest \
  --paths 'scripts/infoq_agent_control_plane.py,scripts/tests/test_infoq_agent_control_plane.py' \
  --credential github_oidc
```

Allow only when every JSON `ok` is true (process exit 0).

## High-ROI only

- Independent fallbacks (not the same model, not 3B).
- Compress context to in/out + two ACs. Drop newsletter dumps.
- Block billed-per-review and metered model routers.
- Scripts-only PRs may use existing CI AI review; native diffs need device evidence.
- Prefer OIDC over long-lived keys.
