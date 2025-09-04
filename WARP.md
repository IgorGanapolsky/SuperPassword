# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Repository Overview

SuperPassword is a mobile password management application built with React Native and Expo. This repository is currently under initial setup with core directory structure in place.

Status:

- Initial directory structure created
- CI/CD configuration in progress (PR #76)
- Core application setup pending

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

## Project Architecture

The application follows a feature-based architecture with React Native best practices:

```text path=null start=null
/src
├── components/     # Reusable UI components (pending)
├── contexts/       # React Context providers (pending)
├── hooks/         # Custom React hooks (pending)
├── navigation/    # Navigation configuration (pending)
├── screens/       # Feature-specific screens (pending)
├── services/      # Business logic layer (pending)
├── types/         # TypeScript definitions (pending)
└── utils/         # Helper utilities (pending)

/.github          # GitHub Actions and automation
/.eas             # Expo Application Services config
/.husky           # Git hooks for code quality
/.trunk           # Trunk-based development config
/assets           # Static assets and resources
/store-listings   # App store metadata
```

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

GitHub Actions workflows under configuration in PR #76:

- Automated testing
- Type checking
- Linting
- Security scanning
- Build validation

Workflow locations:

- Core CI: `.github/workflows/ci.yml` (pending)
- Security: `.github/workflows/security.yml` (pending)
- Release: `.github/workflows/release.yml` (pending)

## Getting Started

1. Clone and setup:

```bash path=null start=null
git clone {{REPO_URL}}
cd SuperPassword
git checkout develop
```

2. Watch PR #76 for CI/CD completion
3. Await initial package.json and build configuration
4. Reference this file for updated commands once setup is complete
