import analytics from "@react-native-firebase/analytics";
import auth from "@react-native-firebase/auth";
import crashlytics from "@react-native-firebase/crashlytics";
import firestore from "@react-native-firebase/firestore";
import remoteConfig from "@react-native-firebase/remote-config";

// Initialize and export the services
const firebaseAuth = auth();
const firebaseFirestore = firestore();
const firebaseAnalytics = analytics();
const firebaseCrashlytics = crashlytics();
const firebaseRemoteConfig = remoteConfig();

/**
 * Initializes Remote Config with default values and fetches latest.
 */
async function initRemoteConfig(): Promise<void> {
  try {
    await firebaseRemoteConfig.setDefaults({
      show_banner_ad: false,
      interstitial_ad_frequency: 10,
    });
    const fetched = await firebaseRemoteConfig.fetchAndActivate();
    if (fetched) {
      console.log("Remote config updated.");
    }
  } catch (error) {
    console.error("Error initializing Remote Config:", error);
    firebaseCrashlytics.recordError(error as Error);
  }
}

/**
 * Logs an error to Crashlytics with additional context.
 * @param error The error object or message.
 * @param context Additional key-value pairs for context.
 */
function logError(error: unknown, context?: Record<string, string | number | boolean>): void {
  const err = error instanceof Error ? error : new Error(String(error));
  if (context) {
    // Convert all values to strings as required by Crashlytics
    const stringContext: Record<string, string> = {};
    for (const [key, value] of Object.entries(context)) {
      stringContext[key] = String(value);
    }
    firebaseCrashlytics.setAttributes(stringContext);
  }
  firebaseCrashlytics.recordError(err);
}

export const FirebaseService = {
  auth: firebaseAuth,
  firestore: firebaseFirestore,
  analytics: firebaseAnalytics,
  crashlytics: firebaseCrashlytics,
  remoteConfig: firebaseRemoteConfig,
  initRemoteConfig,
  logError,
};
