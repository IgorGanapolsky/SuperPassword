# Issue Management System

This document explains how the automated issue management system works in this repository.

## Overview

The issue management system consists of several GitHub Actions workflows that automatically handle:

1. Triage of new issues
2. Status updates based on assignments
3. SLA monitoring
4. Project board synchronization

## Workflows

### Issue Management (`issue-management.yml`)

This is the main workflow that handles:

- **Triage of new issues**: Adds `status: triage` label and welcome comment
- **Status updates**: Updates labels when issues are assigned/unassigned
- **SLA monitoring**: Checks for SLA violations hourly and adds appropriate labels/comments

### Project Sync (`project-sync.yml`)

Handles synchronization with the project board:

- Moves issues between columns based on their state
- Tracks PRs through their lifecycle

### Project Kanban Management (`project-kanban.yml`)

Provides additional project board automation:

- Auto-adds high priority issues to the project
- Moves cards between columns based on events

## How It Works

### New Issues

When a new issue is created:
1. It automatically gets the `status: triage` label
2. A welcome comment is added with instructions
3. The issue is added to the "To Do" column of the project board

### Assignment

When an issue is assigned:
1. The `status: triage` label is removed
2. The `status: in-progress` label is added
3. The issue is moved to the "In Progress" column

When an issue is unassigned:
1. The `status: in-progress` label is removed
2. The `status: unassigned` label is added
3. The issue is moved back to the "To Do" column

### SLA Monitoring

The system checks hourly for SLA violations:
- High priority issues: 24 hours
- Medium priority issues: 72 hours
- Low priority issues: 168 hours (1 week)

When an SLA is violated:
1. The `sla: violated` label is added
2. A comment is added to notify the team

### Aging

Issues are automatically labeled based on their age:
- Fresh issues (less than 24 hours): `age: fresh`
- Stale issues (more than 24 hours): `age: stale`

## Configuration

The system is configured through:
- `.github/issue-management.yml`: Main configuration file
- `.github/project.yml`: Project board configuration
- `.github/project-views.yml`: Project views configuration

## Troubleshooting

If issues are not being updated:

1. Check that GitHub Actions are enabled for the repository
2. Verify that the required secrets are configured:
   - `PROJECT_PAT`: Personal Access Token with project permissions
3. Check the Actions tab for any workflow failures
4. Ensure the project board URL is correct in the workflows