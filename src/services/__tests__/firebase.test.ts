import { FirebaseService } from "../firebase";

describe("FirebaseService", () => {
  beforeEach(() => {
    jest.spyOn(console, "log").mockImplementation(() => {});
    jest.spyOn(console, "error").mockImplementation(() => {});
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  describe("auth", () => {
    it("returns null for currentUser", () => {
      expect(FirebaseService.auth.currentUser).toBeNull();
    });

    it("signInAnonymously returns resolved promise with null user", async () => {
      const result = await FirebaseService.auth.signInAnonymously();
      expect(result).toEqual({ user: null });
    });

    it("signOut returns resolved promise", async () => {
      await expect(FirebaseService.auth.signOut()).resolves.toBeUndefined();
    });
  });

  describe("firestore", () => {
    it("provides stub collection and doc methods", async () => {
      const doc = FirebaseService.firestore.collection("test").doc("123");

      const getResult = await doc.get();
      expect(getResult).toEqual({ exists: false });

      await expect(doc.set({})).resolves.toBeUndefined();
    });
  });

  describe("analytics", () => {
    it("logs events to console", async () => {
      const consoleSpy = jest.spyOn(console, "log");

      await FirebaseService.analytics.logEvent("test_event", {
        param: "value",
      });

      expect(consoleSpy).toHaveBeenCalledWith("Analytics event: test_event", {
        param: "value",
      });
    });
  });

  describe("crashlytics", () => {
    it("logs errors to console", async () => {
      const consoleSpy = jest.spyOn(console, "error");
      const error = new Error("Test error");

      await FirebaseService.crashlytics.recordError(error);

      expect(consoleSpy).toHaveBeenCalledWith("Crashlytics stub:", error);
    });

    it("setAttribute resolves without error", async () => {
      await expect(
        FirebaseService.crashlytics.setAttribute(),
      ).resolves.toBeUndefined();
    });
  });

  describe("remoteConfig", () => {
    it("returns default string value", () => {
      const value = FirebaseService.remoteConfig.getValue("test").asString();
      expect(value).toBe("default");
    });

    it("setDefaults resolves without error", async () => {
      await expect(
        FirebaseService.remoteConfig.setDefaults(),
      ).resolves.toBeUndefined();
    });

    it("fetchAndActivate resolves to true", async () => {
      await expect(
        FirebaseService.remoteConfig.fetchAndActivate(),
      ).resolves.toBe(true);
    });
  });

  describe("initRemoteConfig", () => {
    it("logs to console and resolves", async () => {
      const consoleSpy = jest.spyOn(console, "log");

      await FirebaseService.initRemoteConfig();

      expect(consoleSpy).toHaveBeenCalledWith(
        "Firebase RemoteConfig stub: initialized",
      );
    });
  });

  describe("logError", () => {
    it("logs Error object with context", () => {
      const consoleSpy = jest.spyOn(console, "error");
      const error = new Error("Test error");
      const context = { source: "test" };

      FirebaseService.logError(error, context);

      expect(consoleSpy).toHaveBeenCalledWith(
        "Firebase error log:",
        error,
        context,
      );
    });

    it("converts non-Error to Error object", () => {
      const consoleSpy = jest.spyOn(console, "error");
      const errorString = "string error";

      FirebaseService.logError(errorString);

      expect(consoleSpy).toHaveBeenCalledWith(
        "Firebase error log:",
        expect.any(Error),
        undefined,
      );
      expect(consoleSpy.mock.calls[0][1].message).toBe("string error");
    });
  });
});
