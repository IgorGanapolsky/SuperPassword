# Branch Strategy

## Main Branches

- `main` - Production code
  - Protected branch
  - Requires pull request reviews
  - Requires status checks to pass
  - No direct pushes
- `develop` - Development code
  - Protected branch
  - Requires pull request reviews
  - Requires status checks to pass
  - No direct pushes

## Working Branches

- Feature branches: `feat/*`
  - New features and enhancements
  - Branch from: `develop`
  - Merge to: `develop`

- Bug fix branches: `fix/*`
  - Bug fixes for existing features
  - Branch from: `develop`
  - Merge to: `develop`

- Hotfix branches: `hotfix/*`
  - Critical fixes for production issues
  - Branch from: `main`
  - Merge to: `main` and `develop`

- Release branches: `release/*`
  - Release preparation
  - Branch from: `develop`
  - Merge to: `main` and `develop`

## Branch Protection Rules

### `main` and `develop`

- Require pull request reviews
- Require status checks to pass
- Require linear history
- Include administrators in restrictions
- Automatically delete head branches after merge

### Working Branches

- No direct restrictions
- Follow naming conventions
- Delete after merging

## Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

Types:

- feat: A new feature
- fix: A bug fix
- docs: Documentation only changes
- style: Changes that do not affect the meaning of the code
- refactor: A code change that neither fixes a bug nor adds a feature
- perf: A code change that improves performance
- test: Adding missing tests or correcting existing tests
- chore: Changes to the build process or auxiliary tools

Example:

```
feat(auth): implement biometric authentication

- Add FaceID/TouchID support
- Add fallback to PIN
- Add user preference toggle

Closes #123
```
