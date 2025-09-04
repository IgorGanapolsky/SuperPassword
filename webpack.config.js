const createExpoWebpackConfigAsync = require("@expo/webpack-config");
const path = require("path");

module.exports = async function (env, argv) {
  const config = await createExpoWebpackConfigAsync(env, argv);

  // Customize the config before returning it.
  config.resolve.alias = {
    ...config.resolve.alias,
    // Add your aliases here
    "@": path.resolve(__dirname, "src"),
  };

  // PWA settings
  config.plugins.push(
    new WorkboxWebpackPlugin.GenerateSW({
      clientsClaim: true,
      skipWaiting: true,
      maximumFileSizeToCacheInBytes: 5 * 1024 * 1024, // 5MB
      runtimeCaching: [
        {
          urlPattern: /\.(png|jpg|jpeg|gif|svg)$/,
          handler: "CacheFirst",
          options: {
            cacheName: "images",
            expiration: {
              maxEntries: 50,
              maxAgeSeconds: 30 * 24 * 60 * 60, // 30 days
            },
          },
        },
        {
          urlPattern: /api/,
          handler: "NetworkFirst",
          options: {
            cacheName: "api-cache",
            networkTimeoutSeconds: 10,
            expiration: {
              maxEntries: 100,
              maxAgeSeconds: 24 * 60 * 60, // 24 hours
            },
          },
        },
      ],
    }),
  );

  return config;
};
