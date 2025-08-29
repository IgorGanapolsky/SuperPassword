# Development Workflow

## Overview

This document describes the development workflow for SuperPassword, outlining our processes, tools, and standards for 2025.

## Branch Strategy

### Main Branches

- `main`: Production code, always stable
- `develop`: Integration branch for features

### Feature Development

1. Create feature branch from `develop`:

   ```bash
   git checkout develop
   git pull
   git checkout -b feat/your-feature-name
   ```

2. Commit using conventional commits:

   ```bash
   git commit -m "feat: add new feature"
   git commit -m "fix: resolve bug"
   git commit -m "chore: update dependencies"
   ```

3. Push and create PR:
   ```bash
   git push -u origin feat/your-feature-name
   gh pr create --base develop
   ```

## Development Standards

### Code Quality

- TypeScript for type safety
- ESLint for code quality
- Prettier for formatting
- Jest for testing

### CI/CD Pipeline

All PRs must pass:

- Type checking
- Linting
- Tests
- Security scans
- Build validation

### Security Standards

- All dependencies must be up-to-date
- Security vulnerabilities must be addressed
- Secrets must be properly managed
- Code must be scanned for sensitive data

## Project Organization

### Issue Types

- 🐛 Bug: Something isn't working
- ✨ Feature: New functionality
- 📝 Documentation: Documentation updates
- 🔒 Security: Security-related changes
- ⚡ Performance: Performance improvements
- 🧹 Chore: Maintenance tasks

### PR Process

1. Create branch from `develop`
2. Implement changes
3. Run tests locally
4. Create PR with description
5. Wait for CI checks
6. Get code review
7. Address feedback
8. Merge when approved

### Release Process

1. Merge features into `develop`
2. Create release branch
3. Run final tests
4. Create PR to `main`
5. Deploy to production
6. Tag release

## Tools & Automation

### Development Tools

- VS Code for development
- GitHub for source control
- GitHub Actions for CI/CD
- Sentry for monitoring
- EAS for mobile builds

### Automation

- PR assignments
- Issue tracking
- Dependency updates
- Security scanning
- Release notes

## Project Board Structure

### Columns

1. 📋 Backlog
   - Upcoming work
   - Not yet prioritized

2. 🎯 Ready
   - Prioritized
   - Ready for development

3. 🏃‍♂️ In Progress
   - Currently being worked on
   - Assigned to developer

4. 👀 In Review
   - PR created
   - Waiting for review

5. ✅ Done
   - Work completed
   - Merged to develop

### Automation Rules

- New issues → Backlog
- PR opened → In Progress
- PR ready for review → In Review
- PR merged → Done

## Support & Documentation

### Key Resources

- `README.md`: Project overview
- `CONTRIBUTING.md`: Contribution guide
- `WORKFLOW.md`: This document
- `SECURITY.md`: Security policy

### Getting Help

- Check existing documentation
- Search closed issues
- Ask in team chat
- Create new issue
