import React from "react";
import { View, Text } from "react-native";

// Web-specific ads implementation
export const AdsService = {
  async initialize() {
    return Promise.resolve();
  },
  createInterstitial() {
    return {
      load: () => Promise.resolve(),
      show: () => Promise.resolve(),
      addListener: () => ({ remove: () => {} }),
    };
  },
};

export const Banner: React.FC = () => {
  return null; // No ads on web version
};
