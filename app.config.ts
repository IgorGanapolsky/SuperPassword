import type { ExpoConfig } from "expo/config";
import "dotenv/config";
import type { AppConfig } from "./src/config/types";
import { version } from "./package.json";

const BUILD_NUMBER = process.env.BUILD_NUMBER || "1";
const APP_ENV = process.env.APP_ENV || "development";

const appName = process.env.APP_NAME ?? "SecurePass - Password Generator";
const slug = process.env.APP_SLUG ?? "superpassword";
const scheme = process.env.APP_SCHEME ?? "securepass";
const owner = process.env.EXPO_OWNER ?? "igorganapolsky";

const iosBundleId =
  process.env.IOS_BUNDLE_ID ?? "com.igorganapolsky.superpassword";
const androidPackage =
  process.env.ANDROID_PACKAGE ?? "com.igorganapolsky.superpassword";
const easProjectId =
  process.env.EAS_PROJECT_ID || "9cd42433-a590-418c-82bc-b5f884a1caed";
const isUuid = (v?: string) =>
  !!v &&
  /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$/.test(
    v,
  );

const config: ExpoConfig = {
  name: appName,
  slug,
  version: "1.0.0",
  orientation: "portrait",
  icon: "./assets/icon.png",
  userInterfaceStyle: "automatic",
  scheme,
  owner,
  jsEngine: "hermes",
  platforms: ["ios", "android", "web"],
  splash: {
    image: "./assets/splash.png",
    resizeMode: "cover",
    backgroundColor: "#667eea",
  },
  ios: {
    supportsTablet: true,
    bundleIdentifier: iosBundleId,
    buildNumber: "1",
    infoPlist: {
      NSUserTrackingUsageDescription:
        "This identifier will be used to deliver personalized ads to you.",
      SKAdNetworkItems: [
        { SKAdNetworkIdentifier: "cstr6suwn9.skadnetwork" },
        { SKAdNetworkIdentifier: "4fzdc2evr5.skadnetwork" },
        { SKAdNetworkIdentifier: "v72qych5uu.skadnetwork" },
      ],
    },
    config: { usesNonExemptEncryption: false },
  },
  android: {
    package: androidPackage,
    versionCode: 1,
    adaptiveIcon: {
      foregroundImage: "./assets/adaptive-icon.png",
      backgroundColor: "#667eea",
    },
    permissions: [
      "INTERNET",
      "VIBRATE",
      "ACCESS_NETWORK_STATE",
      "com.google.android.gms.permission.AD_ID",
    ],
  },
  web: { favicon: "./assets/favicon.png", bundler: "metro" },
  plugins: [
    "expo-font",
    [
      "sentry-expo",
      {
        organization: process.env.SENTRY_ORG,
        project: process.env.SENTRY_PROJECT,
      },
    ],
    [
      "expo-build-properties",
      {
        android: {
          compileSdkVersion: 35,
          targetSdkVersion: 34,
          buildToolsVersion: "35.0.0",
          minSdkVersion: 26,
        },
        ios: { deploymentTarget: "15.1" },
      },
    ],
  ],
  extra: {
    environment: {
      APP_ENV,
      APP_VERSION: version,
      BUILD_NUMBER,
      API_URL: process.env.API_URL || "https://api.securepass.generator"
    },
    security: {
      encryptionEnabled: true,
      certificatePinning: APP_ENV === "production"
    },
    ...(isUuid(easProjectId) ? { eas: { projectId: easProjectId } } : {}),
    SENTRY_DSN: process.env.EXPO_PUBLIC_SENTRY_DSN,
    PLAUSIBLE_DOMAIN: process.env.EXPO_PUBLIC_PLAUSIBLE_DOMAIN,
    STRIPE_PUBLISHABLE_KEY: process.env.EXPO_PUBLIC_STRIPE_PUBLISHABLE_KEY,
    FIREBASE_API_KEY: process.env.EXPO_PUBLIC_FIREBASE_API_KEY,
    FIREBASE_AUTH_DOMAIN: process.env.EXPO_PUBLIC_FIREBASE_AUTH_DOMAIN,
    FIREBASE_PROJECT_ID: process.env.EXPO_PUBLIC_FIREBASE_PROJECT_ID,
    FIREBASE_STORAGE_BUCKET: process.env.EXPO_PUBLIC_FIREBASE_STORAGE_BUCKET,
    FIREBASE_MESSAGING_SENDER_ID:
      process.env.EXPO_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
    FIREBASE_APP_ID: process.env.EXPO_PUBLIC_FIREBASE_APP_ID,
    FIREBASE_MEASUREMENT_ID: process.env.EXPO_PUBLIC_FIREBASE_MEASUREMENT_ID,
  },
  updates: {
    fallbackToCacheTimeout: 0,
    checkAutomatically: APP_ENV === "production" ? "ON_ERROR_RECOVERY" : "ON_LOAD",
    url: "https://u.expo.dev/" + easProjectId
  },
  assetBundlePatterns: ["**/*"],
  extra: {
    hooks: {
    postPublish: [
      {
        file: "sentry-expo/upload-sourcemaps",
        config: {
          organization: process.env.SENTRY_ORG,
          project: process.env.SENTRY_PROJECT,
          authToken: process.env.SENTRY_AUTH_TOKEN,
        },
      },
    ],
  },
};

export default config;
