#!/bin/bash

# This script sets up branch protection rules using the GitHub CLI
# Required environment variables:
# - GITHUB_TOKEN with admin:repo scope

# Function to check if GitHub CLI is installed
check_gh() {
  if ! command -v gh &> /dev/null; then
    echo "GitHub CLI (gh) is not installed. Please install it first."
    exit 1
  fi
}

# Function to check if logged in to GitHub CLI
check_auth() {
  if ! gh auth status &> /dev/null; then
    echo "Not logged in to GitHub CLI. Please run 'gh auth login' first."
    exit 1
  fi
}

# Set up develop branch protection
setup_develop_protection() {
  echo "Setting up develop branch protection..."
  gh api \
    --method PUT \
    "/repos/$GITHUB_REPOSITORY/branches/develop/protection" \
    -f required_status_checks='{"strict":true,"contexts":["validate","security","build"]}' \
    -f enforce_admins=true \
    -f required_pull_request_reviews='{"required_approving_review_count":1,"dismiss_stale_reviews":true}' \
    -f restrictions=null
}

# Set up main branch protection
setup_main_protection() {
  echo "Setting up main branch protection..."
  gh api \
    --method PUT \
    "/repos/$GITHUB_REPOSITORY/branches/main/protection" \
    -f required_status_checks='{"strict":true,"contexts":["validate","security","build","release"]}' \
    -f enforce_admins=true \
    -f required_pull_request_reviews='{"required_approving_review_count":2,"dismiss_stale_reviews":true,"require_code_owner_reviews":true}' \
    -f restrictions='{"users":[],"teams":[],"apps":[]}' \
    -f required_linear_history=true \
    -f allow_force_pushes=false \
    -f allow_deletions=false
}

# Main execution
main() {
  check_gh
  check_auth
  
  echo "Setting up branch protection rules for $GITHUB_REPOSITORY"
  
  # Create or update branch protection rules
  setup_develop_protection
  setup_main_protection
  
  echo "Branch protection rules set up successfully!"
}

main "$@"
