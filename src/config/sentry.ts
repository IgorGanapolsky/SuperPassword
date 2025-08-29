import * as Sentry from 'sentry-expo';
import Constants from 'expo-constants';
import { Platform } from 'react-native';
import { getVersionInfo } from './version';

interface SentryConfig {
  dsn: string;
  debug?: boolean;
  environment: string;
  release?: string;
  dist?: string;
  enableAutoPerformanceTracking?: boolean;
  tracesSampleRate: number;
  enableUserInteractionTracing?: boolean;
}

const getSentryConfig = async (): Promise<SentryConfig> => {
  const versionInfo = await getVersionInfo();
  const environment = Constants.expoConfig?.extra?.environment?.APP_ENV || 'development';
  const isProd = environment === 'production';

  return {
    dsn: Constants.expoConfig?.extra?.SENTRY_DSN || '',
    debug: !isProd,
    environment,
    release: `${versionInfo.bundleId}@${versionInfo.version}`,
    dist: versionInfo.buildNumber,
    enableAutoPerformanceTracking: true,
    tracesSampleRate: isProd ? 0.2 : 1.0,
    enableUserInteractionTracing: true,
  };
};

export const initSentry = async (): Promise<void> => {
  const config = await getSentryConfig();
  
  Sentry.init({
    ...config,
    enableAutoSessionTracking: true,
    sessionTrackingIntervalMillis: 30000,
    // Enable native crash handling
    enableNative: Platform.OS !== 'web',
    // Enable native instrumentation
    enableNativeNagger: Platform.OS !== 'web',
    // Capture uncaught exceptions
    enableAutoUnhandledPromiseRejections: true,
    // Enable performance monitoring
    enableAutoPerformanceTracking: true,
    // Additional configuration based on environment
    beforeSend: (event) => {
      // Don't send events from development
      if (config.environment === 'development') {
        return null;
      }
      return event;
    },
    // Configure performance
    integrations: [
      new Sentry.Native.ReactNativeTracing({
        shouldCreateSpanForRequest: (url) => {
          // Only create spans for your api
          return url.includes('api.securepass.generator');
        },
        tracePropagationTargets: [
          'api.securepass.generator',
        ],
      }),
    ],
  });

  // Set user segment for better error tracking
  Sentry.Native.setTag('platform', Platform.OS);
  Sentry.Native.setTag('runtime', 'react-native');
  Sentry.Native.setTag('expo', Constants.expoVersion);
};

export const configureScope = (userId?: string): void => {
  Sentry.Native.configureScope((scope) => {
    if (userId) {
      scope.setUser({ id: userId });
    }
    scope.setTag('lastActive', new Date().toISOString());
  });
};

export const captureError = (error: Error, context?: Record<string, any>): void => {
  Sentry.Native.withScope((scope) => {
    if (context) {
      Object.entries(context).forEach(([key, value]) => {
        scope.setExtra(key, value);
      });
    }
    Sentry.Native.captureException(error);
  });
};
