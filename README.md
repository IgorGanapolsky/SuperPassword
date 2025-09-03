# SuperPassword - Secure Password Management App

## CI/CD Pipeline

Our CI/CD pipeline is designed to ensure code quality, security, and reliable deployments:

### Workflows

1. **CI Pipeline** (.github/workflows/ci.yml)
   - Runs on all PRs and pushes to develop
   - Validates code quality (TypeScript, lint, tests)
   - Performs security checks
   - Builds development versions

2. **Security Pipeline** (.github/workflows/security.yml)
   - Daily security scans
   - Dependency vulnerability checks
   - Code security analysis
   - Mobile-specific security checks

3. **Release Pipeline** (.github/workflows/release.yml)
   - Triggered by version tags or manually
   - Supports staging and production deployments
   - Generates SBOM and release notes
   - Handles app store submissions

### Branch Protection

- All work branches from `develop`
- PRs require:
  - CI pipeline success
  - Code review approval
  - Up-to-date branch status
- `main` branch:
  - Protected from direct pushes
  - Requires admin approval for merges
  - Release tags trigger deployments

### Security Features

- CodeQL analysis
- OWASP dependency checking
- Secret scanning
- Mobile security framework integration
- SBOM generation
- Dependency audit

### Release Process

1. Create feature branch from develop
2. Open PR to develop
3. Pass CI and get approval
4. Merge to develop
5. Create release PR to main (when ready)
6. Get admin approval
7. Tag release triggers deployment

# SuperPassword

## Development Workflow

### Branch Strategy

- `main`: Production-ready code
- `develop`: Primary development branch
- Feature branches: Create from `develop`, merge back to `develop`

### Pull Request Process

1. Create branch from `develop`
2. Make your changes
3. Ensure all checks pass:
   - Linting
   - Type checking
   - Tests
   - Build verification
4. Submit PR to `develop`
5. Once approved, merge to `develop`

### Active GitHub Actions

- **CI**: Runs on PRs and pushes to main/develop
  - Linting, type checking, tests, and build verification
- **CodeQL**: Security scanning
  - Runs weekly and on PRs to main
- **Dependabot**: Dependency updates
  - Monthly schedule
  - Security updates as needed

### Development Commands

```bash
# Install dependencies
npm install

# Start development server
npm run start

# Run tests
npm run test

# Lint code
npm run lint

# Type check
npm run typecheck

# Build app
npm run build
```

# SecurePass - Password Generator

[![CI/CD Pipeline](https://github.com/IgorGanapolsky/SuperPassword/actions/workflows/main.yml/badge.svg)](https://github.com/IgorGanapolsky/SuperPassword/actions/workflows/main.yml)
[![codecov](https://codecov.io/gh/IgorGanapolsky/SuperPassword/branch/main/graph/badge.svg)](https://codecov.io/gh/IgorGanapolsky/SuperPassword)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)
[![Maintainability](https://api.codeclimate.com/v1/badges/your-repo-id/maintainability)](https://codeclimate.com/github/IgorGanapolsky/SuperPassword/maintainability)
[![Known Vulnerabilities](https://snyk.io/test/github/IgorGanapolsky/SuperPassword/badge.svg)](https://snyk.io/test/github/IgorGanapolsky/SuperPassword)

A professional password generator React Native Expo app with Material Design, ready for deployment to Google Play Store and Apple App Store.

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

### Premium Features ($2.99 one-time purchase)

- 📜 Unlimited password history
- ☁️ Cloud sync across devices
- 🎯 Custom character sets and exclusion rules
- 📦 Bulk password generation (up to 100 at once)
- 📊 Export passwords to CSV
- 🔒 Advanced security settings
- 🚫 No advertisements

## Tech Stack

- React Native with Expo
- TypeScript
- React Navigation
- React Native Paper (Material Design)
- AsyncStorage for local data
- Firebase (ready for integration)
- Google AdMob (ready for integration)

## Getting Started

### Prerequisites

- Node.js 16+ and npm/yarn
- Expo CLI
- iOS Simulator (Mac only) or Android Emulator

### Installation

1. Copy env and install dependencies:

```bash
cp .env.example .env
npm install
```

2. Start the development server:

```bash
npx expo start
```

3. Run on iOS Simulator:

```bash
npx expo run:ios
```

4. Run on Android Emulator:

```bash
npx expo run:android
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
├── constants/      # App constants and theme
└── store/          # State management
```

## Building for Production

### Using EAS Build

1. Install EAS CLI:

```bash
npm install -g eas-cli
```

2. Configure EAS:

```bash
eas build:configure
```

3. Build for iOS:

```bash
eas build --platform ios --profile production
```

4. Build for Android:

```bash
eas build --platform android --profile production
```

5. Submit to stores (after first credential setup):

```bash
eas submit --platform ios --profile production
.eas submit --platform android --profile production
```

## App Store Configuration

### Google Play Store

- Package name: `com.securepass.generator`
- Target SDK: 34
- Min SDK: 24 (Android 7.0+)

### Apple App Store

- Bundle ID: `com.securepass.generator`
- Deployment target: iOS 15.1+

## Firebase Setup (Required for production)

1. Create a Firebase project at https://console.firebase.google.com
2. Add iOS and Android apps with the package/bundle IDs
3. Download `google-services.json` (Android) and `GoogleService-Info.plist` (iOS)
4. Place configuration files in the project root
5. Configure Firebase services:
   - Authentication
   - Firestore
   - Remote Config
   - Analytics
   - Crashlytics

## AdMob Setup (Required for monetization)

1. Create AdMob account at https://admob.google.com
2. Create ad units:
   - Banner ad for main screen
   - Interstitial ad for password generations
   - Rewarded video for premium trial
3. Add AdMob App IDs to app configuration
4. Test with test ad unit IDs during development

## Environment Variables

Copy `.env.example` to `.env` and set values. Key settings:

- APP_NAME, APP_SLUG, APP_SCHEME, EXPO_OWNER
- IOS_BUNDLE_ID, ANDROID_PACKAGE
- EAS_PROJECT_ID
- ADMOB_APP_ID_IOS, ADMOB_APP_ID_ANDROID
- SENTRY_DSN

## CI/CD & Autonomous Ops

- Local hourly autofix: LaunchAgent runs `scripts/autofix-local.sh` to format/lint, commit, and push.
- Cloud hourly autofix: `.github/workflows/autofix.yml` runs Prettier + ESLint and auto-commits.
- CI checks: `.github/workflows/ci.yml` runs tsc, expo-doctor, lint, and prettier on PRs.
- OTA updates (optional): use EAS Update to ship JS-only fixes to channels.

### Sentry (crash and error reporting)

1. Create a Sentry project (React Native) and get DSN.
2. Set env:

```bash
echo "SENTRY_DSN=your_sentry_dsn" >> .env
```

3. For CI/EAS builds, set secrets:
   - GitHub Actions: `SENTRY_AUTH_TOKEN` (org:project release:write)
   - EAS Secrets: `SENTRY_AUTH_TOKEN`

4. Build a release with EAS so source maps upload and crashes link to code:

```bash
eas build --platform ios --profile production
eas build --platform android --profile production
```

### Firebase (Auth, Analytics, Crashlytics, Firestore, Remote Config)

1. Download platform configs from Firebase Console and place at project root:
   - iOS: `GoogleService-Info.plist` (path referenced in `app.config.ts`)
   - Android: `google-services.json` (path referenced in `app.config.ts`)
2. Dev client (required for local dev with native SDKs):
   - iOS: `eas build --profile development --platform ios && eas build:run --platform ios`
   - Android: `eas build --profile development --platform android && eas build:run --platform android`
3. Start server: `npx expo start --dev-client`
4. Verify Crashlytics: trigger `FirebaseService.logError(new Error('test'), { screen: 'Home' })` and check Firebase console.

### Release flow (fully scripted)

```bash
# 1) Set env vars in .env or CI secrets (bundle IDs, EAS_PROJECT_ID, AdMob, Sentry)
# 2) Build
EAS_NO_VCS=1 eas build --platform ios --profile production
EAS_NO_VCS=1 eas build --platform android --profile production
# 3) Submit
EAS_NO_VCS=1 eas submit --platform ios --profile production
EAS_NO_VCS=1 eas submit --platform android --profile production
```

Notes:

- Manage credentials via EAS on first run; subsequent runs use stored credentials.
- For multiple apps, keep a repo per app; parameterize via `app.config.ts` + `.env`.

## Testing

Run tests:

```bash
npm test
```

Run TypeScript type checking:

```bash
npx tsc --noEmit
```

## License

MIT

## Support

For support, email support@securepass.app
