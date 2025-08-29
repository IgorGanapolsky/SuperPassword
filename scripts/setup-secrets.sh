#!/bin/bash

# Modern security setup script for SuperPassword (2025 Edition)

# Function to validate input is not empty
validate_input() {
    if [ -z "$1" ]; then
        echo "Error: Input cannot be empty"
        exit 1
    fi
}

# Function to securely set a GitHub secret
set_github_secret() {
    local secret_name=$1
    local secret_value=$2
    
    echo "Setting $secret_name..."
    echo "$secret_value" | gh secret set "$secret_name"
}

# Get GitGuardian API Key
echo "Please paste your GitGuardian API Key:"
read -s GITGUARDIAN_API_KEY
validate_input "$GITGUARDIAN_API_KEY"

# Get Snyk Token
echo -e "\nPlease paste your Snyk Token:"
read -s SNYK_TOKEN
validate_input "$SNYK_TOKEN"

# Get SonarCloud Token
echo -e "\nPlease paste your SonarCloud Token:"
read -s SONAR_TOKEN
validate_input "$SONAR_TOKEN"

# Set the secrets in GitHub
set_github_secret "GITGUARDIAN_API_KEY" "$GITGUARDIAN_API_KEY"
set_github_secret "SNYK_TOKEN" "$SNYK_TOKEN"
set_github_secret "SONAR_TOKEN" "$SONAR_TOKEN"

echo -e "\nAll secrets have been set successfully!"

# Configure branch protection
echo "Configuring branch protection rules..."
gh api \
  --method PUT \
  -H "Accept: application/vnd.github.v3+json" \
  "/repos/IgorGanapolsky/SuperPassword/branches/main/protection" \
  -f required_status_checks='{"strict":true,"contexts":["build","CodeQL","GitGuardian Security Checks","SonarCloud Code Analysis"]}' \
  -f enforce_admins=true \
  -f required_pull_request_reviews='{"dismissal_restrictions":{},"dismiss_stale_reviews":true,"require_code_owner_reviews":true,"required_approving_review_count":1}' \
  -f restrictions=null

# Add SonarCloud configuration
echo "Creating SonarCloud configuration..."
cat > sonar-project.properties << EOL
sonar.projectKey=IgorGanapolsky_SuperPassword
sonar.organization=igorganapolsky

# Sources
sonar.sources=src
sonar.tests=src
sonar.test.inclusions=**/*.test.ts,**/*.spec.ts
sonar.exclusions=**/*.test.ts,**/*.spec.ts,**/node_modules/**,**/coverage/**

# TypeScript specific
sonar.typescript.lcov.reportPaths=coverage/lcov.info
sonar.typescript.tsconfigPath=tsconfig.json

# General
sonar.sourceEncoding=UTF-8
sonar.verbose=true
EOL

echo "Setup complete! The repository is now configured with enhanced security and automation."

echo "🔐 Setting up App Store Connect API secrets"
echo "=========================================="

# Set Key ID
read -p "Enter your App Store Connect API Key ID: " KEY_ID
gh secret set APPSTORE_KEY_ID -b"$KEY_ID"

# Set Issuer ID
read -p "Enter your App Store Connect Issuer ID: " ISSUER_ID
gh secret set APPSTORE_ISSUER_ID -b"$ISSUER_ID"

# Set up Slack webhook
read -p "Enter your Slack webhook URL (press Enter to skip): " SLACK_URL
if [ ! -z "$SLACK_URL" ]; then
    gh secret set SLACK_WEBHOOK_URL -b"$SLACK_URL"
fi

echo "✅ Secrets have been set up successfully!"
echo ""
echo "You can now use the following GitHub Actions workflows:"
echo "- .github/workflows/eas-build.yml for building your app"
echo "- .github/workflows/eas-submit.yml for submitting to stores"
echo "- .github/workflows/appstore-automation.yml for analytics and monitoring"

# Clean up
rm -f private_key.p8

echo ""
echo "🚀 Ready to go! Try running your first automated build:"
echo "gh workflow run eas-build.yml -f platform=all -f profile=preview"
