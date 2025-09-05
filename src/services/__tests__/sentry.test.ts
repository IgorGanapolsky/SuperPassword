import * as Sentry from "sentry-expo";
import {
  initializeSentry,
  captureException,
  captureMessage,
  addBreadcrumb,
  isSentryInitialized,
} from "../sentry";

jest.mock("sentry-expo", () => ({
  init: jest.fn(),
  Native: {
    captureException: jest.fn(),
    captureMessage: jest.fn(),
    addBreadcrumb: jest.fn(),
    ErrorBoundary: jest.fn(),
  },
}));

jest.mock("expo-constants", () => ({
  default: {
    expoConfig: {
      extra: {
        SENTRY_DSN: "test-dsn",
      },
    },
  },
}));

describe("Sentry Service", () => {
  // Reset modules before each test to ensure clean state
  beforeEach(() => {
    jest.resetModules();
    jest.clearAllMocks();
  });
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("initializeSentry", () => {
    it("initializes Sentry", async () => {
      jest.isolateModules(async () => {
        const { initializeSentry } = require("../sentry");
        const ok = await initializeSentry();
        expect(ok).toBe(true);
        expect(Sentry.init).toHaveBeenCalled();
      });
    });

    it("does not reinitialize when already initialized", async () => {
      jest.isolateModules(async () => {
        const { initializeSentry } = require("../sentry");
        await initializeSentry();
        await initializeSentry();
        expect(Sentry.init).toHaveBeenCalledTimes(1);
      });
    });
  });

  describe("captureException", () => {
    it("captures exception when initialized", async () => {
      jest.isolateModules(async () => {
        const { initializeSentry, captureException } = require("../sentry");
        await initializeSentry();
        const error = new Error("Test error");
        captureException(error);
        expect(Sentry.Native.captureException).toHaveBeenCalledWith(error);
      });
    });

    it("does not send to Sentry when not initialized", async () => {
      jest.isolateModules(() => {
        const { captureException } = require("../sentry");
        const error = new Error("Test error");
        captureException(error);
        expect(Sentry.Native.captureException).not.toHaveBeenCalled();
      });
    });
  });

  describe("captureMessage", () => {
    it("captures message with specified level when initialized", async () => {
      await initializeSentry();
      captureMessage("Test message", "error");

      expect(Sentry.Native.captureMessage).toHaveBeenCalledWith(
        "Test message",
        {
          level: "error",
        },
      );
    });

    it("uses info level by default when initialized", async () => {
      await initializeSentry();
      captureMessage("Test message");

      expect(Sentry.Native.captureMessage).toHaveBeenCalledWith(
        "Test message",
        {
          level: "info",
        },
      );
    });

    it("does not send to Sentry when not initialized", () => {
      jest.isolateModules(() => {
        const { captureMessage } = require("../sentry");
        captureMessage("Test message", "warning");
        expect(Sentry.Native.captureMessage).not.toHaveBeenCalled();
      });
    });
  });

  describe("addBreadcrumb", () => {
    it("adds breadcrumb when initialized", async () => {
      await initializeSentry();
      addBreadcrumb("Test breadcrumb", "auth");

      expect(Sentry.Native.addBreadcrumb).toHaveBeenCalledWith({
        message: "Test breadcrumb",
        category: "auth",
      });
    });

    it("uses custom category by default when initialized", async () => {
      await initializeSentry();
      addBreadcrumb("Test breadcrumb");

      expect(Sentry.Native.addBreadcrumb).toHaveBeenCalledWith({
        message: "Test breadcrumb",
        category: "custom",
      });
    });

    it("does not send breadcrumb when not initialized", () => {
      jest.isolateModules(() => {
        const { addBreadcrumb } = require("../sentry");
        addBreadcrumb("Test breadcrumb", "navigation");
        expect(Sentry.Native.addBreadcrumb).not.toHaveBeenCalled();
      });
    });
  });

  describe("isSentryInitialized", () => {
    it("returns false by default and true after init", async () => {
      jest.isolateModules(async () => {
        const { isSentryInitialized, initializeSentry } = require("../sentry");
        expect(isSentryInitialized()).toBe(false);
        await initializeSentry();
        expect(isSentryInitialized()).toBe(true);
      });
    });
  });
});
