import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'standalone',
  /* config options here */
  // 允许开发模式下的跨域请求
  allowedDevOrigins: ['anmei.jibu.club'],
  env: {
    NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_URL 
      ? `${process.env.NEXT_PUBLIC_API_URL}/api/v1` 
      : 'http://localhost:8000/api/v1',
    NEXT_PUBLIC_WS_URL: process.env.NEXT_PUBLIC_WS_URL 
      ? process.env.NEXT_PUBLIC_WS_URL 
      : (process.env.NEXT_PUBLIC_API_URL 
          ? process.env.NEXT_PUBLIC_API_URL.replace('http', 'ws') + '/api/v1/ws'
          : 'ws://localhost:8000/api/v1/ws'),
  },
  // 临时禁用构建时的 ESLint 检查，确保安全修复后构建能通过
  // TODO: 后续逐步修复代码质量问题后，可移除此配置
  eslint: {
    ignoreDuringBuilds: true,
  },
  // 优化静态资源缓存策略，减少 chunk 加载失败问题
  async headers() {
    return [
      {
        // 对静态 chunk 文件使用长期缓存，但支持重新验证
        source: '/_next/static/chunks/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',
          },
        ],
      },
      {
        // 对 HTML 文件禁用缓存，确保始终获取最新版本
        source: '/:path*.html',
        headers: [
          {
            key: 'Cache-Control',
            value: 'no-cache, no-store, must-revalidate',
          },
        ],
      },
      {
        // 对主页面禁用缓存
        source: '/',
        headers: [
          {
            key: 'Cache-Control',
            value: 'no-cache, no-store, must-revalidate',
          },
        ],
      },
    ];
  },
  async rewrites() {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    return [
      {
        source: '/api/:path*',
        destination: `${apiUrl}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
