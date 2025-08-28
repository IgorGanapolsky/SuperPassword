import { MaterialCommunityIcons } from "@expo/vector-icons";
import React from "react";
import { View, Text, StyleSheet, TouchableOpacity } from "react-native";

interface ErrorFallbackProps {
  error: Error;
  resetError: () => void;
}

export const ErrorFallback: React.FC<ErrorFallbackProps> = ({
  error,
  resetError,
}) => {
  return (
    <View style={styles.container}>
      <MaterialCommunityIcons name="alert-circle" size={64} color="#dc2626" />
      <Text style={styles.title}>Oops! Something went wrong</Text>
      <Text style={styles.message}>
        We apologize for the inconvenience. The error has been reported and
        we&apos;ll fix it soon.
      </Text>
      {__DEV__ && (
        <View style={styles.errorDetails}>
          <Text style={styles.errorTitle}>Error details (dev only):</Text>
          <Text style={styles.errorMessage}>{error.message}</Text>
        </View>
      )}
      <TouchableOpacity style={styles.button} onPress={resetError}>
        <Text style={styles.buttonText}>Try Again</Text>
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    padding: 20,
    backgroundColor: "#f8f9fa",
  },
  title: {
    fontSize: 24,
    fontWeight: "bold",
    color: "#1f2937",
    marginTop: 16,
    marginBottom: 8,
  },
  message: {
    fontSize: 16,
    color: "#6b7280",
    textAlign: "center",
    marginBottom: 24,
  },
  errorDetails: {
    backgroundColor: "#fee2e2",
    padding: 12,
    borderRadius: 8,
    marginBottom: 24,
    maxWidth: "90%",
  },
  errorTitle: {
    fontSize: 14,
    fontWeight: "bold",
    color: "#991b1b",
    marginBottom: 4,
  },
  errorMessage: {
    fontSize: 12,
    color: "#dc2626",
    fontFamily: "monospace",
  },
  button: {
    backgroundColor: "#667eea",
    paddingVertical: 12,
    paddingHorizontal: 32,
    borderRadius: 8,
  },
  buttonText: {
    color: "#ffffff",
    fontSize: 16,
    fontWeight: "600",
  },
});
