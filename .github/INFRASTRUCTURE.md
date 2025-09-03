# SuperPassword Infrastructure

This document outlines the infrastructure and CI/CD setup for SuperPassword.

## Branch Strategy

We follow a modified GitFlow approach:

- `develop` is the main development branch
- Feature branches are created from `develop`
- `main` is protected and only receives changes through releases
- All work must go through PRs to `develop`
- Releases are created from `develop` to `main`

## CI/CD Pipelines

### Core Workflows

1. **CI Pipeline** (`ci.yml`)
   - Runs on PRs and pushes to develop
   - Validates code quality
   - Runs security checks
   - Creates development builds

2. **Security Pipeline** (`security.yml`)
   - Daily security scans
   - Dependency checks
   - Code analysis
   - Mobile security

3. **Release Pipeline** (`release.yml`)
   - Handles versioned releases
   - Creates production builds
   - Manages app store submissions

4. **Analytics Pipeline** (`analytics.yml`)
   - Weekly performance reports
   - Security metrics
   - Deployment statistics

### Branch Protection

#### develop

- Required status checks:
  - CI: validate
  - CI: security
  - CI: build
- Required reviews: 1
- Dismiss stale reviews
- No direct pushes

#### main

- All develop protections plus:
- Required reviews: 2
- Admin approval required
- No force push
- Required linear history
- Release workflow required

## Environments

### Staging

- Protected environment
- Single reviewer required
- 5-minute wait timer
- Deploys from develop

### Production

- Protected environment
- Two reviewers required
- 15-minute wait timer
- Admin approval required
- Deploys from main via release tags

## Security Features

### Code Security

- CodeQL analysis
- SAST scanning
- Secret scanning
- Mobile security framework

### Dependencies

- OWASP dependency check
- npm audit
- Snyk integration
- Dependency review

### Build Security

- SBOM generation
- Build provenance
- Artifact signing
- Cache security

## Monitoring

### Performance Metrics

- Build success rates
- Average duration
- Cache hit rates
- Resource usage

### Security Metrics

- Vulnerability trends
- Dependency alerts
- Secret scanning alerts
- Security review stats

### Deployment Metrics

- Success rates by environment
- Time to deployment
- Rollback frequency
- Environment stability

## Setup Instructions

1. **Branch Protection**

   ```bash
   export GITHUB_REPOSITORY="IgorGanapolsky/SuperPassword"
   ./.github/scripts/setup-branch-protection.sh
   ```

2. **Environments**
   - Create via GitHub UI
   - Use `.github/environments.yml` as reference
   - Configure protection rules
   - Set up required secrets

3. **Required Secrets**

   ```yaml
   # CI/CD
   EXPO_TOKEN: "Expo account token"
   EXPO_PUBLIC_SENTRY_DSN: "Sentry DSN"

   # iOS
   APPSTORE_PRIVATE_KEY: "App Store Connect API key"
   APPSTORE_KEY_ID: "Key ID"
   APPSTORE_ISSUER_ID: "Issuer ID"

   # Android
   GOOGLE_SERVICE_ACCOUNT_JSON: "Service account JSON"

   # Notifications
   SLACK_WEBHOOK_URL: "Slack webhook"

   # Security
   SNYK_TOKEN: "Snyk API token"
   ```

## Maintenance

### Weekly Tasks

- Review analytics reports
- Check security alerts
- Audit environment access
- Review cache usage

### Monthly Tasks

- Rotate access tokens
- Review protection rules
- Update action versions
- Audit permissions

### Quarterly Tasks

- Security policy review
- Performance optimization
- Infrastructure update
- Dependency strategy review
