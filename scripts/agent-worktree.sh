#!/bin/bash

# Agent Worktree Manager for Claude Autonomous Agents
# Based on Anthropic's best practices for parallel agentic coding
# https://www.anthropic.com/engineering/claude-code-best-practices

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
WORKTREES_BASE="${PROJECT_ROOT}/../SuperPassword-agents"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Ensure worktrees base directory exists
ensure_worktrees_dir() {
    if [ ! -d "$WORKTREES_BASE" ]; then
        log_info "Creating worktrees base directory: $WORKTREES_BASE"
        mkdir -p "$WORKTREES_BASE"
    fi
}

# Create a new worktree for an agent task
create_worktree() {
    local task_id="$1"
    local branch_name="${2:-agent/task-$task_id}"
    local worktree_path="$WORKTREES_BASE/$task_id"
    
    ensure_worktrees_dir
    
    if [ -d "$worktree_path" ]; then
        log_warning "Worktree already exists: $worktree_path"
        return 1
    fi
    
    log_info "Creating worktree for task $task_id..."
    
    # Create new branch from develop
    git worktree add -b "$branch_name" "$worktree_path" origin/develop
    
    log_success "Worktree created at: $worktree_path"
    echo "$worktree_path"
}

# List all active worktrees
list_worktrees() {
    log_info "Active agent worktrees:"
    git worktree list | grep -E "SuperPassword-agents" || echo "No agent worktrees found"
}

# Remove a worktree
remove_worktree() {
    local task_id="$1"
    local worktree_path="$WORKTREES_BASE/$task_id"
    
    if [ ! -d "$worktree_path" ]; then
        log_error "Worktree not found: $worktree_path"
        return 1
    fi
    
    log_info "Removing worktree for task $task_id..."
    git worktree remove "$worktree_path" --force
    
    # Clean up the branch if it exists
    local branch_name="agent/task-$task_id"
    if git show-ref --verify --quiet "refs/heads/$branch_name"; then
        git branch -D "$branch_name" 2>/dev/null || true
    fi
    
    log_success "Worktree removed: $worktree_path"
}

# Clean up all agent worktrees
cleanup_all() {
    log_info "Cleaning up all agent worktrees..."
    
    if [ -d "$WORKTREES_BASE" ]; then
        for worktree in "$WORKTREES_BASE"/*; do
            if [ -d "$worktree" ]; then
                local task_id=$(basename "$worktree")
                remove_worktree "$task_id"
            fi
        done
    fi
    
    git worktree prune
    log_success "All agent worktrees cleaned up"
}

# Get status of a worktree
status_worktree() {
    local task_id="$1"
    local worktree_path="$WORKTREES_BASE/$task_id"
    
    if [ ! -d "$worktree_path" ]; then
        log_error "Worktree not found: $worktree_path"
        return 1
    fi
    
    log_info "Status of worktree $task_id:"
    cd "$worktree_path"
    git status --short
    cd - > /dev/null
}

# Main command handler
main() {
    local command="${1:-help}"
    
    case "$command" in
        create)
            if [ $# -lt 2 ]; then
                log_error "Usage: $0 create <task_id> [branch_name]"
                exit 1
            fi
            create_worktree "${2}" "${3:-}"
            ;;
        list)
            list_worktrees
            ;;
        remove)
            if [ $# -lt 2 ]; then
                log_error "Usage: $0 remove <task_id>"
                exit 1
            fi
            remove_worktree "${2}"
            ;;
        status)
            if [ $# -lt 2 ]; then
                log_error "Usage: $0 status <task_id>"
                exit 1
            fi
            status_worktree "${2}"
            ;;
        cleanup)
            cleanup_all
            ;;
        help|*)
            cat << EOF
Agent Worktree Manager - Manage Git worktrees for Claude autonomous agents

Usage: $0 <command> [arguments]

Commands:
    create <task_id> [branch]  Create a new worktree for a task
    list                       List all active agent worktrees
    remove <task_id>          Remove a specific worktree
    status <task_id>          Show status of a worktree
    cleanup                   Remove all agent worktrees
    help                      Show this help message

Examples:
    $0 create issue-127       # Create worktree for issue #127
    $0 list                   # List all worktrees
    $0 status issue-127       # Check status of worktree
    $0 remove issue-127       # Remove worktree when done

Based on Anthropic's Claude Code best practices for parallel execution.
EOF
            ;;
    esac
}

main "$@"
