import { MaterialCommunityIcons } from "@expo/vector-icons";
import * as Application from "expo-application";
import * as Device from "expo-device";
import * as Haptics from "expo-haptics";
import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Switch,
  Alert,
  Platform,
  Linking,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { spacing, borderRadius, fontSize, shadows } from "@/constants/theme";
import { useTheme, ThemeMode } from "@/contexts/ThemeContext";
import { StorageService } from "@/services/storage";
import { UserPreferences } from "@/types";

export const SettingsScreen: React.FC = () => {
  const { theme, themeMode, toggleTheme } = useTheme();
  const [preferences, setPreferences] = useState<UserPreferences | null>(null);
  const [isPremium, setIsPremium] = useState(false);

  useEffect(() => {
    loadPreferences();
    checkPremiumStatus();
  }, []);

  const loadPreferences = async () => {
    const prefs = await StorageService.getUserPreferences();
    setPreferences(prefs);
  };

  const checkPremiumStatus = async () => {
    const status = await StorageService.getPremiumStatus();
    setIsPremium(status);
  };

  const updatePreference = async (key: keyof UserPreferences, value: UserPreferences[keyof UserPreferences]) => {
    if (!preferences) return;

    const updatedPreferences = { ...preferences, [key]: value };
    setPreferences(updatedPreferences);
    await StorageService.saveUserPreferences(updatedPreferences);

    if (Platform.OS === "ios" && preferences.hapticFeedback) {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    }
  };

  const handleThemeChange = (mode: ThemeMode) => {
    toggleTheme(mode);
    if (Platform.OS === "ios" && preferences?.hapticFeedback) {
      Haptics.selectionAsync();
    }
  };

  const handleClearData = () => {
    Alert.alert(
      "Clear All Data",
      "This will delete all your password history and reset settings. This action cannot be undone.",
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Clear",
          style: "destructive",
          onPress: async () => {
            await StorageService.clearAllData();
            await loadPreferences();
            Alert.alert("Success", "All data has been cleared.");
          },
        },
      ],
    );
  };

  const handleExportData = async () => {
    try {
      await StorageService.exportData();
      // In a real app, you would share this data or save it to a file
      Alert.alert("Export Ready", "Your data has been prepared for export.");
    } catch (error) {
      Alert.alert("Error", "Failed to export data.");
    }
  };

  const openPrivacyPolicy = () => {
    Linking.openURL("https://securepass.app/privacy");
  };

  const openTermsOfService = () => {
    Linking.openURL("https://securepass.app/terms");
  };

  const openSupport = () => {
    Linking.openURL("mailto:support@securepass.app");
  };

  const rateApp = () => {
    if (Platform.OS === "ios") {
      Linking.openURL("https://apps.apple.com/app/id1234567890");
    } else {
      Linking.openURL(
        "https://play.google.com/store/apps/details?id=com.securepass.generator",
      );
    }
  };

  const styles = StyleSheet.create({
    container: {
      flex: 1,
      backgroundColor: theme.background,
    },
    header: {
      padding: spacing.lg,
      borderBottomWidth: 1,
      borderBottomColor: theme.divider,
    },
    title: {
      fontSize: fontSize.xxl,
      fontWeight: "bold",
      color: theme.text,
    },
    scrollView: {
      flex: 1,
    },
    section: {
      marginTop: spacing.lg,
      marginHorizontal: spacing.md,
      backgroundColor: theme.surface,
      borderRadius: borderRadius.lg,
      ...shadows.sm,
    },
    sectionHeader: {
      paddingHorizontal: spacing.md,
      paddingVertical: spacing.sm,
      borderBottomWidth: 1,
      borderBottomColor: theme.divider,
    },
    sectionTitle: {
      fontSize: fontSize.md,
      fontWeight: "600",
      color: theme.primary,
    },
    settingRow: {
      flexDirection: "row",
      justifyContent: "space-between",
      alignItems: "center",
      paddingHorizontal: spacing.md,
      paddingVertical: spacing.md,
      borderBottomWidth: 1,
      borderBottomColor: theme.divider,
    },
    settingRowLast: {
      borderBottomWidth: 0,
    },
    settingLabel: {
      fontSize: fontSize.md,
      color: theme.text,
      flex: 1,
    },
    settingDescription: {
      fontSize: fontSize.sm,
      color: theme.textSecondary,
      marginTop: spacing.xs,
    },
    themeSelector: {
      marginTop: spacing.sm,
    },
    themeOptions: {
      flexDirection: "row",
      justifyContent: "space-around",
      paddingVertical: spacing.sm,
    },
    themeOption: {
      alignItems: "center",
      padding: spacing.sm,
      borderRadius: borderRadius.md,
      minWidth: 80,
    },
    themeOptionActive: {
      backgroundColor: theme.primary + "20",
    },
    themeOptionText: {
      fontSize: fontSize.sm,
      color: theme.text,
      marginTop: spacing.xs,
    },
    dangerButton: {
      backgroundColor: theme.error,
      marginHorizontal: spacing.md,
      marginVertical: spacing.md,
      padding: spacing.md,
      borderRadius: borderRadius.md,
      alignItems: "center",
    },
    dangerButtonText: {
      color: "#fff",
      fontSize: fontSize.md,
      fontWeight: "600",
    },
    premiumBadge: {
      backgroundColor: theme.accent,
      paddingHorizontal: spacing.sm,
      paddingVertical: spacing.xs,
      borderRadius: borderRadius.md,
    },
    premiumText: {
      color: "#fff",
      fontSize: fontSize.xs,
      fontWeight: "600",
    },
    versionInfo: {
      padding: spacing.lg,
      alignItems: "center",
    },
    versionText: {
      fontSize: fontSize.sm,
      color: theme.textSecondary,
    },
  });

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Settings</Text>
      </View>

      <ScrollView style={styles.scrollView}>
        {/* Appearance Section */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Appearance</Text>
          </View>

          <View style={styles.settingRow}>
            <View style={{ flex: 1 }}>
              <Text style={styles.settingLabel}>Theme</Text>
              <View style={styles.themeSelector}>
                <View style={styles.themeOptions}>
                  <TouchableOpacity
                    style={[
                      styles.themeOption,
                      themeMode === "light" && styles.themeOptionActive,
                    ]}
                    onPress={() => handleThemeChange("light")}
                  >
                    <MaterialCommunityIcons
                      name="weather-sunny"
                      size={24}
                      color={theme.text}
                    />
                    <Text style={styles.themeOptionText}>Light</Text>
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={[
                      styles.themeOption,
                      themeMode === "dark" && styles.themeOptionActive,
                    ]}
                    onPress={() => handleThemeChange("dark")}
                  >
                    <MaterialCommunityIcons
                      name="weather-night"
                      size={24}
                      color={theme.text}
                    />
                    <Text style={styles.themeOptionText}>Dark</Text>
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={[
                      styles.themeOption,
                      themeMode === "system" && styles.themeOptionActive,
                    ]}
                    onPress={() => handleThemeChange("system")}
                  >
                    <MaterialCommunityIcons
                      name="cellphone"
                      size={24}
                      color={theme.text}
                    />
                    <Text style={styles.themeOptionText}>System</Text>
                  </TouchableOpacity>
                </View>
              </View>
            </View>
          </View>
        </View>

        {/* Preferences Section */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Preferences</Text>
          </View>

          <View style={styles.settingRow}>
            <View style={{ flex: 1 }}>
              <Text style={styles.settingLabel}>Haptic Feedback</Text>
              <Text style={styles.settingDescription}>
                Vibration on interactions
              </Text>
            </View>
            <Switch
              value={preferences?.hapticFeedback ?? true}
              onValueChange={(value) =>
                updatePreference("hapticFeedback", value)
              }
              trackColor={{ true: theme.primary }}
            />
          </View>

          <View style={styles.settingRow}>
            <View style={{ flex: 1 }}>
              <Text style={styles.settingLabel}>Auto-Save Passwords</Text>
              <Text style={styles.settingDescription}>
                Automatically save to history
              </Text>
            </View>
            <Switch
              value={preferences?.autoSave ?? true}
              onValueChange={(value) => updatePreference("autoSave", value)}
              trackColor={{ true: theme.primary }}
            />
          </View>

          <View style={styles.settingRow}>
            <View style={{ flex: 1 }}>
              <Text style={styles.settingLabel}>Show Strength Meter</Text>
              <Text style={styles.settingDescription}>
                Display password strength indicator
              </Text>
            </View>
            <Switch
              value={preferences?.showPasswordStrength ?? true}
              onValueChange={(value) =>
                updatePreference("showPasswordStrength", value)
              }
              trackColor={{ true: theme.primary }}
            />
          </View>

          <View style={[styles.settingRow, styles.settingRowLast]}>
            <View style={{ flex: 1 }}>
              <Text style={styles.settingLabel}>Quick Copy</Text>
              <Text style={styles.settingDescription}>
                Copy password with single tap
              </Text>
            </View>
            <Switch
              value={preferences?.quickCopyEnabled ?? true}
              onValueChange={(value) =>
                updatePreference("quickCopyEnabled", value)
              }
              trackColor={{ true: theme.primary }}
            />
          </View>
        </View>

        {/* Data Management Section */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Data Management</Text>
          </View>

          <TouchableOpacity
            style={styles.settingRow}
            onPress={handleExportData}
          >
            <Text style={styles.settingLabel}>Export Data</Text>
            <MaterialCommunityIcons
              name="download"
              size={20}
              color={theme.textSecondary}
            />
          </TouchableOpacity>

          {isPremium && (
            <TouchableOpacity
              style={[styles.settingRow, styles.settingRowLast]}
              onPress={() =>
                Alert.alert(
                  "Cloud Sync",
                  "Cloud sync is enabled for premium users.",
                )
              }
            >
              <Text style={styles.settingLabel}>Cloud Sync</Text>
              <View style={styles.premiumBadge}>
                <Text style={styles.premiumText}>PREMIUM</Text>
              </View>
            </TouchableOpacity>
          )}
        </View>

        {/* Support Section */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Support</Text>
          </View>

          <TouchableOpacity style={styles.settingRow} onPress={rateApp}>
            <Text style={styles.settingLabel}>Rate SecurePass</Text>
            <MaterialCommunityIcons
              name="star"
              size={20}
              color={theme.textSecondary}
            />
          </TouchableOpacity>

          <TouchableOpacity style={styles.settingRow} onPress={openSupport}>
            <Text style={styles.settingLabel}>Contact Support</Text>
            <MaterialCommunityIcons
              name="email"
              size={20}
              color={theme.textSecondary}
            />
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.settingRow}
            onPress={openPrivacyPolicy}
          >
            <Text style={styles.settingLabel}>Privacy Policy</Text>
            <MaterialCommunityIcons
              name="shield-check"
              size={20}
              color={theme.textSecondary}
            />
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.settingRow, styles.settingRowLast]}
            onPress={openTermsOfService}
          >
            <Text style={styles.settingLabel}>Terms of Service</Text>
            <MaterialCommunityIcons
              name="file-document"
              size={20}
              color={theme.textSecondary}
            />
          </TouchableOpacity>
        </View>

        {/* Danger Zone */}
        <TouchableOpacity style={styles.dangerButton} onPress={handleClearData}>
          <Text style={styles.dangerButtonText}>Clear All Data</Text>
        </TouchableOpacity>

        {/* Version Info */}
        <View style={styles.versionInfo}>
          <Text style={styles.versionText}>
            SecurePass v{Application.nativeApplicationVersion || "1.0.0"}
          </Text>
          <Text style={styles.versionText}>
            {Device.modelName} • {Device.osName} {Device.osVersion}
          </Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};
