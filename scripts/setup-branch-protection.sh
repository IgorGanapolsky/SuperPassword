#!/bin/bash

# Setup Branch Protection and Auto-Merge
# This script configures branch protection rules and enables auto-merge for the repository

set -e

REPO="IgorGanapolsky/SuperPassword"

echo "🔧 Configuring branch protection for $REPO..."

# Enable auto-merge for the repository
echo "📦 Enabling auto-merge for repository..."
gh api \
  --method PATCH \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  /repos/$REPO \
  -f allow_auto_merge=true \
  -f allow_squash_merge=true \
  -f allow_merge_commit=false \
  -f allow_rebase_merge=false \
  -f delete_branch_on_merge=true

echo "✅ Auto-merge enabled"

# Configure branch protection for main
echo "🛡️ Configuring protection for main branch..."
gh api \
  --method PUT \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  /repos/$REPO/branches/main/protection \
  -F required_status_checks='
  {
    "strict": true,
    "contexts": [
      "Test & Validate",
      "Claude Review",
      "CodeQL"
    ]
  }' \
  -F enforce_admins=false \
  -F required_pull_request_reviews='
  {
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": false,
    "required_approving_review_count": 1,
    "require_last_push_approval": false
  }' \
  -F restrictions=null \
  -F allow_force_pushes=false \
  -F allow_deletions=false \
  -F block_creations=true \
  -F required_conversation_resolution=true \
  -F lock_branch=false \
  -F allow_fork_syncing=false

echo "✅ Main branch protection configured"

# Configure branch protection for develop
echo "🛡️ Configuring protection for develop branch..."
gh api \
  --method PUT \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  /repos/$REPO/branches/develop/protection \
  -F required_status_checks='
  {
    "strict": false,
    "contexts": [
      "Test & Validate",
      "Claude Review"
    ]
  }' \
  -F enforce_admins=false \
  -F required_pull_request_reviews='
  {
    "dismiss_stale_reviews": false,
    "require_code_owner_reviews": false,
    "required_approving_review_count": 0
  }' \
  -F restrictions=null \
  -F allow_force_pushes=false \
  -F allow_deletions=false \
  -F block_creations=false \
  -F required_conversation_resolution=false \
  -F lock_branch=false \
  -F allow_fork_syncing=false

echo "✅ Develop branch protection configured"

# Create auto-merge labels
echo "🏷️ Creating auto-merge labels..."

# Create auto-merge label
gh label create "🚀 auto-merge" \
  --repo $REPO \
  --description "Automatically merge this PR when checks pass" \
  --color "0E8A16" \
  --force

# Create ready-to-merge label
gh label create "ready-to-merge" \
  --repo $REPO \
  --description "PR is ready to be merged" \
  --color "2EA043" \
  --force

# Create needs-review label
gh label create "needs-review" \
  --repo $REPO \
  --description "PR needs code review" \
  --color "FBCA04" \
  --force

echo "✅ Labels created"

echo "
🎉 Branch protection and auto-merge setup complete!

Next steps:
1. Add the '🚀 auto-merge' label to PRs you want to auto-merge
2. Ensure all required checks are passing
3. The auto-merge workflow will handle the rest

For critical/security PRs:
- These will NOT auto-merge even with the label
- Manual review and merge is required
"
