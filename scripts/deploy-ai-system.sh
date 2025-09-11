#!/bin/bash

# AI Agent Orchestration System Deployment Script
# SuperPassword - 2025 Best Practices Implementation
# Based on Anthropic Claude Code parallel execution patterns

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
WORKTREES_DIR="${REPO_ROOT}/../SuperPassword-agents"
CONFIG_FILE="${REPO_ROOT}/.ai-config.json"
GITHUB_REPO="$(git remote get-url origin | sed 's/.*github.com[:/]\(.*\)\.git/\1/')"

# Function definitions
log_info() { echo -e "${BLUE}ℹ️  ${NC}$1"; }
log_success() { echo -e "${GREEN}✅ ${NC}$1"; }
log_warning() { echo -e "${YELLOW}⚠️  ${NC}$1"; }
log_error() { echo -e "${RED}❌ ${NC}$1"; }
log_step() { echo -e "${MAGENTA}▶️  ${NC}$1"; }

# Header
clear
cat << 'HEADER'
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║     🤖 AI Agent Orchestration System Deployment                 ║
║         SuperPassword - Claude Code Parallel Execution          ║
║                      Version 1.0.0                              ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
HEADER

echo ""
echo "This script will deploy the complete AI agent orchestration system"
echo "for parallel Claude Code development using git worktrees."
echo ""

# Pre-flight checks
log_step "Running pre-flight checks..."

# Check git version
GIT_VERSION=$(git --version | awk '{print $3}')
log_info "Git version: $GIT_VERSION"

# Check GitHub CLI
if ! command -v gh &> /dev/null; then
    log_error "GitHub CLI (gh) is not installed"
    echo "Install from: https://cli.github.com/"
    exit 1
fi
log_info "GitHub CLI: $(gh --version | head -1)"

# Check jq
if ! command -v jq &> /dev/null; then
    log_error "jq is not installed"
    echo "Install: brew install jq (macOS) or apt install jq (Linux)"
    exit 1
fi
log_info "jq: $(jq --version)"

# Check authentication
if ! gh auth status &> /dev/null; then
    log_warning "Not authenticated with GitHub"
    echo "Running: gh auth login"
    gh auth login
fi
log_success "GitHub authentication verified"

echo ""
log_step "Phase 1: Environment Setup"
echo "══════════════════════════════════════"

# Create configuration
log_info "Creating AI configuration..."
cat > "$CONFIG_FILE" << EOF
{
  "version": "1.0.0",
  "deployment_date": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "repository": "$GITHUB_REPO",
  "worktrees_dir": "$WORKTREES_DIR",
  "settings": {
    "max_parallel_agents": 3,
    "agent_timeout_minutes": 30,
    "auto_label_issues": true,
    "kanban_sync_enabled": true,
    "priority_queue_enabled": true
  },
  "labels": {
    "ready": "ai:ready",
    "in_progress": "ai:in-progress",
    "review_needed": "ai:review-needed",
    "blocked": "ai:blocked",
    "completed": "ai:completed",
    "generated": "ai:generated"
  }
}
EOF
log_success "Configuration created: $CONFIG_FILE"

# Create required labels
log_info "Creating GitHub labels..."
for label in "ai:ready" "ai:in-progress" "ai:review-needed" "ai:blocked" "ai:completed" "ai:generated" "ai:system"; do
    gh label create "$label" --color "7057ff" --description "AI agent label" 2>/dev/null || \
    log_info "Label '$label' already exists"
done
log_success "Labels configured"

echo ""
log_step "Phase 2: Worktree Setup"
echo "══════════════════════════════════════"

# Setup worktrees directory
log_info "Setting up worktrees directory..."
mkdir -p "$WORKTREES_DIR"
log_success "Worktrees directory: $WORKTREES_DIR"

# Create initial worktrees for different agent types
log_info "Creating agent worktrees..."
AGENT_TYPES=("feature" "bugfix" "refactor" "docs" "test")
for agent_type in "${AGENT_TYPES[@]}"; do
    WORKTREE_PATH="$WORKTREES_DIR/agent-$agent_type"
    if [ ! -d "$WORKTREE_PATH" ]; then
        log_info "Creating worktree: agent-$agent_type"
        git worktree add "$WORKTREE_PATH" -b "agent/$agent_type" origin/develop 2>/dev/null || \
        git worktree add "$WORKTREE_PATH" "agent/$agent_type"
    else
        log_info "Worktree exists: agent-$agent_type"
    fi
done
log_success "Agent worktrees created"

echo ""
log_step "Phase 3: Workflow Deployment"
echo "══════════════════════════════════════"

# Check workflow files
WORKFLOWS=(
    "agent-orchestrator.yml"
    "agent-executor.yml"
    "agent-coordinator.yml"
    "kanban-sync-v2.yml"
)

log_info "Verifying workflow files..."
MISSING_WORKFLOWS=()
for workflow in "${WORKFLOWS[@]}"; do
    if [ ! -f "$REPO_ROOT/.github/workflows/$workflow" ]; then
        MISSING_WORKFLOWS+=("$workflow")
        log_warning "Missing workflow: $workflow"
    else
        log_info "Found: $workflow"
    fi
done

if [ ${#MISSING_WORKFLOWS[@]} -gt 0 ]; then
    log_error "Missing required workflows. Please ensure all workflows are committed."
    exit 1
fi
log_success "All workflows present"

echo ""
log_step "Phase 4: Secret Configuration"
echo "══════════════════════════════════════"

# Check for required secrets
log_info "Checking GitHub secrets..."
REQUIRED_SECRETS=("ANTHROPIC_API_KEY" "PROJECT_PAT")
MISSING_SECRETS=()

for secret in "${REQUIRED_SECRETS[@]}"; do
    if ! gh secret list | grep -q "^$secret"; then
        MISSING_SECRETS+=("$secret")
        log_warning "Missing secret: $secret"
    else
        log_info "Secret configured: $secret"
    fi
done

if [ ${#MISSING_SECRETS[@]} -gt 0 ]; then
    log_warning "Missing secrets detected. Would you like to configure them now? (y/n)"
    read -r response
    if [[ "$response" == "y" ]]; then
        for secret in "${MISSING_SECRETS[@]}"; do
            if [ "$secret" == "ANTHROPIC_API_KEY" ]; then
                echo "Enter your Anthropic API key (from https://console.anthropic.com/):"
                read -rs api_key
                echo "$api_key" | gh secret set ANTHROPIC_API_KEY
            elif [ "$secret" == "PROJECT_PAT" ]; then
                echo "Enter your GitHub Personal Access Token with project permissions:"
                read -rs pat
                echo "$pat" | gh secret set PROJECT_PAT
            fi
        done
        log_success "Secrets configured"
    else
        log_warning "Secrets not configured. Some features may not work."
    fi
fi

echo ""
log_step "Phase 5: Issue Preparation"
echo "══════════════════════════════════════"

# Label existing issues for AI processing
log_info "Preparing issues for AI processing..."
OPEN_ISSUES=$(gh issue list --state open --json number,labels --limit 100)
UNLABELED_COUNT=0

echo "$OPEN_ISSUES" | jq -r '.[] | select(.labels | map(.name) | contains(["ai:ready", "ai:in-progress", "ai:blocked"]) | not) | .number' | while read -r issue_num; do
    if [ -n "$issue_num" ]; then
        log_info "Labeling issue #$issue_num as ai:ready"
        gh issue edit "$issue_num" --add-label "ai:ready" 2>/dev/null || true
        ((UNLABELED_COUNT++))
    fi
done

log_success "Issues prepared for AI processing"

echo ""
log_step "Phase 6: System Activation"
echo "══════════════════════════════════════"

# Enable workflows
log_info "Enabling GitHub Actions workflows..."
for workflow in "${WORKFLOWS[@]}"; do
    gh workflow enable "$workflow" 2>/dev/null || true
done
log_success "Workflows enabled"

# Trigger initial sync
log_info "Triggering Kanban board sync..."
gh workflow run kanban-sync-v2.yml --field sync_all=true 2>/dev/null || \
log_warning "Could not trigger Kanban sync. Run manually if needed."

echo ""
log_step "Phase 7: Verification"
echo "══════════════════════════════════════"

# Run system check
log_info "Running system verification..."

# Check worktrees
WORKTREE_COUNT=$(git worktree list | grep -c "SuperPassword-agents" || echo "0")
log_info "Active worktrees: $WORKTREE_COUNT"

# Check issues
READY_ISSUES=$(gh issue list --label "ai:ready" --state open --json number | jq 'length')
log_info "Issues ready for processing: $READY_ISSUES"

# Check workflows
WORKFLOW_RUNS=$(gh run list --limit 5 --json name,status,conclusion)
log_info "Recent workflow activity:"
echo "$WORKFLOW_RUNS" | jq -r '.[] | "  - \(.name): \(.status) \(.conclusion)"' | head -5

echo ""
echo "════════════════════════════════════════════════════════════════"
log_success "🎉 AI Agent Orchestration System Deployed Successfully!"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "📊 System Status:"
echo "  • Worktrees created: $WORKTREE_COUNT"
echo "  • Issues ready: $READY_ISSUES"
echo "  • Max parallel agents: 3"
echo ""
echo "🚀 Quick Commands:"
echo ""
echo "  # Start AI agents manually"
echo "  gh workflow run agent-orchestrator.yml --field max_agents=2 --field dry_run=false"
echo ""
echo "  # Check agent status"
echo "  gh run list --workflow=agent-orchestrator.yml"
echo ""
echo "  # View Kanban board"
echo "  open https://github.com/users/IgorGanapolsky/projects/3/views/1"
echo ""
echo "  # Monitor agent activity"
echo "  gh issue list --label 'ai:in-progress'"
echo ""
echo "  # Add new issue to AI queue"
echo "  gh issue edit <issue-number> --add-label 'ai:ready'"
echo ""
echo "📚 Documentation:"
echo "  $REPO_ROOT/docs/ai-orchestration-architecture.md"
echo ""
echo "⏰ Scheduled Operations:"
echo "  • Agent Orchestrator: Every 2 hours (business hours)"
echo "  • Agent Coordinator: Every hour"
echo "  • Kanban Sync: On issue/PR events"
echo ""
log_info "The system is now active and will process issues automatically."
log_info "Agent workflows will run on schedule or can be triggered manually."
echo ""

# Save deployment record
DEPLOYMENT_RECORD="$REPO_ROOT/.ai-deployment-$(date +%Y%m%d-%H%M%S).log"
cat > "$DEPLOYMENT_RECORD" << EOF
AI Agent Orchestration System Deployment Log
============================================
Date: $(date)
User: $(whoami)
Repository: $GITHUB_REPO
Worktrees Directory: $WORKTREES_DIR
Worktree Count: $WORKTREE_COUNT
Ready Issues: $READY_ISSUES
Configuration: $CONFIG_FILE

Deployment completed successfully.
EOF

log_success "Deployment record saved: $DEPLOYMENT_RECORD"
echo ""
echo "Happy autonomous coding! 🤖"
