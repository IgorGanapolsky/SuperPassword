import { ExpoConfig } from 'expo/config';

export interface AppEnvironment {
  APP_ENV: 'development' | 'staging' | 'production';
  APP_VERSION: string;
  BUILD_NUMBER: string;
  API_URL: string;
}

export interface AppConfig extends ExpoConfig {
  extra: {
    environment: AppEnvironment;
    sentry: {
      dsn: string;
      org: string;
      project: string;
    };
    analytics: {
      plausibleDomain?: string;
    };
    security: {
      encryptionEnabled: boolean;
      certificatePinning: boolean;
    };
    updates: {
      checkAutomatically: 'ON_ERROR_RECOVERY' | 'ON_LOAD';
      fallbackToCacheTimeout: number;
    };
  };
}

export interface BuildConfig {
  ios: {
    resourceClass: string;
    simulator: boolean;
    buildNumber: string;
    bundleIdentifier: string;
    entitlements: Record<string, unknown>;
  };
  android: {
    buildType: string;
    gradleCommand: string;
    image: string;
    versionCode: number;
  };
  env: Record<string, string>;
}
