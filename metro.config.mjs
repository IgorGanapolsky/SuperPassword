import { getDefaultConfig } from "expo/metro-config";
import { createRequire } from "module";
import { fileURLToPath } from "url";
import path from "path";

const require = createRequire(import.meta.url);
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/** @type {import('expo/metro-config').MetroConfig} */
const config = getDefaultConfig(__dirname);

// Ensure proper module resolution
config.resolver = {
  ...config.resolver,
  // Add tslib to extra node modules to ensure it's resolved correctly
  extraNodeModules: {
    ...config.resolver.extraNodeModules,
    tslib: require.resolve("tslib"),
  },
};

// Ensure source map support for better debugging
config.transformer = {
  ...config.transformer,
  minifierConfig: {
    keep_fnames: true,
    mangle: {
      keep_fnames: true,
    },
  },
};

export default config;
