import React from "react";
import { View, Text, TouchableOpacity, StyleSheet, Alert } from "react-native";

import {
  captureException,
  captureMessage,
  isSentryInitialized,
} from "@/services/sentry";

export const SentryTest: React.FC = () => {
  const handleTestError = () => {
    try {
      // This will throw an error
      throw new Error(
        "Test error from SuperPassword app - Please ignore this test error!",
      );
    } catch (error) {
      captureException(error);
      Alert.alert(
        "Test Error Sent",
        "A test error has been sent to Sentry. Check your dashboard!",
      );
    }
  };

  const handleTestMessage = () => {
    captureMessage("Test message from SuperPassword app", "info");
    Alert.alert("Test Message Sent", "A test message has been sent to Sentry.");
  };

  const isInitialized = isSentryInitialized();

  if (!__DEV__) {
    return null; // Only show in development
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Sentry Debug Panel</Text>
      <Text style={styles.status}>
        Status: {isInitialized ? "✅ Initialized" : "❌ Not Initialized"}
      </Text>

      <TouchableOpacity
        style={[styles.button, !isInitialized && styles.buttonDisabled]}
        onPress={handleTestError}
        disabled={!isInitialized}
      >
        <Text style={styles.buttonText}>Send Test Error</Text>
      </TouchableOpacity>

      <TouchableOpacity
        style={[
          styles.button,
          styles.buttonInfo,
          !isInitialized && styles.buttonDisabled,
        ]}
        onPress={handleTestMessage}
        disabled={!isInitialized}
      >
        <Text style={styles.buttonText}>Send Test Message</Text>
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    padding: 16,
    backgroundColor: "#f0f0f0",
    borderRadius: 8,
    margin: 16,
  },
  title: {
    fontSize: 16,
    fontWeight: "bold",
    marginBottom: 8,
  },
  status: {
    fontSize: 14,
    marginBottom: 12,
  },
  button: {
    backgroundColor: "#dc2626",
    padding: 12,
    borderRadius: 6,
    marginBottom: 8,
    alignItems: "center",
  },
  buttonInfo: {
    backgroundColor: "#2563eb",
  },
  buttonDisabled: {
    backgroundColor: "#9ca3af",
  },
  buttonText: {
    color: "#ffffff",
    fontWeight: "600",
  },
});
