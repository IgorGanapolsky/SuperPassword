// Mock expo modules
jest.mock('expo-constants', () => ({
  default: {
    expoConfig: {
      name: 'SuperPassword',
      slug: 'superpassword',
    },
  },
}));

// Mock AsyncStorage
jest.mock('@react-native-async-storage/async-storage', () => ({
  setItem: jest.fn(),
  getItem: jest.fn(),
  removeItem: jest.fn(),
}));
