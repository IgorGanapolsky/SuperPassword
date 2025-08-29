#!/bin/bash
set -e

# Branches to preserve
PROTECTED_BRANCHES=("main" "develop" "feat/add-web-support" "fix/dependency-compatibility")

# Function to check if branch is protected
is_protected() {
  local branch=$1
  for protected in "${PROTECTED_BRANCHES[@]}"; do
    [[ $branch == $protected ]] && return 0
  done
  return 1
}

# Sync with remote
git fetch --prune

# Get list of merged branches
echo "🔍 Analyzing branches..."
for branch in $(git branch -r | grep 'origin/' | sed 's/origin\///'); do
  # Skip protected branches
  if is_protected "$branch"; then
    echo "⏩ Skipping protected branch: $branch"
    continue
  fi

  # Check if branch is merged
  if git branch -r --merged origin/develop | grep -q "origin/$branch"; then
    echo "🗑️  Deleting merged branch: $branch"
    git push origin --delete "$branch"
  fi
done

echo "✨ Branch cleanup complete!"
echo "
Remaining branches:"
git branch -r | grep 'origin/' | sed 's/origin\///'

