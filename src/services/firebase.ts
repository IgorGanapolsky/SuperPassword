import "@react-native-firebase/app";
import analytics from "@react-native-firebase/analytics";
import auth from "@react-native-firebase/auth";
import crashlytics from "@react-native-firebase/crashlytics";
import firestore from "@react-native-firebase/firestore";
import remoteConfig from "@react-native-firebase/remote-config";

export const FirebaseService = {
  get auth() {
    return auth();
  },
  get firestore() {
    return firestore();
  },
  get analytics() {
    return analytics();
  },
  get crashlytics() {
    return crashlytics();
  },
  get remoteConfig() {
    return remoteConfig();
  },
  async initRemoteConfig() {
    await remoteConfig().setDefaults({
      premium_enabled: true,
      interstitial_frequency: 5,
    });
    await remoteConfig().fetchAndActivate();
  },
  logError(error: unknown, context?: Record<string, any>) {
    const err = error instanceof Error ? error : new Error(String(error));
    if (context) {
      Object.entries(context).forEach(([k, v]) =>
        crashlytics().setAttribute(k, String(v)),
      );
    }
    crashlytics().recordError(err);
  },
};
