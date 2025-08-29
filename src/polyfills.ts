// Web platform polyfills

// Mock the expo-font module for web
if (!global.FontFace) {
  global.FontFace = class FontFace {
    constructor() {
      // Mock implementation
    }
    load() {
      return Promise.resolve();
    }
  };
}

// Add other web-specific polyfills here
export default {};
