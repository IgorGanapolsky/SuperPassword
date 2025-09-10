import { MaterialCommunityIcons } from "@expo/vector-icons";
import { format } from "date-fns";
import * as Clipboard from "expo-clipboard";
import * as Haptics from "expo-haptics";
import React, { useState, useEffect, useCallback } from "react";
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  Alert,
  RefreshControl,
  Platform,
} from "react-native";
import { Swipeable } from "react-native-gesture-handler";
import { SafeAreaView } from "react-native-safe-area-context";

import {
  spacing,
  borderRadius,
  fontSize,
  shadows,
  passwordStrengthColors,
} from "@/constants/theme";
import { useTheme } from "@/contexts/ThemeContext";
import { StorageService } from "@/services/storage";
import { PasswordEntry } from "@/types";
import { getPasswordStrengthLabel } from "@/utils/passwordGenerator";

export const HistoryScreen: React.FC = () => {
  const { theme } = useTheme();
  const [history, setHistory] = useState<PasswordEntry[]>([]);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isPremium, setIsPremium] = useState(false);

  useEffect(() => {
    loadHistory();
    checkPremiumStatus();
  }, []);

  const checkPremiumStatus = async () => {
    const status = await StorageService.getPremiumStatus();
    setIsPremium(status);
  };

  const loadHistory = async () => {
    const data = await StorageService.getPasswordHistory();
    setHistory(data);
  };

  const handleRefresh = useCallback(async () => {
    setIsRefreshing(true);
    await loadHistory();
    setIsRefreshing(false);
  }, []);

  const handleCopyPassword = async (password: string) => {
    await Clipboard.setStringAsync(password);
    if (Platform.OS === "ios") {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    }
    Alert.alert("Copied!", "Password copied to clipboard");
  };

  const handleDeletePassword = (id: string) => {
    Alert.alert(
      "Delete Password",
      "Are you sure you want to delete this password from history?",
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Delete",
          style: "destructive",
          onPress: async () => {
            await StorageService.removePasswordFromHistory(id);
            await loadHistory();
            if (Platform.OS === "ios") {
              Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
            }
          },
        },
      ],
    );
  };

  const handleClearHistory = () => {
    Alert.alert(
      "Clear History",
      "Are you sure you want to clear all password history?",
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Clear All",
          style: "destructive",
          onPress: async () => {
            await StorageService.clearPasswordHistory();
            setHistory([]);
            if (Platform.OS === "ios") {
              Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy);
            }
          },
        },
      ],
    );
  };

  const renderRightActions = (id: string) => {
    return (
      <TouchableOpacity
        style={[styles.deleteButton, { backgroundColor: theme.error }]}
        onPress={() => handleDeletePassword(id)}
      >
        <MaterialCommunityIcons name="delete" size={24} color="#fff" />
      </TouchableOpacity>
    );
  };

  const renderPasswordItem = ({ item }: { item: PasswordEntry }) => {
    const strengthColor = passwordStrengthColors[item.strength];

    return (
      <Swipeable renderRightActions={() => renderRightActions(item.id)}>
        <View style={[styles.passwordItem, { backgroundColor: theme.surface }]}>
          <View style={styles.passwordHeader}>
            <View style={styles.strengthIndicator}>
              <View
                style={[styles.strengthDot, { backgroundColor: strengthColor }]}
              />
              <Text
                style={[styles.strengthText, { color: theme.textSecondary }]}
              >
                {getPasswordStrengthLabel(item.strength)}
              </Text>
            </View>
            <Text style={[styles.timestamp, { color: theme.textSecondary }]}>
              {format(new Date(item.timestamp), "MMM dd, HH:mm")}
            </Text>
          </View>

          <TouchableOpacity
            onPress={() => handleCopyPassword(item.password)}
            activeOpacity={0.7}
          >
            <Text
              style={[styles.password, { color: theme.text }]}
              numberOfLines={1}
            >
              {item.password}
            </Text>
          </TouchableOpacity>

          <View style={styles.passwordFooter}>
            <Text style={[styles.optionText, { color: theme.textSecondary }]}>
              Length: {item.options.length}
            </Text>
            <View style={styles.optionIcons}>
              {item.options.includeUppercase && (
                <MaterialCommunityIcons
                  name="alphabetical"
                  size={16}
                  color={theme.textSecondary}
                />
              )}
              {item.options.includeNumbers && (
                <MaterialCommunityIcons
                  name="numeric"
                  size={16}
                  color={theme.textSecondary}
                />
              )}
              {item.options.includeSymbols && (
                <MaterialCommunityIcons
                  name="code-tags"
                  size={16}
                  color={theme.textSecondary}
                />
              )}
            </View>
          </View>
        </View>
      </Swipeable>
    );
  };

  const renderEmptyState = () => (
    <View style={styles.emptyState}>
      <MaterialCommunityIcons
        name="history"
        size={64}
        color={theme.textSecondary}
      />
      <Text style={[styles.emptyTitle, { color: theme.text }]}>
        No Password History
      </Text>
      <Text style={[styles.emptySubtitle, { color: theme.textSecondary }]}>
        Generated passwords will appear here
      </Text>
    </View>
  );

  const renderHeader = () => (
    <View style={[styles.header, { backgroundColor: theme.background }]}>
      <View style={styles.headerContent}>
        <Text style={[styles.title, { color: theme.text }]}>History</Text>
        {!isPremium && (
          <View style={[styles.limitBadge, { backgroundColor: theme.warning }]}>
            <Text style={styles.limitText}>
              {history.length}/10 (Free Plan)
            </Text>
          </View>
        )}
      </View>
      {history.length > 0 && (
        <TouchableOpacity onPress={handleClearHistory}>
          <Text style={[styles.clearButton, { color: theme.error }]}>
            Clear All
          </Text>
        </TouchableOpacity>
      )}
    </View>
  );

  const styles = StyleSheet.create({
    container: {
      flex: 1,
      backgroundColor: theme.background,
    },
    header: {
      flexDirection: "row",
      justifyContent: "space-between",
      alignItems: "center",
      padding: spacing.lg,
      borderBottomWidth: 1,
      borderBottomColor: theme.divider,
    },
    headerContent: {
      flexDirection: "row",
      alignItems: "center",
    },
    title: {
      fontSize: fontSize.xxl,
      fontWeight: "bold",
    },
    limitBadge: {
      marginLeft: spacing.md,
      paddingHorizontal: spacing.sm,
      paddingVertical: spacing.xs,
      borderRadius: borderRadius.md,
    },
    limitText: {
      color: "#fff",
      fontSize: fontSize.xs,
      fontWeight: "600",
    },
    clearButton: {
      fontSize: fontSize.md,
      fontWeight: "600",
    },
    passwordItem: {
      padding: spacing.md,
      marginHorizontal: spacing.md,
      marginVertical: spacing.xs,
      borderRadius: borderRadius.md,
      ...shadows.sm,
    },
    passwordHeader: {
      flexDirection: "row",
      justifyContent: "space-between",
      alignItems: "center",
      marginBottom: spacing.sm,
    },
    strengthIndicator: {
      flexDirection: "row",
      alignItems: "center",
    },
    strengthDot: {
      width: 8,
      height: 8,
      borderRadius: 4,
      marginRight: spacing.xs,
    },
    strengthText: {
      fontSize: fontSize.sm,
      fontWeight: "500",
    },
    timestamp: {
      fontSize: fontSize.xs,
    },
    password: {
      fontSize: fontSize.md,
      fontFamily: Platform.OS === "ios" ? "Menlo" : "monospace",
      marginBottom: spacing.sm,
    },
    passwordFooter: {
      flexDirection: "row",
      justifyContent: "space-between",
      alignItems: "center",
    },
    optionText: {
      fontSize: fontSize.sm,
    },
    optionIcons: {
      flexDirection: "row",
      gap: spacing.xs,
    },
    deleteButton: {
      justifyContent: "center",
      alignItems: "center",
      width: 80,
      marginVertical: spacing.xs,
      marginRight: spacing.md,
      borderRadius: borderRadius.md,
    },
    emptyState: {
      flex: 1,
      justifyContent: "center",
      alignItems: "center",
      padding: spacing.xl,
    },
    emptyTitle: {
      fontSize: fontSize.xl,
      fontWeight: "600",
      marginTop: spacing.md,
    },
    emptySubtitle: {
      fontSize: fontSize.md,
      marginTop: spacing.xs,
      textAlign: "center",
    },
  });

  return (
    <SafeAreaView style={styles.container}>
      {renderHeader()}
      <FlatList
        data={history}
        keyExtractor={(item) => item.id}
        renderItem={renderPasswordItem}
        ListEmptyComponent={renderEmptyState}
        refreshControl={
          <RefreshControl
            refreshing={isRefreshing}
            onRefresh={handleRefresh}
            tintColor={theme.primary}
          />
        }
        contentContainerStyle={history.length === 0 ? { flex: 1 } : undefined}
      />
    </SafeAreaView>
  );
};
