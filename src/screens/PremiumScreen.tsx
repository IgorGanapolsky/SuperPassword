import { MaterialCommunityIcons } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  Platform,
  Animated,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { spacing, borderRadius, fontSize, shadows } from "@/constants/theme";
import { useTheme } from "@/contexts/ThemeContext";
import { StorageService } from "@/services/storage";

interface Feature {
  icon: string;
  title: string;
  description: string;
  free: boolean;
  premium: boolean;
}

const features: Feature[] = [
  {
    icon: "history",
    title: "Password History",
    description: "Save your generated passwords",
    free: true,
    premium: true,
  },
  {
    icon: "infinity",
    title: "Unlimited History",
    description: "Save unlimited passwords (vs 10)",
    free: false,
    premium: true,
  },
  {
    icon: "cloud-sync",
    title: "Cloud Sync",
    description: "Sync across all your devices",
    free: false,
    premium: true,
  },
  {
    icon: "tune",
    title: "Custom Character Sets",
    description: "Create your own character rules",
    free: false,
    premium: true,
  },
  {
    icon: "content-copy",
    title: "Bulk Generation",
    description: "Generate up to 100 passwords at once",
    free: false,
    premium: true,
  },
  {
    icon: "file-export",
    title: "CSV Export",
    description: "Export passwords to spreadsheet",
    free: false,
    premium: true,
  },
  {
    icon: "shield-lock",
    title: "Advanced Security",
    description: "Extra security settings & encryption",
    free: false,
    premium: true,
  },
  {
    icon: "ad",
    title: "No Advertisements",
    description: "Remove all ads permanently",
    free: false,
    premium: true,
  },
  {
    icon: "star",
    title: "Priority Support",
    description: "24/7 premium customer support",
    free: false,
    premium: true,
  },
];

export const PremiumScreen: React.FC = () => {
  const { theme } = useTheme();
  const [isPremium, setIsPremium] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedPrice] = useState("2.99");
  const scaleAnimation = new Animated.Value(1);

  useEffect(() => {
    checkPremiumStatus();
    startPulseAnimation();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const checkPremiumStatus = async () => {
    const status = await StorageService.getPremiumStatus();
    setIsPremium(status);
  };

  const startPulseAnimation = () => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(scaleAnimation, {
          toValue: 1.05,
          duration: 1000,
          useNativeDriver: true,
        }),
        Animated.timing(scaleAnimation, {
          toValue: 1,
          duration: 1000,
          useNativeDriver: true,
        }),
      ]),
    ).start();
  };

  const handlePurchase = async () => {
    setIsLoading(true);
    if (Platform.OS === "ios") {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    }

    // Simulate purchase process
    setTimeout(() => {
      Alert.alert(
        "Purchase Premium",
        `Unlock all premium features for just $${selectedPrice}`,
        [
          { text: "Cancel", style: "cancel" },
          {
            text: "Purchase",
            onPress: async () => {
              // In production, this would trigger the actual IAP flow
              Alert.alert(
                "Success!",
                "Premium features unlocked! Thank you for your support.",
                [{ text: "OK" }],
              );
              await StorageService.setPremiumStatus(true);
              setIsPremium(true);
            },
          },
        ],
      );
      setIsLoading(false);
    }, 500);
  };

  const handleRestore = async () => {
    setIsLoading(true);
    // In production, this would restore purchases from the app store
    setTimeout(() => {
      Alert.alert(
        "Restore Purchases",
        "No previous purchases found. Would you like to upgrade to premium?",
        [
          { text: "Cancel", style: "cancel" },
          { text: "Upgrade", onPress: handlePurchase },
        ],
      );
      setIsLoading(false);
    }, 1000);
  };

  const handleWatchAd = () => {
    Alert.alert(
      "Watch Ad for Trial",
      "Watch a video ad to unlock premium features for 24 hours!",
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Watch Ad",
          onPress: () => {
            // In production, this would show a rewarded video ad
            Alert.alert(
              "Trial Activated!",
              "Premium features unlocked for 24 hours.",
            );
          },
        },
      ],
    );
  };

  const styles = StyleSheet.create({
    container: {
      flex: 1,
      backgroundColor: theme.background,
    },
    gradient: {
      paddingVertical: spacing.xl,
      alignItems: "center",
    },
    header: {
      alignItems: "center",
      marginBottom: spacing.lg,
    },
    crown: {
      marginBottom: spacing.md,
    },
    title: {
      fontSize: fontSize.xxxl,
      fontWeight: "bold",
      color: "#fff",
      marginBottom: spacing.xs,
    },
    subtitle: {
      fontSize: fontSize.lg,
      color: "rgba(255, 255, 255, 0.9)",
    },
    scrollView: {
      flex: 1,
    },
    content: {
      padding: spacing.lg,
    },
    priceCard: {
      backgroundColor: theme.surface,
      borderRadius: borderRadius.xl,
      padding: spacing.lg,
      marginBottom: spacing.lg,
      alignItems: "center",
      ...shadows.lg,
    },
    priceLabel: {
      fontSize: fontSize.sm,
      color: theme.textSecondary,
      marginBottom: spacing.xs,
    },
    priceAmount: {
      fontSize: 48,
      fontWeight: "bold",
      color: theme.primary,
    },
    priceCurrency: {
      fontSize: fontSize.xl,
      color: theme.primary,
    },
    priceDescription: {
      fontSize: fontSize.md,
      color: theme.text,
      marginTop: spacing.xs,
    },
    featuresContainer: {
      marginBottom: spacing.lg,
    },
    sectionTitle: {
      fontSize: fontSize.xl,
      fontWeight: "bold",
      color: theme.text,
      marginBottom: spacing.md,
    },
    featureItem: {
      flexDirection: "row",
      alignItems: "center",
      backgroundColor: theme.surface,
      padding: spacing.md,
      marginBottom: spacing.sm,
      borderRadius: borderRadius.md,
      ...shadows.sm,
    },
    featureIcon: {
      width: 40,
      alignItems: "center",
    },
    featureContent: {
      flex: 1,
      marginLeft: spacing.md,
    },
    featureTitle: {
      fontSize: fontSize.md,
      fontWeight: "600",
      color: theme.text,
    },
    featureDescription: {
      fontSize: fontSize.sm,
      color: theme.textSecondary,
      marginTop: 2,
    },
    checkmark: {
      marginLeft: spacing.sm,
    },
    purchaseButton: {
      backgroundColor: theme.primary,
      borderRadius: borderRadius.lg,
      padding: spacing.lg,
      alignItems: "center",
      marginBottom: spacing.md,
      ...shadows.lg,
    },
    purchaseButtonText: {
      color: "#fff",
      fontSize: fontSize.lg,
      fontWeight: "bold",
    },
    trialButton: {
      backgroundColor: theme.accent,
      borderRadius: borderRadius.lg,
      padding: spacing.md,
      alignItems: "center",
      marginBottom: spacing.md,
    },
    trialButtonText: {
      color: "#fff",
      fontSize: fontSize.md,
      fontWeight: "600",
    },
    restoreButton: {
      padding: spacing.md,
      alignItems: "center",
    },
    restoreButtonText: {
      color: theme.primary,
      fontSize: fontSize.md,
      fontWeight: "600",
    },
    premiumBadge: {
      backgroundColor: theme.success,
      paddingHorizontal: spacing.lg,
      paddingVertical: spacing.md,
      borderRadius: borderRadius.lg,
      marginBottom: spacing.lg,
    },
    premiumBadgeText: {
      color: "#fff",
      fontSize: fontSize.lg,
      fontWeight: "bold",
    },
    guarantee: {
      backgroundColor: theme.info + "20",
      padding: spacing.md,
      borderRadius: borderRadius.md,
      marginTop: spacing.lg,
      alignItems: "center",
    },
    guaranteeText: {
      color: theme.info,
      fontSize: fontSize.sm,
      textAlign: "center",
    },
  });

  if (isPremium) {
    return (
      <SafeAreaView style={styles.container}>
        <LinearGradient
          colors={[theme.gradient.start, theme.gradient.end]}
          style={styles.gradient}
        >
          <View style={styles.header}>
            <MaterialCommunityIcons name="crown" size={64} color="#FFD700" />
            <Text style={styles.title}>Premium Active</Text>
            <Text style={styles.subtitle}>
              Thank you for supporting SecurePass!
            </Text>
          </View>
        </LinearGradient>

        <ScrollView
          style={styles.scrollView}
          contentContainerStyle={styles.content}
        >
          <View style={styles.premiumBadge}>
            <Text style={styles.premiumBadgeText}>
              ✨ All Features Unlocked
            </Text>
          </View>

          <Text style={styles.sectionTitle}>Your Premium Benefits</Text>
          {features
            .filter((f) => f.premium && !f.free)
            .map((feature, index) => (
              <View key={index} style={styles.featureItem}>
                <View style={styles.featureIcon}>
                  <MaterialCommunityIcons
                    name={feature.icon as any}
                    size={24}
                    color={theme.success}
                  />
                </View>
                <View style={styles.featureContent}>
                  <Text style={styles.featureTitle}>{feature.title}</Text>
                  <Text style={styles.featureDescription}>
                    {feature.description}
                  </Text>
                </View>
                <MaterialCommunityIcons
                  name="check-circle"
                  size={24}
                  color={theme.success}
                />
              </View>
            ))}
        </ScrollView>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <LinearGradient
        colors={[theme.gradient.start, theme.gradient.end]}
        style={styles.gradient}
      >
        <View style={styles.header}>
          <Animated.View
            style={[styles.crown, { transform: [{ scale: scaleAnimation }] }]}
          >
            <MaterialCommunityIcons name="crown" size={64} color="#FFD700" />
          </Animated.View>
          <Text style={styles.title}>Go Premium</Text>
          <Text style={styles.subtitle}>Unlock all features forever</Text>
        </View>
      </LinearGradient>

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.content}
      >
        <View style={styles.priceCard}>
          <Text style={styles.priceLabel}>ONE-TIME PURCHASE</Text>
          <Text style={styles.priceAmount}>
            <Text style={styles.priceCurrency}>$</Text>
            {selectedPrice}
          </Text>
          <Text style={styles.priceDescription}>Pay once, use forever</Text>
        </View>

        <View style={styles.featuresContainer}>
          <Text style={styles.sectionTitle}>Compare Features</Text>
          {features.map((feature, index) => (
            <View key={index} style={styles.featureItem}>
              <View style={styles.featureIcon}>
                <MaterialCommunityIcons
                  name={feature.icon as any}
                  size={24}
                  color={feature.premium ? theme.primary : theme.textSecondary}
                />
              </View>
              <View style={styles.featureContent}>
                <Text
                  style={[
                    styles.featureTitle,
                    !feature.premium && { color: theme.textSecondary },
                  ]}
                >
                  {feature.title}
                </Text>
                <Text style={styles.featureDescription}>
                  {feature.description}
                </Text>
              </View>
              {feature.free && (
                <MaterialCommunityIcons
                  name="check"
                  size={20}
                  color={theme.textSecondary}
                  style={styles.checkmark}
                />
              )}
              {feature.premium && (
                <MaterialCommunityIcons
                  name="check-circle"
                  size={20}
                  color={theme.primary}
                  style={styles.checkmark}
                />
              )}
            </View>
          ))}
        </View>

        <TouchableOpacity
          style={styles.purchaseButton}
          onPress={handlePurchase}
          disabled={isLoading}
          activeOpacity={0.8}
        >
          <Text style={styles.purchaseButtonText}>
            {isLoading ? "Processing..." : "Unlock Premium - $2.99"}
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.trialButton}
          onPress={handleWatchAd}
          activeOpacity={0.8}
        >
          <Text style={styles.trialButtonText}>
            🎬 Watch Ad for 24-Hour Trial
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.restoreButton}
          onPress={handleRestore}
          disabled={isLoading}
        >
          <Text style={styles.restoreButtonText}>Restore Purchases</Text>
        </TouchableOpacity>

        <View style={styles.guarantee}>
          <Text style={styles.guaranteeText}>
            🔒 Secure payment via App Store / Google Play{"\n"}
            30-day money-back guarantee
          </Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};
