#!/bin/bash

# Comprehensive App Store Connect API Setup Script
# This script will:
# 1. Generate API keys
# 2. Set up GitHub secrets (requires gh CLI)
# 3. Configure EAS for automated builds

echo "🔐 App Store Connect API Setup"
echo "============================="

# Check for required tools
check_requirements() {
    local missing_tools=()
    
    if ! command -v openssl &> /dev/null; then
        missing_tools+=("openssl")
    fi
    
    if ! command -v gh &> /dev/null; then
        missing_tools+=("gh (GitHub CLI)")
    fi
    
    if ! command -v eas &> /dev/null; then
        missing_tools+=("eas-cli")
    fi
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        echo "❌ Error: The following required tools are missing:"
        printf '%s\n' "${missing_tools[@]}"
        echo "Please install them and try again."
        exit 1
    fi
}

# Generate private key
generate_private_key() {
    echo "📝 Generating private key..."
    openssl ecparam -name prime256v1 -genkey -noout -out private_key.p8
    
    if [ $? -eq 0 ]; then
        echo "✅ Private key generated successfully"
        PRIVATE_KEY_CONTENT=$(cat private_key.p8)
    else
        echo "❌ Failed to generate private key"
        exit 1
    fi
}

# Set up GitHub secrets
setup_github_secrets() {
    echo "🔒 Setting up GitHub secrets..."
    
    # Check if authenticated with GitHub CLI
    if ! gh auth status &> /dev/null; then
        echo "❌ Not authenticated with GitHub CLI. Please run 'gh auth login' first."
        exit 1
    }
    
    # Get repository name
    REPO_URL=$(git config --get remote.origin.url)
    REPO_NAME=$(echo $REPO_URL | sed 's/.*github.com[:\/]\(.*\).git/\1/')
    
    echo "📦 Using repository: $REPO_NAME"
    
    # Set GitHub secrets
    echo "🔑 Setting APPSTORE_PRIVATE_KEY secret..."
    echo "$PRIVATE_KEY_CONTENT" | gh secret set APPSTORE_PRIVATE_KEY --repo="$REPO_NAME"
    
    echo "🔑 Setting APPSTORE_KEY_ID secret..."
    read -p "Enter your App Store Connect API Key ID: " KEY_ID
    echo "$KEY_ID" | gh secret set APPSTORE_KEY_ID --repo="$REPO_NAME"
    
    echo "🔑 Setting APPSTORE_ISSUER_ID secret..."
    read -p "Enter your App Store Connect Issuer ID: " ISSUER_ID
    echo "$ISSUER_ID" | gh secret set APPSTORE_ISSUER_ID --repo="$REPO_NAME"
    
    # Set up Slack webhook if needed
    read -p "Do you want to set up Slack notifications? (y/n) " SLACK_SETUP
    if [[ $SLACK_SETUP =~ ^[Yy]$ ]]; then
        read -p "Enter your Slack webhook URL: " SLACK_WEBHOOK
        echo "$SLACK_WEBHOOK" | gh secret set SLACK_WEBHOOK_URL --repo="$REPO_NAME"
    fi
}

# Configure EAS
setup_eas() {
    echo "🛠 Setting up EAS..."
    
    # Check if logged in to EAS
    if ! eas whoami &> /dev/null; then
        echo "❌ Not logged in to EAS. Please run 'eas login' first."
        exit 1
    fi
    
    # Update EAS configuration
    echo "📝 Updating EAS configuration..."
    eas update
}

# Main execution
main() {
    echo "🚀 Starting setup..."
    
    check_requirements
    generate_private_key
    setup_github_secrets
    setup_eas
    
    echo "✨ Setup complete!"
    echo ""
    echo "Next steps:"
    echo "1. Verify your GitHub Actions workflows are properly configured"
    echo "2. Try running a test build with 'gh workflow run eas-build.yml'"
    echo "3. Monitor the build progress in the GitHub Actions tab"
    echo ""
    echo "Remember to:"
    echo "- Keep your private key secure"
    echo "- Regularly rotate your API keys"
    echo "- Monitor your GitHub Actions usage"
    
    # Clean up
    rm private_key.p8
}

# Run the script
main
