const path = require("path");

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: false,
  outputFileTracingRoot: path.resolve(__dirname),
  generateBuildId: async () => {
    return "sentinel-ai-build";
  },
  turbopack: {},
  webpack: (config) => {
    config.optimization.moduleIds = "deterministic";
    return config;
  },
};

module.exports = nextConfig;
