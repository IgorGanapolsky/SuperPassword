const globals = require("globals");
const js = require("@eslint/js");
const tsPlugin = require("@typescript-eslint/eslint-plugin");
const tsParser = require("@typescript-eslint/parser");
const reactPlugin = require("eslint-plugin-react");
const reactHooksPlugin = require("eslint-plugin-react-hooks");
const reactNativePlugin = require("eslint-plugin-react-native");
const importPlugin = require("eslint-plugin-import");
const unusedImportsPlugin = require("eslint-plugin-unused-imports");

module.exports = [
  // Global ignores
  {
    ignores: [
      "node_modules/",
      "dist/",
      "build/",
      ".expo/",
      ".expo-shared/",
      "android/",
      "ios/",
      "web-build/",
      "coverage/",
      "babel.config.js",
      "metro.config.js",
      "jest.config.js",
      "jest.setup.js",
      "webpack.config.js",
      ".eslintrc.cjs",
      ".eslintrc.js",
    ],
  },

  // Base recommended configs
  js.configs.recommended,

  // TypeScript files (React Native App)
  {
    files: ["src/**/*.{ts,tsx}"],
    languageOptions: {
      parser: tsParser,
      parserOptions: {
        ecmaFeatures: { jsx: true },
        ecmaVersion: "latest",
        sourceType: "module",
        project: "./tsconfig.json",
      },
      globals: {
        ...globals.browser,
        ...globals.node,
        ...globals.es2021,
        "__DEV__": "readonly",
      },
    },
    plugins: {
      "@typescript-eslint": tsPlugin,
      react: reactPlugin,
      "react-hooks": reactHooksPlugin,
      "react-native": reactNativePlugin,
      "unused-imports": unusedImportsPlugin,
      import: importPlugin,
    },
    rules: {
      ...reactPlugin.configs.recommended.rules,
      ...reactHooksPlugin.configs.recommended.rules,
      "no-unused-vars": "off",
      "@typescript-eslint/no-unused-vars": ["warn", { "argsIgnorePattern": "^_" }],
      "react/react-in-jsx-scope": "off",
      "react-native/no-inline-styles": "off",
      "react-native/sort-styles": "off",
      "react-native/no-raw-text": "off",
      "react-native/no-color-literals": "off",
      "react-native/no-unused-styles": "warn",
      "@typescript-eslint/no-explicit-any": "warn",
      "unused-imports/no-unused-imports": "error",
      "import/namespace": "off",
      "import/order": [
        "warn",
        {
          "newlines-between": "always",
          groups: [
            ["builtin", "external"],
            ["internal"],
            ["parent", "sibling", "index"],
          ],
          pathGroups: [{ pattern: "@/**", group: "internal", position: "after" }],
          pathGroupsExcludedImportTypes: ["builtin"],
          alphabetize: { order: "asc", caseInsensitive: true },
        },
      ],
    },
    settings: {
      react: { version: "detect" },
      "import/resolver": {
        typescript: {},
      },
    },
  },

  // Jest (Test files)
  {
    files: ["src/**/*.test.{ts,tsx}", "src/**/__tests__/**", "jest.setup.js"],
    languageOptions: {
      globals: {
        ...globals.jest,
      },
    },
  },

  // Node.js config files
  {
    files: ["*.js", "*.cjs", "scripts/**/*.js", "scripts/**/*.mjs", ".github/scripts/**/*.mjs"],
    languageOptions: {
      globals: {
        ...globals.node,
      },
    },
    rules: {
      "no-unused-vars": ["error", { "varsIgnorePattern": "^_" , "argsIgnorePattern": "^_" }],
    }
  },
];