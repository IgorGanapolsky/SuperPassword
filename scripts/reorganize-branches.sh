#!/bin/bash

# Ensure we're in the repository root
cd "$(git rev-parse --show-toplevel)" || exit 1

# Fetch all branches
git fetch --all

# Create develop branch from main if it doesn't exist
if ! git show-ref --verify --quiet refs/heads/develop; then
  echo "Creating develop branch from main..."
  git checkout main
  git pull origin main
  git checkout -b develop
  git push origin develop
fi

# Consolidate chore branches into a single feature branch
echo "Consolidating chore branches..."
git checkout -b feat/workflow-improvements
git merge origin/chore/add-security-workflow origin/chore/consolidate-orchestration \
  origin/chore/enhance-pr-monitoring origin/chore/update-eas-workflow --no-commit

# If there are conflicts, abort and notify
if [ $? -ne 0 ]; then
  echo "Merge conflicts detected. Please resolve manually."
  git merge --abort
  exit 1
fi

git commit -m "feat(workflow): consolidate CI/CD improvements

- Add security workflow
- Consolidate orchestration
- Enhance PR monitoring
- Update EAS workflow"

# Push the new feature branch
git push origin feat/workflow-improvements

# Create pull request for workflow improvements
gh pr create \
  --base develop \
  --title "feat(workflow): consolidate CI/CD improvements" \
  --body "This PR consolidates various workflow improvements into a single feature.

Changes include:
- Add security workflow
- Consolidate orchestration
- Enhance PR monitoring
- Update EAS workflow

Part of the repository modernization effort." \
  --label enhancement

# Clean up old branches (only after successful PR creation)
if [ $? -eq 0 ]; then
  echo "Cleaning up old branches..."
  git push origin --delete chore/add-security-workflow
  git push origin --delete chore/consolidate-orchestration
  git push origin --delete chore/enhance-pr-monitoring
  git push origin --delete chore/update-eas-workflow
fi

echo "Branch reorganization complete!
Next steps:
1. Review and merge feat/workflow-improvements into develop
2. Set up branch protection rules in GitHub web interface
3. Update all existing PRs to target develop instead of main"
