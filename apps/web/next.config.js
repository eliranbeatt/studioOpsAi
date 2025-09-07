/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable RTL support
  i18n: {
    locales: ['he'],
    defaultLocale: 'he',
  },
  // API proxy for development
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/:path*',
      },
    ]
  },
}

module.exports = nextConfig