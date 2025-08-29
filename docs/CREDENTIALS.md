# Credentials Management

This document describes how to manage credentials for the SuperPassword app.

## App Store Connect API Key

The app uses App Store Connect API for automated builds and submissions. The key is stored in the following location:

- Development: `./certs/private_key.p8`
- CI/CD: Base64 encoded in GitHub Actions secrets

### Current Credentials

- Key ID: `JT347VCCTP`
- Issuer ID: `9e5d7ebf-d4fe-47c2-8370-14dd87c17113`
- Team ID: `9GMM26JC5X`

### Setting Up Locally

1. Copy the `private_key.p8` file to the `./certs` directory
2. Ensure file permissions are secure:
   ```bash
   chmod 600 ./certs/private_key.p8
   ```

### Setting Up CI/CD

1. Base64 encode the private key:

   ```bash
   base64 -i private_key.p8 | pbcopy
   ```

2. Add the following secrets to GitHub Actions:
   - `APP_STORE_CONNECT_KEY_B64`: The base64 encoded private key
   - `APP_STORE_CONNECT_ISSUER_ID`: `9e5d7ebf-d4fe-47c2-8370-14dd87c17113`
   - `APP_STORE_CONNECT_KEY_ID`: `JT347VCCTP`
   - `EXPO_TOKEN`: Your Expo access token (get from expo.dev)

## Rotating Credentials

### App Store Connect API Key

1. Generate new key in App Store Connect
2. Update `eas.json` with new key details
3. Update the key file in `./certs`
4. Update GitHub Actions secrets
5. Update this documentation

## Security Best Practices

- Never commit credentials to version control
- Keep the private key secure and limit access
- Rotate keys periodically (recommended: every 6 months)
- Use separate keys for development and production
