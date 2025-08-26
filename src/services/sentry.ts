/**
 * Sentry error tracking service - STUB IMPLEMENTATION
 * Replace when adding back sentry-expo package
 */

let isInitialized = false;

/**
 * Initialize Sentry for error tracking
 * This function is safe to call multiple times
 */
export const initializeSentry = async (): Promise<boolean> => {
  if (isInitialized) {
    return true;
  }

  // Stub implementation
  console.log("Sentry stub: initialization called");
  isInitialized = true;
  return true;
};

/**
 * Capture an exception to Sentry
 * Safe to call even if Sentry is not initialized
 */
export const captureException = (error: Error | unknown): void => {
  console.error("Sentry stub - Error:", error);
};

/**
 * Capture a message to Sentry
 * Safe to call even if Sentry is not initialized
 */
export const captureMessage = (
  message: string,
  level?: "info" | "warning" | "error",
): void => {
  console.log(`Sentry stub - Message: [${level || "info"}] ${message}`);
};

/**
 * Add breadcrumb for better error context
 */
export const addBreadcrumb = (message: string, category?: string): void => {
  console.log(`Sentry stub - Breadcrumb: [${category || "custom"}] ${message}`);
};

/**
 * Get the Sentry error boundary component
 * Returns null if Sentry is not initialized
 */
export const getErrorBoundary = () => {
  return null;
};

/**
 * Check if Sentry is initialized
 */
export const isSentryInitialized = (): boolean => {
  return isInitialized;
};
