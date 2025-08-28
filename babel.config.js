module.exports = function (api) {
  api.cache(true);
  return {
    presets: [
      [
        "babel-preset-expo",
        {
          jsxImportSource: "react",
        },
      ],
    ],
    plugins: [
      // Ensure TypeScript helpers are properly imported
      ["@babel/plugin-transform-runtime", { helpers: true }],
      [
        "module-resolver",
        {
          root: ["."],
          extensions: [
            ".ios.ts",
            ".android.ts",
            ".ts",
            ".ios.tsx",
            ".android.tsx",
            ".tsx",
            ".jsx",
            ".js",
            ".json",
          ],
          alias: {
            "@": "./src",
            "@/components": "./src/components",
            "@/screens": "./src/screens",
            "@/contexts": "./src/contexts",
            "@/services": "./src/services",
            "@/utils": "./src/utils",
            "@/constants": "./src/constants",
            "@/navigation": "./src/navigation",
            "@/hooks": "./src/hooks",
            "@/types": "./src/types",
            "@/store": "./src/store",
            "@/config": "./src/config",
          },
        },
      ],
      "react-native-reanimated/plugin",
    ],
  };
};
