import Constants from "expo-constants";
import * as Sentry from "sentry-expo";

let isInitialized = false;

/**
 * Initialize Sentry for error tracking
 * This function is safe to call multiple times
 */
export const initializeSentry = async (): Promise<boolean> => {
  if (isInitialized) {
    return true;
  }

  try {
    Sentry.init({
      dsn: Constants.expoConfig?.extra?.SENTRY_DSN as string,
      enableInExpoDevelopment: true,
      debug: __DEV__,
      tracesSampleRate: 1.0,
      enableAutoPerformanceTracing: true,
    });

    isInitialized = true;
    return true;
  } catch (error) {
    console.error("Failed to initialize Sentry:", error);
    return false;
  }
};

/**
 * Capture an exception to Sentry
 * Safe to call even if Sentry is not initialized
 */
export const captureException = (error: Error | unknown): void => {
  if (!isInitialized) {
    console.error("Sentry not initialized - Error:", error);
    return;
  }

  Sentry.Native.captureException(error);
};

/**
 * Capture a message to Sentry
 * Safe to call even if Sentry is not initialized
 */
export const captureMessage = (
  message: string,
  level?: "info" | "warning" | "error",
): void => {
  if (!isInitialized) {
    console.log(
      `Sentry not initialized - Message: [${level || "info"}] ${message}`,
    );
    return;
  }

  Sentry.Native.captureMessage(message, {
    level: level || "info",
  });
};

/**
 * Add breadcrumb for better error context
 */
export const addBreadcrumb = (message: string, category?: string): void => {
  if (!isInitialized) {
    console.log(
      `Sentry not initialized - Breadcrumb: [${category || "custom"}] ${message}`,
    );
    return;
  }

  Sentry.Native.addBreadcrumb({
    message,
    category: category || "custom",
  });
};

/**
 * Get the Sentry error boundary component
 * Returns null if Sentry is not initialized
 */
export const getErrorBoundary = (): React.ComponentType<any> | null => {
  if (!isInitialized) {
    return null;
  }

  return Sentry.Native.ErrorBoundary;
};

/**
 * Check if Sentry is initialized
 */
export const isSentryInitialized = (): boolean => {
  return isInitialized;
};
