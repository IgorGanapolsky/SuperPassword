const { getDefaultConfig } = require("expo/metro-config");
const path = require('path');

/** @type {import('expo/metro-config').MetroConfig} */
const config = getDefaultConfig(__dirname, {
  // Enable CSS support
  isCSSEnabled: true,
});

// Configure caching
config.cacheStores = [
  {
    name: 'local',
    path: path.join(__dirname, '.metro-cache'),
  },
];

// Ensure proper module resolution
config.resolver = {
  ...config.resolver,
  // Add tslib to extra node modules to ensure it's resolved correctly
  extraNodeModules: {
    ...config.resolver.extraNodeModules,
    tslib: require.resolve("tslib"),
  },
};

// Configure build optimization
config.transformer = {
  ...config.transformer,
  hermesParser: true,
  minifierPath: 'metro-minify-terser',
  minifierConfig: {
    compress: {
      reduce_funcs: true,
      passes: 2,
      drop_console: process.env.APP_ENV === 'production',
    },
    mangle: {
      toplevel: true,
      keep_classnames: process.env.APP_ENV !== 'production',
      keep_fnames: process.env.APP_ENV !== 'production',
    },
    output: {
      ascii_only: true,
      quote_style: 1,
      wrap_iife: true,
    },
    sourceMap: process.env.APP_ENV !== 'production',
  },
  transformVariants: {
    development: {
      minify: false,
      dev: true,
    },
    production: {
      minify: true,
      dev: false,
    },
  },
};

module.exports = config;
