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
<<<<<<< HEAD
  if (isInitialized) {
    return true;
  }

  try {
    Sentry.init({
      dsn: Constants.expoConfig?.extra?.SENTRY_DSN as string,
      enableInExpoDevelopment: true,
      debug: __DEV__,
      tracesSampleRate: 1.0,
      enableAutoPerformanceTracking: true,
    });

    isInitialized = true;
    return true;
  } catch (error) {
    console.error("Failed to initialize Sentry:", error);
    return false;
  }
=======
  return true;
>>>>>>> fix/dependency-compatibility
};

/**
 * Capture an exception to Sentry
 */
export const captureException = (error: Error | unknown): void => {
<<<<<<< HEAD
  if (!isInitialized) {
    console.error("Sentry not initialized - Error:", error);
    return;
  }

=======
>>>>>>> fix/dependency-compatibility
  Sentry.Native.captureException(error);
};

/**
 * Capture a message to Sentry
 */
export const captureMessage = (
  message: string,
  level?: "info" | "warning" | "error",
): void => {
<<<<<<< HEAD
  if (!isInitialized) {
    console.log(
      `Sentry not initialized - Message: [${level || "info"}] ${message}`,
    );
    return;
  }

=======
>>>>>>> fix/dependency-compatibility
  Sentry.Native.captureMessage(message, {
    level: level || "info",
  });
};

/**
 * Add breadcrumb for better error context
 */
export const addBreadcrumb = (message: string, category?: string): void => {
<<<<<<< HEAD
  if (!isInitialized) {
    console.log(
      `Sentry not initialized - Breadcrumb: [${category || "custom"}] ${message}`,
    );
    return;
  }

=======
>>>>>>> fix/dependency-compatibility
  Sentry.Native.addBreadcrumb({
    message,
    category: category || "custom",
  });
};

/**
 * Get the Sentry error boundary component
 */
<<<<<<< HEAD
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
=======
export const getErrorBoundary = (): React.ComponentType<any> => {
  return Sentry.Native.ErrorBoundary;
>>>>>>> fix/dependency-compatibility
};
