import React from "react";
import { Platform } from "react-native";
import mobileAds, {
  BannerAd,
  BannerAdSize,
  InterstitialAd,
  TestIds,
} from "react-native-google-mobile-ads";

const isDev = __DEV__;

const ANDROID_BANNER = isDev ? TestIds.BANNER : "ca-app-pub-XXXX/YYYY";
const IOS_BANNER = isDev ? TestIds.BANNER : "ca-app-pub-XXXX/ZZZZ";
const ANDROID_INTERSTITIAL = isDev
  ? TestIds.INTERSTITIAL
  : "ca-app-pub-XXXX/IIII";
const IOS_INTERSTITIAL = isDev ? TestIds.INTERSTITIAL : "ca-app-pub-XXXX/JJJJ";

export const AdsService = {
  async initialize() {
    await mobileAds().initialize();
  },
  createInterstitial() {
    const adUnitId = Platform.select({
      android: ANDROID_INTERSTITIAL,
      ios: IOS_INTERSTITIAL,
    }) as string;
    return InterstitialAd.createForAdRequest(adUnitId);
  },
};

export const Banner: React.FC = () => {
  const adUnitId = Platform.select({
    android: ANDROID_BANNER,
    ios: IOS_BANNER,
  }) as string;
  return (
    <BannerAd unitId={adUnitId} size={BannerAdSize.ANCHORED_ADAPTIVE_BANNER} />
  );
};
