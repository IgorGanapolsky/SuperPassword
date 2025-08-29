import Constants from "expo-constants";
import * as Sentry from "sentry-expo";

// Initialize Sentry immediately
try {
  Sentry.init({
    dsn: Constants.expoConfig?.extra?.SENTRY_DSN as string,
    enableInExpoDevelopment: true,
    debug: __DEV__,
    tracesSampleRate: 1.0,
    enableAutoPerformanceTracing: true,
  });
} catch (error) {
  console.error("Failed to initialize Sentry:", error);
}

/**
 * Initialize Sentry for error tracking
 * This function exists for backward compatibility
 */
export const initializeSentry = async (): Promise<boolean> => {
  return true;
};

/**
 * Capture an exception to Sentry
 */
export const captureException = (error: Error | unknown): void => {
  Sentry.Native.captureException(error);
};

/**
 * Capture a message to Sentry
 */
export const captureMessage = (
  message: string,
  level?: "info" | "warning" | "error",
): void => {
  Sentry.Native.captureMessage(message, {
    level: level || "info",
  });
};

/**
 * Add breadcrumb for better error context
 */
export const addBreadcrumb = (message: string, category?: string): void => {
  Sentry.Native.addBreadcrumb({
    message,
    category: category || "custom",
  });
};

/**
 * Get the Sentry error boundary component
 */
export const getErrorBoundary = (): React.ComponentType<any> => {
  return Sentry.Native.ErrorBoundary;
};
