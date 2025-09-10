# SuperPassword

[![CI Status](https://github.com/IgorGanapolsky/SuperPassword/workflows/CI%20(Optimized)/badge.svg?branch=develop)](https://github.com/IgorGanapolsky/SuperPassword/actions/workflows/ci-optimized.yml)
[![Security Scan](https://github.com/IgorGanapolsky/SuperPassword/workflows/Security%20Pipeline/badge.svg?branch=develop)](https://github.com/IgorGanapolsky/SuperPassword/actions/workflows/security.yml)
[![codecov](https://codecov.io/gh/IgorGanapolsky/SuperPassword/branch/main/graph/badge.svg)](https://codecov.io/gh/IgorGanapolsky/SuperPassword)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=IgorGanapolsky_SuperPassword&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=IgorGanapolsky_SuperPassword)
[![Security Rating](https://sonarcloud.io/api/project_badges/measure?project=IgorGanapolsky_SuperPassword&metric=security_rating)](https://sonarcloud.io/summary/new_code?id=IgorGanapolsky_SuperPassword)
[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=IgorGanapolsky_SuperPassword&metric=sqale_rating)](https://sonarcloud.io/summary/new_code?id=IgorGanapolsky_SuperPassword)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A professional password generator React Native Expo app with material design, leveraging modern security standards and ready for 2025 deployment requirements.

## Features

### Core Features (Free)

- ✨ Clean Material Design interface with gradient background
- 🔐 Password generation with customizable length (8-50 characters)
- ⚙️ Toggle options for uppercase, lowercase, numbers, special characters
- 💪 Real-time password strength meter with color coding
- 📋 One-tap copy to clipboard with success animation
- 📜 Password history (last 10 generated passwords) with timestamps
- 🌓 Dark mode toggle with system preference detection
- 📳 Haptic feedback for interactions
- 🖥️ Web support with PWA capabilities

### Premium Features ($2.99 one-time purchase)

- 📜 Unlimited password history
- ☁️ Cloud sync across devices
- 🎯 Custom character sets and exclusion rules
- 📦 Bulk password generation (up to 100 at once)
- 📊 Export passwords to CSV
- 🔒 Advanced security settings
- 🚫 No advertisements

## Tech Stack

- React Native with Expo SDK 53
- TypeScript 5.x
- React Navigation 7.x
- React Native Paper (Material Design)
- Jest & React Testing Library
- Sentry for error tracking
- Firebase for backend services
- AsyncStorage for local data

## CI/CD Pipeline

Our CI/CD pipeline ensures code quality, security, and reliable deployments using GitHub Actions.

### Workflows

1.  **CI (Optimized)** (`.github/workflows/ci-optimized.yml`): Runs on pull requests and pushes to `develop` and `main`. It handles:
    -   Linting and formatting checks
    -   TypeScript type checking
    -   Unit and integration tests with coverage reports
    -   EAS build validation for iOS and Android

2.  **Security Pipeline** (`.github/workflows/security.yml`): Runs daily and on pushes to protected branches. It performs:
    -   CodeQL analysis for security vulnerabilities
    -   Dependency checks using `npm audit` and Snyk
    -   Secret scanning with Gitleaks
    -   Mobile security analysis with MobSF

3.  **Release Pipeline** (`.github/workflows/release.yml`): Triggered by version tags (e.g., `v1.0.0`) or manually. It manages:
    -   Staging and production deployments
    -   Building and signing of app bundles/IPAs via EAS
    -   Submission to the Apple App Store and Google Play Store
    -   Generation of SBOM and release notes

### Branch Strategy & Protection

-   `main`: Protected branch for production-ready code. Changes are merged from `develop` via release PRs.
-   `develop`: Primary development branch. All feature branches are merged into `develop`.
-   **Pull Requests**: All PRs to `develop` and `main` require passing status checks (CI, security) and at least one code review.

## Getting Started

### Prerequisites

-   Node.js 20+ and npm
-   Expo CLI
-   iOS Simulator (Mac only) or Android Emulator

### Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/IgorGanapolsky/SuperPassword.git
    cd SuperPassword
    ```

2.  Install dependencies:
    ```bash
    npm install
    ```

3.  Start the development server:
    ```bash
    npx expo start
    ```

## Project Structure

```
src/
├── components/     # Reusable UI components
├── screens/        # App screens
├── navigation/     # Navigation setup
├── services/       # Services (storage, Firebase, etc.)
├── utils/          # Utility functions
├── hooks/          # Custom React hooks
├── types/          # TypeScript type definitions
└── constants/      # App constants and theme
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
