# Contributing to SuperPassword

## Getting Started

1. Fork the repository
2. Clone your fork:

   ```bash
   git clone git@github.com:your-username/SuperPassword.git
   cd SuperPassword
   ```

3. Install dependencies:

   ```bash
   npm install
   ```

4. Start development:
   ```bash
   npm start
   ```

## Development Process

### 1. Choose an Issue

- Check existing issues
- Create new issue if needed
- Get assignment/approval

### 2. Create Branch

```bash
git checkout develop
git pull
git checkout -b feat/your-feature
```

### 3. Make Changes

- Follow code style
- Add tests
- Update documentation

### 4. Commit Changes

Use conventional commits:

```bash
git commit -m "feat: add new feature"
git commit -m "fix: resolve bug"
git commit -m "docs: update readme"
```

### 5. Create PR

```bash
git push -u origin feat/your-feature
gh pr create --base develop
```

## Code Standards

### TypeScript

- Use strict mode
- No any types
- Document complex types

### React

- Functional components
- Hooks for state
- Props typing
- Performance optimization

### Testing

- Jest for unit tests
- React Testing Library
- E2E with Detox
- High coverage

### Style

- ESLint configuration
- Prettier formatting
- Component organization
- Import ordering

## Review Process

### PR Requirements

- Passing CI/CD
- No conflicts
- Documentation
- Tests
- Clean code

### Review Guidelines

- Be constructive
- Focus on:
  - Security
  - Performance
  - Maintainability
  - User experience

## Release Process

### Version Bump

- Follow semver
- Update changelog
- Tag releases

### Deployment

- Staging first
- QA validation
- Production release
- Post-deploy checks

## Need Help?

- Read documentation
- Ask in issues
- Join discussions
- Contact maintainers
