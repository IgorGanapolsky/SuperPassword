#!/bin/bash

# Setup script for parallel Claude development using git worktrees
# Based on Anthropic's best practices: https://www.anthropic.com/engineering/claude-code-best-practices

set -e

REPO_ROOT=$(git rev-parse --show-toplevel)
WORKTREE_BASE="${REPO_ROOT}/../SuperPassword-worktrees"

echo "🚀 Setting up parallel Claude development environment"
echo "=================================================="

# Create worktree base directory if it doesn't exist
if [ ! -d "$WORKTREE_BASE" ]; then
    echo "📁 Creating worktree base directory: $WORKTREE_BASE"
    mkdir -p "$WORKTREE_BASE"
fi

# Function to create a worktree for a specific task
create_worktree() {
    local task_name=$1
    local branch_name=$2
    local worktree_path="${WORKTREE_BASE}/${task_name}"
    
    if [ -d "$worktree_path" ]; then
        echo "⚠️  Worktree already exists: $worktree_path"
        return 1
    fi
    
    echo "🌳 Creating worktree for task: $task_name"
    git worktree add "$worktree_path" -b "$branch_name" origin/develop
    echo "✅ Worktree created at: $worktree_path"
}

# Function to list all worktrees
list_worktrees() {
    echo ""
    echo "📋 Current worktrees:"
    echo "-------------------"
    git worktree list
}

# Function to prepare issue for Claude
prepare_issue_for_claude() {
    local issue_number=$1
    local worktree_name="issue-${issue_number}"
    local branch_name="claude/issue-${issue_number}"
    
    echo ""
    echo "🤖 Preparing issue #${issue_number} for Claude processing"
    
    # Create worktree for this issue
    create_worktree "$worktree_name" "$branch_name"
    
    # Label the issue as AI-ready
    echo "🏷️  Adding ai:ready label to issue #${issue_number}"
    gh issue edit "$issue_number" --add-label "ai:ready" 2>/dev/null || true
    
    # Create a Claude context file in the worktree
    local context_file="${WORKTREE_BASE}/${worktree_name}/.claude-context.md"
    cat > "$context_file" << EOF
# Claude Development Context

## Issue Details
Issue #${issue_number}

## Working Directory
${WORKTREE_BASE}/${worktree_name}

## Branch
${branch_name}

## Instructions for Claude
1. All work should be done in this worktree
2. Create atomic commits with clear messages
3. Push changes when complete
4. Open a PR when ready

## Commands
\`\`\`bash
cd ${WORKTREE_BASE}/${worktree_name}
git status
git add .
git commit -m "feat: implement issue #${issue_number}"
git push origin ${branch_name}
gh pr create --base develop --title "Fix: Issue #${issue_number}" --body "Implements #${issue_number}"
\`\`\`
EOF
    
    echo "✅ Context file created: $context_file"
}

# Main menu
echo ""
echo "What would you like to do?"
echo "1. Set up parallel worktrees for open PRs"
echo "2. Create worktree for specific issue"
echo "3. List all worktrees"
echo "4. Clean up completed worktrees"
echo "5. Full parallel setup (recommended)"

read -p "Enter choice (1-5): " choice

case $choice in
    1)
        echo "Setting up worktrees for open PRs..."
        for pr in $(gh pr list --state open --json number --jq '.[].number'); do
            branch=$(gh pr view $pr --json headRefName --jq '.headRefName')
            create_worktree "pr-${pr}" "$branch" || true
        done
        list_worktrees
        ;;
    2)
        read -p "Enter issue number: " issue_num
        prepare_issue_for_claude "$issue_num"
        ;;
    3)
        list_worktrees
        ;;
    4)
        echo "Cleaning up completed worktrees..."
        git worktree prune
        echo "✅ Cleanup complete"
        list_worktrees
        ;;
    5)
        echo "🎯 Full parallel setup initiated..."
        
        # Create worktrees for different parallel tasks
        echo ""
        echo "Creating standard parallel development worktrees..."
        
        # Feature development worktree
        create_worktree "feature-dev" "claude/feature-development" || true
        
        # Bug fixes worktree
        create_worktree "bug-fixes" "claude/bug-fixes" || true
        
        # Refactoring worktree
        create_worktree "refactoring" "claude/refactoring" || true
        
        # Testing worktree
        create_worktree "testing" "claude/testing" || true
        
        # Documentation worktree
        create_worktree "docs" "claude/documentation" || true
        
        # Label existing issues for AI processing
        echo ""
        echo "🏷️  Preparing issues for AI processing..."
        
        # Get open issues without AI labels
        for issue in $(gh issue list --state open --json number,labels --jq '.[] | select(.labels | map(.name) | contains(["ai:ready", "ai:in-progress"]) | not) | .number'); do
            echo "  - Adding ai:ready label to issue #${issue}"
            gh issue edit "$issue" --add-label "ai:ready" 2>/dev/null || true
        done
        
        list_worktrees
        
        echo ""
        echo "✨ Parallel Claude development environment ready!"
        echo ""
        echo "📚 Quick Guide:"
        echo "  - Each worktree is independent with its own working directory"
        echo "  - Multiple Claude sessions can work simultaneously"
        echo "  - No merge conflicts between parallel tasks"
        echo "  - Issues labeled 'ai:ready' will be picked up by the orchestrator"
        echo ""
        echo "🚀 Next steps:"
        echo "  1. The agent orchestrator will run every 2 hours (or trigger manually)"
        echo "  2. It will claim 'ai:ready' issues and work on them in parallel"
        echo "  3. Each Claude session works in its own worktree"
        echo "  4. PRs are created automatically when work completes"
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "🎉 Done!"
