/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://bedrock-gateway-alb-664380835.us-east-1.elb.amazonaws.com/api/:path*",
      },
      {
        source: "/v1/:path*",
        destination: "http://bedrock-gateway-alb-664380835.us-east-1.elb.amazonaws.com/v1/:path*",
      },
    ];
  },
};

module.exports = nextConfig;
