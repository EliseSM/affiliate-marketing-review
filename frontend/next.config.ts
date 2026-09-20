import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Hides the on-screen dev-mode route indicator (the bottom-left badge).
  // Next.js still surfaces compile/runtime errors without it.
  devIndicators: false,
};

export default nextConfig;
