#!/bin/bash

# SuperPassword Project Status Updater
# This script manually updates issue #81 with current project statistics

set -e

echo "🔄 Updating SuperPassword Project Status..."

# Get current stats
OPEN_ISSUES=$(gh api repos/IgorGanapolsky/SuperPassword/issues --method GET --field state=open --field per_page=100 --jq '[.[] | select(has("pull_request") | not) | select(.number != 81)] | length')
OPEN_PRS=$(gh api repos/IgorGanapolsky/SuperPassword/pulls --method GET --field state=open --field per_page=100 --jq 'length')

# Calculate progress metrics
ASSIGNED_ISSUES=$(gh api repos/IgorGanapolsky/SuperPassword/issues --method GET --field state=open --field per_page=100 --jq '[.[] | select(has("pull_request") | not) | select(.number != 81) | select(.assignees | length > 0)] | length')

# Count by labels
BUGS=$(gh api repos/IgorGanapolsky/SuperPassword/issues --method GET --field state=open --field per_page=100 --jq '[.[] | select(has("pull_request") | not) | select(.number != 81) | select(.labels[]?.name | test("bug"))] | length')
FEATURES=$(gh api repos/IgorGanapolsky/SuperPassword/issues --method GET --field state=open --field per_page=100 --jq '[.[] | select(has("pull_request") | not) | select(.number != 81) | select(.labels[]?.name | test("enhancement|feature"))] | length')

# Calculate percentages
if [ "$OPEN_ISSUES" -gt 0 ]; then
    PROGRESS_RATE=$(( (ASSIGNED_ISSUES * 100) / OPEN_ISSUES ))
else
    PROGRESS_RATE=0
fi

# Generate status indicators
if [ "$OPEN_ISSUES" -gt 10 ]; then
    ISSUE_STATUS="🔴 High"
elif [ "$OPEN_ISSUES" -gt 5 ]; then
    ISSUE_STATUS="🟡 Medium"
else
    ISSUE_STATUS="🟢 Good"
fi

if [ "$OPEN_PRS" -gt 5 ]; then
    PR_STATUS="🔴 High"
elif [ "$OPEN_PRS" -gt 2 ]; then
    PR_STATUS="🟡 Medium"
else
    PR_STATUS="🟢 Good"
fi

if [ "$BUGS" -gt 5 ]; then
    BUG_STATUS="🔴 Critical"
elif [ "$BUGS" -gt 2 ]; then
    BUG_STATUS="🟡 Moderate"
else
    BUG_STATUS="🟢 Low"
fi

if [ "$PROGRESS_RATE" -ge 40 ]; then
    PROGRESS_HEALTH="🟢 Good"
elif [ "$PROGRESS_RATE" -ge 20 ]; then
    PROGRESS_HEALTH="🟡 Fair"
else
    PROGRESS_HEALTH="🔴 Needs Attention"
fi

# Generate recommendations
RECOMMENDATIONS=""
if [ "$OPEN_ISSUES" -gt 15 ]; then
    RECOMMENDATIONS="${RECOMMENDATIONS}⚠️ **High Issue Count**: Consider prioritizing issue resolution\n"
fi
if [ "$BUGS" -gt 5 ]; then
    RECOMMENDATIONS="${RECOMMENDATIONS}🐛 **Bug Alert**: Multiple bugs detected - prioritize bug fixes\n"
fi
if [ "$PROGRESS_RATE" -lt 30 ]; then
    RECOMMENDATIONS="${RECOMMENDATIONS}📈 **Low Progress Rate**: Consider assigning more issues to active development\n"
fi
if [ "$OPEN_ISSUES" -le 5 ] && [ "$BUGS" -le 2 ]; then
    RECOMMENDATIONS="${RECOMMENDATIONS}✅ **Healthy Project**: Good balance of issues and activity\n"
fi

# Generate the status update
STATUS_BODY="# 📊 SuperPassword Project Status

*Last updated: $(date '+%B %d, %Y at %I:%M %p %Z')*

## 📈 Current Metrics

| Metric | Count | Status |
|--------|-------|--------|
| 📋 Open Issues | ${OPEN_ISSUES} | ${ISSUE_STATUS} |
| 🔧 Open PRs | ${OPEN_PRS} | ${PR_STATUS} |
| 🏃 In Progress | ${ASSIGNED_ISSUES} | ${PROGRESS_RATE}% of issues |
| 🐛 Bugs | ${BUGS} | ${BUG_STATUS} |
| ✨ Features | ${FEATURES} | ${FEATURES} planned |

## 🎯 Health Dashboard

### Progress Health: ${PROGRESS_HEALTH}
- **Work in Progress**: ${PROGRESS_RATE}% of issues are actively assigned
- **Velocity**: $((ASSIGNED_ISSUES + OPEN_PRS)) items in active development

## 📋 Issue Breakdown

\`\`\`
📊 Distribution:
├── 🐛 Bugs: ${BUGS}
├── ✨ Features: ${FEATURES}
└── 📝 Other: $((OPEN_ISSUES - BUGS - FEATURES))
\`\`\`

## 🎯 Recommendations

${RECOMMENDATIONS}

## 🔄 Automation Status

- ✅ Auto-labeling active
- ✅ Project board sync enabled
- ✅ Status updates every hour
- ⚡ Manual updates available

---

*This status is automatically updated by GitHub Actions. Last manual update: $(date -Iseconds)*"

# Update the issue
echo "📝 Updating issue #81..."
gh issue edit 81 --body "$STATUS_BODY" --repo IgorGanapolsky/SuperPassword

echo "✅ Project status updated successfully!"
echo "📊 Stats: $OPEN_ISSUES issues, $OPEN_PRS PRs, $ASSIGNED_ISSUES in progress"
echo "🌐 View: https://github.com/IgorGanapolsky/SuperPassword/issues/81"
