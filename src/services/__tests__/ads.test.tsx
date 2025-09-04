import React from "react";
import { render } from "@testing-library/react-native";
import { AdsService, Banner } from "../ads";

describe("AdsService", () => {
  beforeEach(() => {
    jest.spyOn(console, "log").mockImplementation(() => {});
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  describe("initialize", () => {
    it("logs to console and resolves", async () => {
      const consoleSpy = jest.spyOn(console, "log");

      await AdsService.initialize();

      expect(consoleSpy).toHaveBeenCalledWith(
        "Ads service stub: initialize called",
      );
    });
  });

  describe("createInterstitial", () => {
    it("returns interstitial stub with required methods", () => {
      const consoleSpy = jest.spyOn(console, "log");
      const interstitial = AdsService.createInterstitial();

      expect(consoleSpy).toHaveBeenCalledWith(
        "Ads service stub: createInterstitial called",
      );
      expect(interstitial).toHaveProperty("load");
      expect(interstitial).toHaveProperty("show");
      expect(interstitial).toHaveProperty("addListener");
    });

    it("interstitial load resolves", async () => {
      const interstitial = AdsService.createInterstitial();
      await expect(interstitial.load()).resolves.toBeUndefined();
    });

    it("interstitial show resolves", async () => {
      const interstitial = AdsService.createInterstitial();
      await expect(interstitial.show()).resolves.toBeUndefined();
    });

    it("interstitial addListener returns removable listener", () => {
      const interstitial = AdsService.createInterstitial();
      const listener = interstitial.addListener();

      expect(listener).toHaveProperty("remove");
      expect(() => listener.remove()).not.toThrow();
    });
  });
});

describe("Banner", () => {
  const originalDev = global.__DEV__;

  afterEach(() => {
    global.__DEV__ = originalDev;
  });

  it("renders placeholder in development", () => {
    global.__DEV__ = true;
    const { getByText } = render(<Banner />);
    expect(getByText("Ad Banner Placeholder")).toBeTruthy();
  });

  it("renders nothing in production", () => {
    global.__DEV__ = false;
    const { container } = render(<Banner />);
    expect(container.children.length).toBe(0);
  });
});
