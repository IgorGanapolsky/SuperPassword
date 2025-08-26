/**
 * Sentry error tracking service
 * This module safely initializes Sentry to avoid runtime conflicts
 */

import Constants from "expo-constants";

let SentryModule: typeof import("sentry-expo") | null = null;
let isInitialized = false;

// Get the Sentry DSN from constants
const SENTRY_DSN =
  Constants.expoConfig?.extra?.SENTRY_DSN ||
  Constants.manifest?.extra?.SENTRY_DSN ||
  "https://f51e85c3bd8c51d99059d901a5954113@o4509329568235520.ingest.us.sentry.io/4509329571315712";

/**
 * Initialize Sentry for error tracking
 * This function is safe to call multiple times
 */
export const initializeSentry = async (): Promise<boolean> => {
  if (isInitialized) {
    return true;
  }

  try {
    // Dynamically import Sentry to avoid initialization issues
    SentryModule = await import("sentry-expo");

    SentryModule.init({
      dsn: SENTRY_DSN,
      enableInExpoDevelopment: true,
      debug: __DEV__,
      tracesSampleRate: __DEV__ ? 1.0 : 0.1,
      // Additional options
      environment: __DEV__ ? "development" : "production",
      beforeSend: (event) => {
        // Filter out development noise if needed
        if (__DEV__) {
          console.log("Sentry Event:", event.event_id);
        }
        return event;
      },
    });

    isInitialized = true;
    console.log("✅ Sentry initialized successfully");
    return true;
  } catch (error) {
    console.warn("⚠️ Failed to initialize Sentry:", error);
    return false;
  }
};

/**
 * Capture an exception to Sentry
 * Safe to call even if Sentry is not initialized
 */
export const captureException = (error: Error | unknown): void => {
  if (!isInitialized || !SentryModule) {
    console.error("Error (Sentry not initialized):", error);
    return;
  }

  try {
    SentryModule.Native.captureException(error);
  } catch (e) {
    console.error("Failed to capture exception:", e);
  }
};

/**
 * Capture a message to Sentry
 * Safe to call even if Sentry is not initialized
 */
export const captureMessage = (
  message: string,
  level?: "info" | "warning" | "error",
): void => {
  if (!isInitialized || !SentryModule) {
    console.log(
      `Message (Sentry not initialized): [${level || "info"}] ${message}`,
    );
    return;
  }

  try {
    SentryModule.Native.captureMessage(message, level);
  } catch (e) {
    console.error("Failed to capture message:", e);
  }
};

/**
 * Add breadcrumb for better error context
 */
export const addBreadcrumb = (message: string, category?: string): void => {
  if (!isInitialized || !SentryModule) {
    return;
  }

  try {
    SentryModule.Native.addBreadcrumb({
      message,
      category: category || "custom",
      level: "info",
    });
  } catch (e) {
    console.error("Failed to add breadcrumb:", e);
  }
};

/**
 * Get the Sentry error boundary component
 * Returns null if Sentry is not initialized
 */
export const getErrorBoundary = () => {
  if (!isInitialized || !SentryModule) {
    return null;
  }

  return SentryModule.Native.ErrorBoundary;
};

/**
 * Check if Sentry is initialized
 */
export const isSentryInitialized = (): boolean => {
  return isInitialized;
};
