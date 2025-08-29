# Security Policy

## Supported Versions

We release patches for security vulnerabilities. Which versions are eligible for
receiving such patches depends on the CVSS v3.0 Rating:

| CVSS v3.0 | Supported Versions                        |
| --------- | ---------------------------------------- |
| 9.0-10.0  | Releases within the last 6 months        |
| 4.0-8.9   | Most recent release                      |

## Reporting a Vulnerability

Please report security vulnerabilities through private means:

1. Email: security@securepass.generator
2. Through GitHub's Security Advisories: https://github.com/IgorGanapolsky/SuperPassword/security/advisories/new

Please include the following information:
- Type of issue (e.g. buffer overflow, SQL injection, cross-site scripting, etc.)
- Full paths of source file(s) related to the manifestation of the issue
- The location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Impact of the issue, including how an attacker might exploit it

## Security Measures

### Code Signing
- All iOS builds are signed with Apple Developer certificates
- Android builds use Google Play App Signing
- App Store Connect API keys are rotated every 6 months

### Data Protection
- All sensitive data is encrypted at rest using AES-256
- Network requests use certificate pinning in production
- No sensitive data is stored in device logs
- Automatic data sanitization in debug logs

### Authentication & Authorization
- OAuth 2.0 for third-party integrations
- Biometric authentication available for app access
- Secure session management with automatic timeouts
- Rate limiting on authentication attempts

### Compliance
- GDPR compliant data handling
- CCPA compliance for California users
- Regular security audits
- Bug bounty program active

### Build Security
- Dependency scanning in CI/CD pipeline
- SBOM generation for each release
- Code signing verification
- Container scanning
- Automated security testing

## Security Measures Implementation

### For Developers

1. **Local Development**
   - Use `.env.development` for development credentials
   - Never commit sensitive credentials
   - Use mock data for testing
   - Enable all security lint rules

2. **Code Review Requirements**
   - Security-focused code review checklist
   - Automated security scanning must pass
   - No security warnings in dependencies
   - All new APIs must use HTTPS

3. **Testing Requirements**
   - Security test coverage > 90%
   - Penetration testing before major releases
   - Regular vulnerability scanning
   - API security testing

### For Users

1. **Data Security**
   - All user data is encrypted
   - Optional biometric authentication
   - Secure password storage
   - Regular security updates

2. **Privacy**
   - No data collection without consent
   - Clear data usage policies
   - Data deletion on request
   - Regular privacy audits
