import React from "react";
import { View, Text } from "react-native";

// Stub implementation for ads - replace when adding back react-native-google-mobile-ads
export const AdsService = {
  async initialize() {
    console.log("Ads service stub: initialize called");
    return Promise.resolve();
  },
  createInterstitial() {
    console.log("Ads service stub: createInterstitial called");
    return {
      load: () => Promise.resolve(),
      show: () => Promise.resolve(),
      addListener: () => ({ remove: () => {} }),
    };
  },
};

export const Banner: React.FC = () => {
  if (__DEV__) {
    return (
      <View style={{ padding: 10, backgroundColor: "#f0f0f0" }}>
        <Text style={{ textAlign: "center", color: "#666" }}>
          Ad Banner Placeholder
        </Text>
      </View>
    );
  }
  return null;
};
