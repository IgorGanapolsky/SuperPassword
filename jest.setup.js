// Mock expo modules
jest.mock("expo-constants", () => ({
  default: {
    expoConfig: {
      name: "SuperPassword",
      slug: "superpassword",
    },
  },
}));

// Mock AsyncStorage
jest.mock("@react-native-async-storage/async-storage", () => ({
  setItem: jest.fn(),
  getItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
  getAllKeys: jest.fn(),
  flushGetRequests: jest.fn(),
}));

// Mock Reanimated
global.__reanimatedWorkletInit = jest.fn();
jest.mock("react-native-reanimated", () =>
  require("react-native-reanimated/mock"),
);

// Mock expo modules
jest.mock("expo-font");
jest.mock("expo-status-bar", () => ({
  StatusBar: () => "StatusBar",
}));

// Mock device info
jest.mock("expo-device", () => ({
  isDevice: true,
  brand: "Apple",
  manufacturer: "Apple",
  modelName: "iPhone 12",
  osName: "iOS",
  osVersion: "14.5",
}));

// Mock Animated
jest.mock("react-native/Libraries/Animated/NativeAnimatedHelper");

// Mock clipboard
jest.mock("expo-clipboard", () => ({
  setStringAsync: jest.fn(),
  getStringAsync: jest.fn(),
}));

// Mock haptics
jest.mock("expo-haptics", () => ({
  selectionAsync: jest.fn(),
  impactAsync: jest.fn(),
  notificationAsync: jest.fn(),
}));
