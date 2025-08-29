import { MaterialCommunityIcons } from "@expo/vector-icons";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import { NavigationContainer } from "@react-navigation/native";
import { createStackNavigator } from "@react-navigation/stack";
import React from "react";
import { Platform } from "react-native";

import { useTheme } from "@/contexts/ThemeContext";
import { HistoryScreen } from "@/screens/HistoryScreen";
import { HomeScreen } from "@/screens/HomeScreen";
import { PremiumScreen } from "@/screens/PremiumScreen";
import { SettingsScreen } from "@/screens/SettingsScreen";
import { BottomTabParamList, RootStackParamList } from "@/types";

const Tab = createBottomTabNavigator<BottomTabParamList>();
const Stack = createStackNavigator<RootStackParamList>();

const TabNavigator: React.FC = () => {
  const { theme } = useTheme();

  return (
    <Tab.Navigator
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: theme.primary,
        tabBarInactiveTintColor: theme.textSecondary,
        tabBarStyle: {
          backgroundColor: theme.surface,
          borderTopColor: theme.divider,
          borderTopWidth: 1,
        },
        tabBarLabelStyle: {
          fontSize: 12,
          fontWeight: "600",
        },
      }}
    >
      <Tab.Screen
        name="Home"
        component={HomeScreen}
        options={{
          tabBarLabel: "Generate",
          tabBarIcon: ({ color, size }) => (
            <MaterialCommunityIcons
              name="key-variant"
              size={size}
              color={color}
            />
          ),
        }}
      />
      <Tab.Screen
        name="History"
        component={HistoryScreen}
        options={{
          tabBarLabel: "History",
          tabBarIcon: ({ color, size }) => (
            <MaterialCommunityIcons name="history" size={size} color={color} />
          ),
        }}
      />
      <Tab.Screen
        name="Settings"
        component={SettingsScreen}
        options={{
          tabBarLabel: "Settings",
          tabBarIcon: ({ color, size }) => (
            <MaterialCommunityIcons name="cog" size={size} color={color} />
          ),
        }}
      />
      <Tab.Screen
        name="Premium"
        component={PremiumScreen}
        options={{
          tabBarLabel: "Premium",
          tabBarIcon: ({ color, size }) => (
            <MaterialCommunityIcons name="crown" size={size} color={color} />
          ),
        }}
      />
    </Tab.Navigator>
  );
};

export const AppNavigator: React.FC = () => {
  const { theme } = useTheme();

  return (
    <NavigationContainer
      documentTitle={{
        formatter: (options, route) =>
          Platform.OS === 'web' ? `${options?.title ?? route?.name} - SuperPassword` : undefined,
      }}
    >
      <Stack.Navigator
        screenOptions={{
          headerShown: false,
          cardStyle: { backgroundColor: theme.background },
        }}
      >
        <Stack.Screen name="MainTabs" component={TabNavigator} />
      </Stack.Navigator>
    </NavigationContainer>
  );
};
