/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  // Standalone output enables the Docker multi-stage build to copy only what's needed
  output: 'standalone',
  images: {
    domains: [],
  },
}

module.exports = nextConfig
