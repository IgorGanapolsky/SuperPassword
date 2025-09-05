# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Repository Overview

SuperPassword is a mobile password management application built with React Native and Expo. The repository is **production-ready** with comprehensive features implemented.

Status: ✅ **COMPLETED**

- ✅ Core application fully implemented
- ✅ CI/CD pipeline active and functional
- ✅ Full feature set with premium monetization
- ✅ Automated project status tracking (Issue #81)
- ✅ Professional UI/UX with Material Design
- ✅ Complete testing infrastructure

## Repository Configuration

### Branch Management

```bash path=null start=null
# Create new feature branch
git checkout develop
git checkout -b feature/your-feature-name

# Update feature branch with develop
git checkout feature/your-feature-name
git pull origin develop
```

Branch Rules:

- Base all work on `develop` branch
- Main branch protection requires:
  - Passing CI checks (currently being configured in PR #76)
  - Code review approval
  - Password/admin approval for merges

## Project Architecture ✅

The application follows a feature-based architecture with React Native best practices:

```text path=null start=null
/src
├── components/     # Reusable UI components ✅ IMPLEMENTED
├── contexts/       # React Context providers ✅ IMPLEMENTED
├── hooks/         # Custom React hooks ✅ IMPLEMENTED
├── navigation/    # Navigation configuration ✅ IMPLEMENTED
├── screens/       # Feature-specific screens ✅ IMPLEMENTED
├── services/      # Business logic layer ✅ IMPLEMENTED
├── types/         # TypeScript definitions ✅ IMPLEMENTED
└── utils/         # Helper utilities ✅ IMPLEMENTED

/.github          # GitHub Actions and automation ✅ ACTIVE
/.eas             # Expo Application Services config ✅ CONFIGURED
/.husky           # Git hooks for code quality ✅ ACTIVE
/.trunk           # Trunk-based development config ✅ CONFIGURED
/assets           # Static assets and resources ✅ POPULATED
/store-listings   # App store metadata ✅ READY
```

### Current Implementation Status

**Core Features:**

- 🔐 Advanced password generation with strength analysis
- 📱 Professional Material Design UI with dark mode
- 📜 Password history management (10 free, unlimited premium)
- 🎯 Premium features with freemium monetization model
- 📋 One-tap clipboard copy with haptic feedback
- 🌓 Complete theme system with gradient backgrounds

**Technical Stack:**

- React Native 0.79.5 with Expo SDK 53
- TypeScript 5.x with comprehensive type safety
- React Navigation 7.x with bottom tabs
- React Native Paper for Material Design
- AsyncStorage for local persistence
- Sentry for error monitoring

### Technology Stack

Core technologies being set up:

- React Native with Expo SDK
- TypeScript for type safety
- EAS for build and deployment
- GitHub Actions for CI/CD

### Security Architecture

Security features to be implemented:

- End-to-end encryption for password data
- Secure key storage using platform KeyStore/Keychain
- Zero-knowledge architecture
- Biometric authentication integration

## Development Setup

Note: Package manager and build configurations are pending. The following commands will be available after initial setup:

### Environment Setup

```bash path=null start=null
# Install dependencies (pending package.json)
npm install  # or yarn/pnpm based on final setup

# Install development tools
npm install --global eas-cli
```

### Local Development

```bash path=null start=null
# Start development server (command pending)
npm start    # exact command TBD

# Run on simulators (commands pending)
npm run ios
npm run android
```

### Testing

Test framework selection pending. Commands will be standardized as:

```bash path=null start=null
# Run all tests
npm test

# Run specific test
npm test -- path/to/test
```

### EAS Build

```bash path=null start=null
# Configure EAS (first time)
eas configure

# Build for development (requires eas.json)
eas build --profile development --platform all

# Build for production
eas build --profile production --platform all
```

## CI/CD Pipeline

We use consolidated and modular workflows under `.github/workflows/`:

- Validate: TypeScript, ESLint, tests, SonarCloud, Codecov
- Security: OWASP Dependency-Check (SARIF), Snyk (optional), CodeQL
- Build: EAS build validation on protected branches
- Project automation: Issue triage, project board sync, and status updates

Workflow locations:

- Core CI: `.github/workflows/ci.yml` ✅
- Security: `.github/workflows/security.yml` ✅
- Release: `.github/workflows/release.yml` ✅
- Issue automation: `.github/workflows/issue-automation.yml` ✅
- Project automation: `.github/workflows/project-automation.yml` ✅
- Project status sync: `.github/workflows/project-sync.yml` ✅

## Getting Started

1. Clone and setup:

```bash path=null start=null
git clone {{REPO_URL}}
cd SuperPassword
git checkout develop
npm install
```

2. Start development:

```bash path=null start=null
npm run start
```

3. Run tests and lint:

```bash path=null start=null
npm test
npm run lint
```

4. Update project status manually (optional):

```bash path=null start=null
./scripts/update-project-status.sh
```
