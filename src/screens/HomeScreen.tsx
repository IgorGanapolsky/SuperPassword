import { MaterialCommunityIcons } from "@expo/vector-icons";
import Slider from "@react-native-community/slider";
import * as Clipboard from "expo-clipboard";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import React, { useState, useEffect, useCallback, useRef } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Animated,
  Alert,
  Platform,
  Vibration,
} from "react-native";
import { Switch } from "react-native-paper";
import { SafeAreaView } from "react-native-safe-area-context";

import {
  spacing,
  borderRadius,
  fontSize,
  shadows,
  passwordStrengthColors,
} from "@/constants/theme";
import { useTheme } from "@/contexts/ThemeContext";
import { Banner } from "@/services/ads";
import { StorageService } from "@/services/storage";
import { PasswordOptions, PasswordEntry, PasswordStrength } from "@/types";
import {
  generatePassword,
  calculatePasswordStrength,
  getPasswordStrengthLabel,
  estimateCrackTime,
  validatePasswordOptions,
} from "@/utils/passwordGenerator";

export const HomeScreen: React.FC = () => {
  const { theme, isDark } = useTheme();
  const copyAnimationValue = useRef(new Animated.Value(0)).current;
  const scaleAnimation = useRef(new Animated.Value(1)).current;

  const [password, setPassword] = useState("");
  const [passwordStrength, setPasswordStrength] = useState<PasswordStrength>(
    PasswordStrength.VeryWeak,
  );
  const [options, setOptions] = useState<PasswordOptions>({
    length: 16,
    includeUppercase: true,
    includeLowercase: true,
    includeNumbers: true,
    includeSymbols: true,
    excludeAmbiguous: false,
    customCharacters: "",
    excludeCharacters: "",
  });
  const [isPremium, setIsPremium] = useState(false);
  const [generationCount, setGenerationCount] = useState(0);
  const [showCopiedAnimation, setShowCopiedAnimation] = useState(false);

  // Load user preferences and premium status
  useEffect(() => {
    loadUserPreferences();
    checkPremiumStatus();
  }, []);

  const loadUserPreferences = async () => {
    const preferences = await StorageService.getUserPreferences();
    if (preferences?.defaultOptions) {
      setOptions(preferences.defaultOptions);
    }
    // Generate initial password
    handleGeneratePassword(preferences?.defaultOptions || options);
  };

  const checkPremiumStatus = async () => {
    const status = await StorageService.getPremiumStatus();
    setIsPremium(status);
  };

  const handleGeneratePassword = useCallback(
    (currentOptions?: PasswordOptions) => {
      const opts = currentOptions || options;

      if (!validatePasswordOptions(opts)) {
        Alert.alert(
          "Invalid Options",
          "Please select at least one character type.",
        );
        return;
      }

      const newPassword = generatePassword(opts);
      const strength = calculatePasswordStrength(newPassword);

      setPassword(newPassword);
      setPasswordStrength(strength);
      setGenerationCount((prev) => prev + 1);

      // Haptic feedback
      if (Platform.OS === "ios") {
        Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
      } else {
        Vibration.vibrate(50);
      }

      // Animate generate button
      Animated.sequence([
        Animated.timing(scaleAnimation, {
          toValue: 0.95,
          duration: 100,
          useNativeDriver: true,
        }),
        Animated.timing(scaleAnimation, {
          toValue: 1,
          duration: 100,
          useNativeDriver: true,
        }),
      ]).start();

      // Save to history
      saveToHistory(newPassword, strength, opts);
    },
    [options],
  );

  const saveToHistory = async (
    pwd: string,
    strength: PasswordStrength,
    opts: PasswordOptions,
  ) => {
    const entry: PasswordEntry = {
      id: Date.now().toString(),
      password: pwd,
      timestamp: new Date(),
      strength,
      options: opts,
    };

    const maxCount = isPremium ? 999999 : 10;
    await StorageService.addPasswordToHistory(entry, maxCount);
  };

  const handleCopyToClipboard = async () => {
    if (!password) return;

    await Clipboard.setStringAsync(password);

    // Haptic feedback
    if (Platform.OS === "ios") {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    } else {
      Vibration.vibrate([0, 50, 100, 50]);
    }

    // Show copied animation
    setShowCopiedAnimation(true);
    Animated.sequence([
      Animated.timing(copyAnimationValue, {
        toValue: 1,
        duration: 300,
        useNativeDriver: true,
      }),
      Animated.delay(1000),
      Animated.timing(copyAnimationValue, {
        toValue: 0,
        duration: 300,
        useNativeDriver: true,
      }),
    ]).start(() => {
      setShowCopiedAnimation(false);
    });
  };

  const updateOption = (key: keyof PasswordOptions, value: any) => {
    const newOptions = { ...options, [key]: value };
    setOptions(newOptions);

    // Auto-generate on option change
    if (password) {
      handleGeneratePassword(newOptions);
    }
  };

  const styles = StyleSheet.create({
    container: {
      flex: 1,
    },
    gradient: {
      flex: 1,
    },
    scrollView: {
      flex: 1,
    },
    content: {
      padding: spacing.lg,
    },
    header: {
      alignItems: "center",
      marginBottom: spacing.xl,
    },
    title: {
      fontSize: fontSize.xxxl,
      fontWeight: "bold",
      color: "#fff",
      marginTop: spacing.md,
    },
    subtitle: {
      fontSize: fontSize.md,
      color: "rgba(255, 255, 255, 0.8)",
      marginTop: spacing.xs,
    },
    passwordContainer: {
      backgroundColor: theme.surface,
      borderRadius: borderRadius.lg,
      padding: spacing.lg,
      marginBottom: spacing.lg,
      ...shadows.lg,
    },
    passwordText: {
      fontSize: fontSize.xl,
      fontFamily: Platform.OS === "ios" ? "Menlo" : "monospace",
      color: theme.text,
      textAlign: "center",
      marginBottom: spacing.md,
    },
    passwordActions: {
      flexDirection: "row",
      justifyContent: "space-around",
    },
    actionButton: {
      flexDirection: "row",
      alignItems: "center",
      backgroundColor: theme.primary,
      paddingHorizontal: spacing.md,
      paddingVertical: spacing.sm,
      borderRadius: borderRadius.md,
    },
    actionButtonText: {
      color: "#fff",
      marginLeft: spacing.xs,
      fontSize: fontSize.md,
      fontWeight: "600",
    },
    strengthContainer: {
      marginTop: spacing.md,
      padding: spacing.md,
      backgroundColor: isDark ? theme.background : "#f8f9fa",
      borderRadius: borderRadius.md,
    },
    strengthBar: {
      height: 8,
      backgroundColor: isDark ? theme.surface : "#e9ecef",
      borderRadius: borderRadius.sm,
      overflow: "hidden",
      marginBottom: spacing.sm,
    },
    strengthFill: {
      height: "100%",
      borderRadius: borderRadius.sm,
    },
    strengthInfo: {
      flexDirection: "row",
      justifyContent: "space-between",
    },
    strengthLabel: {
      fontSize: fontSize.sm,
      fontWeight: "600",
    },
    crackTime: {
      fontSize: fontSize.sm,
      color: theme.textSecondary,
    },
    optionsContainer: {
      backgroundColor: theme.surface,
      borderRadius: borderRadius.lg,
      padding: spacing.lg,
      marginBottom: spacing.lg,
      ...shadows.md,
    },
    optionRow: {
      flexDirection: "row",
      justifyContent: "space-between",
      alignItems: "center",
      marginBottom: spacing.md,
    },
    optionLabel: {
      fontSize: fontSize.md,
      color: theme.text,
    },
    sliderContainer: {
      marginBottom: spacing.lg,
    },
    sliderHeader: {
      flexDirection: "row",
      justifyContent: "space-between",
      marginBottom: spacing.sm,
    },
    sliderLabel: {
      fontSize: fontSize.md,
      color: theme.text,
      fontWeight: "600",
    },
    sliderValue: {
      fontSize: fontSize.md,
      color: theme.primary,
      fontWeight: "bold",
    },
    slider: {
      width: "100%",
      height: 40,
    },
    generateButton: {
      backgroundColor: theme.accent,
      borderRadius: borderRadius.lg,
      padding: spacing.lg,
      alignItems: "center",
      marginBottom: spacing.lg,
      ...shadows.lg,
    },
    generateButtonText: {
      color: "#fff",
      fontSize: fontSize.xl,
      fontWeight: "bold",
    },
    copiedBadge: {
      position: "absolute",
      top: -30,
      alignSelf: "center",
      backgroundColor: theme.success,
      paddingHorizontal: spacing.md,
      paddingVertical: spacing.xs,
      borderRadius: borderRadius.md,
    },
    copiedText: {
      color: "#fff",
      fontSize: fontSize.sm,
      fontWeight: "600",
    },
  });

  return (
    <LinearGradient
      colors={[theme.gradient.start, theme.gradient.end]}
      style={styles.gradient}
      start={{ x: 0, y: 0 }}
      end={{ x: 1, y: 1 }}
    >
      <SafeAreaView style={styles.container}>
        <ScrollView
          style={styles.scrollView}
          contentContainerStyle={styles.content}
        >
          <View style={styles.header}>
            <MaterialCommunityIcons name="shield-key" size={64} color="#fff" />
            <Text style={styles.title}>SecurePass</Text>
            <Text style={styles.subtitle}>Generate Strong Passwords</Text>
          </View>

          <View style={styles.passwordContainer}>
            <Text style={styles.passwordText} selectable>
              {password || "Press Generate to create a password"}
            </Text>

            {password && (
              <>
                <View style={styles.strengthContainer}>
                  <View style={styles.strengthBar}>
                    <Animated.View
                      style={[
                        styles.strengthFill,
                        {
                          width: `${((passwordStrength + 1) / 6) * 100}%`,
                          backgroundColor:
                            passwordStrengthColors[passwordStrength],
                        },
                      ]}
                    />
                  </View>
                  <View style={styles.strengthInfo}>
                    <Text
                      style={[
                        styles.strengthLabel,
                        { color: passwordStrengthColors[passwordStrength] },
                      ]}
                    >
                      {getPasswordStrengthLabel(passwordStrength)}
                    </Text>
                    <Text style={styles.crackTime}>
                      Time to crack: {estimateCrackTime(password)}
                    </Text>
                  </View>
                </View>

                <View style={styles.passwordActions}>
                  <TouchableOpacity
                    style={styles.actionButton}
                    onPress={handleCopyToClipboard}
                    activeOpacity={0.8}
                  >
                    <MaterialCommunityIcons
                      name="content-copy"
                      size={20}
                      color="#fff"
                    />
                    <Text style={styles.actionButtonText}>Copy</Text>
                  </TouchableOpacity>

                  {showCopiedAnimation && (
                    <Animated.View
                      style={[
                        styles.copiedBadge,
                        {
                          opacity: copyAnimationValue,
                          transform: [
                            {
                              translateY: copyAnimationValue.interpolate({
                                inputRange: [0, 1],
                                outputRange: [10, 0],
                              }),
                            },
                          ],
                        },
                      ]}
                    >
                      <Text style={styles.copiedText}>Copied!</Text>
                    </Animated.View>
                  )}
                </View>
              </>
            )}
          </View>

          <View style={styles.optionsContainer}>
            <View style={{ marginBottom: spacing.lg }}>
              <Banner />
            </View>
            <View style={styles.sliderContainer}>
              <View style={styles.sliderHeader}>
                <Text style={styles.sliderLabel}>Password Length</Text>
                <Text style={styles.sliderValue}>{options.length}</Text>
              </View>
              <Slider
                style={styles.slider}
                minimumValue={8}
                maximumValue={50}
                step={1}
                value={options.length}
                onValueChange={(value) =>
                  updateOption("length", Math.round(value))
                }
                minimumTrackTintColor={theme.primary}
                maximumTrackTintColor={theme.divider}
                thumbTintColor={theme.accent}
              />
            </View>

            <View style={styles.optionRow}>
              <Text style={styles.optionLabel}>Uppercase (A-Z)</Text>
              <Switch
                value={options.includeUppercase}
                onValueChange={(value) =>
                  updateOption("includeUppercase", value)
                }
                color={theme.primary}
              />
            </View>

            <View style={styles.optionRow}>
              <Text style={styles.optionLabel}>Lowercase (a-z)</Text>
              <Switch
                value={options.includeLowercase}
                onValueChange={(value) =>
                  updateOption("includeLowercase", value)
                }
                color={theme.primary}
              />
            </View>

            <View style={styles.optionRow}>
              <Text style={styles.optionLabel}>Numbers (0-9)</Text>
              <Switch
                value={options.includeNumbers}
                onValueChange={(value) => updateOption("includeNumbers", value)}
                color={theme.primary}
              />
            </View>

            <View style={styles.optionRow}>
              <Text style={styles.optionLabel}>Symbols (!@#$%)</Text>
              <Switch
                value={options.includeSymbols}
                onValueChange={(value) => updateOption("includeSymbols", value)}
                color={theme.primary}
              />
            </View>

            <View style={styles.optionRow}>
              <Text style={styles.optionLabel}>Exclude Ambiguous</Text>
              <Switch
                value={options.excludeAmbiguous}
                onValueChange={(value) =>
                  updateOption("excludeAmbiguous", value)
                }
                color={theme.primary}
              />
            </View>
          </View>

          <Animated.View style={{ transform: [{ scale: scaleAnimation }] }}>
            <TouchableOpacity
              style={styles.generateButton}
              onPress={() => handleGeneratePassword()}
              activeOpacity={0.8}
            >
              <Text style={styles.generateButtonText}>Generate Password</Text>
            </TouchableOpacity>
          </Animated.View>
        </ScrollView>
      </SafeAreaView>
    </LinearGradient>
  );
};
