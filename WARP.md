# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Repository Overview

SuperPassword is a **AI-powered mobile password management application** built with React Native + Expo frontend and an Eko-powered Node.js AI backend. The repository is **production-ready** with revolutionary AI intelligence features.

Status: ✅ **COMPLETED + AI ENHANCED**

- ✅ Core mobile app fully implemented
- ✅ **NEW: Eko AI Intelligence Backend Service**
- ✅ **NEW: Multi-Agent Development Workflow**
- ✅ **NEW: Claude + Git Worktrees Architecture**
- ✅ CI/CD pipeline active and functional
- ✅ Full feature set with premium AI monetization
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

/server             # AI Backend Services ✅ NEW!
├── sp-ai-service/  # Eko-powered AI Intelligence API
│   ├── src/
│   │   ├── agents/     # Specialized AI agents
│   │   ├── routes/     # API endpoints
│   │   ├── services/   # Core business logic
│   │   └── types/      # TypeScript definitions
│   ├── package.json    # Node.js dependencies
│   └── test-demo.mjs   # AI features demo
└── README.md       # Backend documentation
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

**NEW: AI Intelligence Stack:**

- 🤖 Eko Framework 3.0.2 for agentic workflows
- 👤 Claude 3.5 Sonnet for AI analysis
- 🔍 Node.js + Fastify backend service
- 🔒 Firebase Authentication & Firestore
- 🌐 HaveIBeenPwned API integration
- 📊 Real-time security analytics

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

---

## 🤖 AI INTELLIGENCE ARCHITECTURE

### Multi-Agent Development Workflow

We use **git worktrees** + **specialized Claude agents** for parallel development:

```bash path=null start=null
# Git worktrees for parallel AI development
git worktree list

# Expected output:
../SuperPassword            develop
../sp-ai-intelligence      feature/ai-intelligence
../sp-secure-storage       feature/secure-storage
../sp-biometrics           feature/biometrics
../sp-ci-hardening         chore/ci-hardening
```

#### Agent Specialization Strategy

- **Security Claude**: E2EE implementation, SecureStore, key rotation
- **Auth Claude**: Biometrics, session hardening, Firebase Auth
- **AI Claude**: Eko integration, intelligence features, backend API
- **DevOps Claude**: CI/CD, testing, automation, deployment

#### Development Process per Worktree

1. **Plan & Document** (`docs/agents/{feature}/PLAN.md`)
2. **TDD Loop**: Write failing tests → Make pass → Refactor
3. **Multi-Agent Review**: 
   - Agent A implements
   - Agent B reviews & comments
   - Agent C verifies against plan/tests
4. **Commit with convention**: `feat: implement AI vault auditing`
5. **Open PR** with clear scope and rollback plan

### Eko AI Service Architecture

**Location**: `server/sp-ai-service/`

```typescript path=/Users/igorganapolsky/workspace/git/apps/SuperPassword/server/sp-ai-service/src/index.ts start=1
// Production-ready Fastify server with Eko integration
import Fastify from 'fastify';
import { EkoService } from './services/EkoService.js';

const server = Fastify({ logger: true });
server.decorate('ekoService', new EkoService());
```

#### Core AI Features Implemented

1. **🔍 Vault Security Audit**
   - **Endpoint**: `POST /api/v1/intelligence/audit`
   - **Purpose**: AI-powered password vulnerability analysis
   - **Output**: Security score, weak/breached/duplicate passwords, recommendations

2. **🎣 Phishing URL Detection**
   - **Endpoint**: `POST /api/v1/intelligence/phishing-check`
   - **Purpose**: Real-time URL threat analysis
   - **Output**: Risk level, phishing indicators, safe alternatives

3. **🔄 Password Rotation Planning**
   - **Endpoint**: `POST /api/v1/intelligence/rotation-plan`
   - **Purpose**: AI-optimized password rotation schedules
   - **Output**: Priority-based rotation timeline, site-specific guidance

4. **📊 Security Reports & Analytics**
   - **Endpoint**: `POST /api/v1/intelligence/generate-report`
   - **Purpose**: Executive/technical/user-friendly reports
   - **Output**: Formatted reports with trends and insights

#### Authentication & Authorization

```typescript path=null start=null
// Firebase Auth integration with tier-based limits
fastify.addHook('preHandler', async (request, reply) => {
  const token = request.headers.authorization?.substring(7);
  const user = await firebaseService.verifyToken(token);
  request.user = user;
  
  // Apply tier-based limits (Free: 10 passwords, Pro: unlimited)
  const userData = await firebaseService.getUserData(user.uid);
  request.userTier = userData.tier;
});
```

#### Monetization Integration

- **Free Tier**: Basic audit (10 passwords max)
- **Plus Tier ($5.99/mo)**: Advanced audits, breach monitoring
- **Pro Tier ($9.99/mo)**: Rotation planning, enterprise reports
- **Family Tier ($14.99/mo)**: Multi-user AI features
- **Enterprise**: Custom pricing, advanced analytics

### Local Development Setup

#### 1. AI Service Setup

```bash path=null start=null
# Navigate to AI service
cd server/sp-ai-service

# Install dependencies
npm install

# Configure environment
cp .env.example .env
# Edit .env with your API keys:
# ANTHROPIC_API_KEY=your_claude_key_here
```

#### 2. Start AI Service

```bash path=null start=null
# Development mode with hot reload
npm run dev

# Service runs on http://localhost:3001
# API docs: http://localhost:3001/docs
# Health check: http://localhost:3001/health
```

#### 3. Test AI Features

```bash path=null start=null
# Run comprehensive AI demo
./test-demo.mjs

# Run specific demos
./test-demo.mjs --audit          # Vault security audit
./test-demo.mjs --phishing       # Phishing detection
./test-demo.mjs --rotation       # Rotation planning
./test-demo.mjs --health         # Health check only
```

### Mobile App Integration

The React Native app connects to AI services via:

```typescript path=/Users/igorganapolsky/workspace/git/apps/SuperPassword/src/services/AIAssistant.ts start=1
// AI Assistant Service (planned)
import { VaultAuditRequest, PhishingCheckRequest } from '../types/ai.ts';

class AIAssistantService {
  private baseURL = 'http://localhost:3001/api/v1/intelligence';
  
  async auditVault(passwords: PasswordEntry[]): Promise<VaultAuditResult> {
    // Implementation connects to backend AI service
  }
}
```

### Production Deployment

#### Backend Service
- **Platform**: Railway, Render, or DigitalOcean
- **Environment**: Node.js 20+, PM2 process manager
- **Database**: Firebase Firestore for user data & audit history
- **Monitoring**: Sentry error tracking, Fastify logging

#### Security Considerations
- **API Keys**: Never exposed in mobile app, backend proxy only
- **Rate Limiting**: Tier-based limits enforced server-side
- **Authentication**: Firebase Auth tokens, JWT verification
- **Data Privacy**: No plaintext passwords stored server-side

### AI Agent Guidelines for Future Development

#### When Working on This Codebase:

1. **Always check current architecture** by reading this WARP.md
2. **Use appropriate worktree** for your feature area
3. **Follow TDD approach** with comprehensive test coverage
4. **Document your changes** in relevant PLAN.md files
5. **Test AI features** using `./test-demo.mjs` before committing
6. **Respect tier limits** and monetization boundaries
7. **Never commit API keys** - use .env files only

#### Common Commands for AI Agents:

```bash path=null start=null
# Check current architecture
cat WARP.md | grep -A 10 "AI INTELLIGENCE"

# Switch to AI development worktree
cd ../sp-ai-intelligence

# Test AI service health
cd server/sp-ai-service && ./test-demo.mjs --health

# Run comprehensive AI demos
cd server/sp-ai-service && ./test-demo.mjs

# Check service logs
tail -f server/sp-ai-service/server.log
```

#### Architecture Decisions Made:

- **Eko Framework**: Chosen for production-ready agentic workflows
- **Fastify**: High-performance Node.js framework for AI API
- **Claude 3.5 Sonnet**: Primary LLM for intelligent analysis
- **Firebase**: Authentication, user data, audit history
- **TypeScript**: End-to-end type safety (mobile + backend)
- **Git Worktrees**: Parallel development without branch conflicts

This architecture enables SuperPassword to be the **first password manager with true AI intelligence**, providing competitive advantages through advanced security analysis, proactive breach detection, and personalized security coaching.
