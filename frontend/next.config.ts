import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // Low CPU and memory footprint for fanless Mac Air M4
  experimental: {
    cpus: 1,
  },
};

export default nextConfig;
