// Stub implementation for Firebase - replace when adding back @react-native-firebase packages

export const FirebaseService = {
  get auth() {
    return {
      currentUser: null,
      signInAnonymously: () => Promise.resolve({ user: null }),
      signOut: () => Promise.resolve(),
    };
  },
  get firestore() {
    return {
      collection: () => ({
        doc: () => ({
          get: () => Promise.resolve({ exists: false }),
          set: () => Promise.resolve(),
        }),
      }),
    };
  },
  get analytics() {
    return {
      logEvent: (event: string, params?: any) => {
        console.log(`Analytics event: ${event}`, params);
        return Promise.resolve();
      },
    };
  },
  get crashlytics() {
    return {
      setAttribute: () => Promise.resolve(),
      recordError: (error: Error) => {
        console.error("Crashlytics stub:", error);
        return Promise.resolve();
      },
    };
  },
  get remoteConfig() {
    return {
      getValue: (key: string) => ({ asString: () => "default" }),
      setDefaults: () => Promise.resolve(),
      fetchAndActivate: () => Promise.resolve(true),
    };
  },
  async initRemoteConfig() {
    console.log("Firebase RemoteConfig stub: initialized");
    return Promise.resolve();
  },
  logError(error: unknown, context?: Record<string, any>) {
    const err = error instanceof Error ? error : new Error(String(error));
    console.error("Firebase error log:", err, context);
  },
};
