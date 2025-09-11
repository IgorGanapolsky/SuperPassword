# GitHub Actions Workflow Guidelines

## 🚨 CRITICAL: Preventing Billing Issues

### 1. **Set Spending Limit to $0**
Go to https://github.com/settings/billing/spending_limits and set Actions limit to $0

### 2. **Never Create Workflow Loops**
- ❌ NEVER have workflows trigger each other
- ❌ NEVER trigger on `issues` events in main CI workflows  
- ❌ NEVER trigger on events that the workflow itself creates

### 3. **Required Safety Features**

Every workflow MUST have:

```yaml
# 1. Concurrency control
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

# 2. Timeout limits
timeout-minutes: 15  # or appropriate for job

# 3. Bot protection
if: github.actor != 'github-actions[bot]'
```

### 4. **Schedule Frequency Limits**

| Type | Maximum Frequency | Example |
|------|------------------|---------|
| CI/CD | On push/PR only | No schedule |
| Monitoring | Daily | `0 0 * * *` |
| Cleanup | Weekly | `0 0 * * 1` |
| Reports | Monthly | `0 0 1 * *` |

❌ **NEVER** use schedules more frequent than hourly
❌ **NEVER** use `*/15` or `*/30` minute schedules

### 5. **Workflow Triggers**

Safe triggers:
```yaml
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]
  workflow_dispatch:  # Manual only
```

Dangerous triggers (use with extreme caution):
```yaml
on:
  issues:  # Can cause loops
  issue_comment:  # Can cause loops
  schedule:  # Can be expensive
```

### 6. **Resource Limits**

- Max parallel jobs: 5
- Max job duration: 30 minutes
- Max workflow runs per day: 50
- Max matrix size: 10

### 7. **Monitoring**

Run the workflow monitor regularly:
```bash
gh workflow run workflow-monitor.yml
```

Check your usage:
```bash
gh api /repos/$(gh repo view --json nameWithOwner -q .nameWithOwner)/actions/runs \
  --jq '[.workflow_runs[] | select(.created_at > (now - 86400 | todate))] | length'
```

### 8. **Emergency Stop**

If workflows are running out of control:

```bash
# Cancel all running workflows
gh run list --status in_progress --json databaseId \
  --jq '.[].databaseId' | xargs -I {} gh run cancel {}

# Disable all workflows
for workflow in .github/workflows/*.yml; do
  gh workflow disable "$(basename $workflow)"
done
```

## Example Safe Workflow

```yaml
name: Safe CI
on:
  push:
    branches: [main, develop]
    paths-ignore:
      - '**.md'
      - '.github/workflows/**'
  pull_request:
  workflow_dispatch:

concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true

jobs:
  build:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    if: github.actor != 'github-actions[bot]'
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npm test
```

## Checklist for New Workflows

- [ ] Has concurrency group
- [ ] Has timeout-minutes
- [ ] Checks for bot actor
- [ ] No issue/comment triggers
- [ ] Schedule is daily or less frequent
- [ ] Tested locally with `act`
- [ ] Resource usage estimated
- [ ] Added to workflow monitor
