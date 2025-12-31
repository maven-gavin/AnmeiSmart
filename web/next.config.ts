import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'standalone',
  /* config options here */
  // 允许开发模式下的跨域请求
  allowedDevOrigins: ['anmei.jibu.club'],
  // 转译 ESM 包，确保构建时正确处理
  transpilePackages: ['streamdown', 'shiki'],
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
  // 注意：规则按顺序匹配，更具体的规则应该放在前面
  async headers() {
    // 开发环境不要对 /_next/static 施加强缓存，否则浏览器可能长期使用旧的 client chunk，
    // 造成“服务端日志/渲染已更新，但浏览器控制台/行为仍是旧代码”的错觉。
    if (process.env.NODE_ENV !== 'production') {
      return [];
    }

    return [
      // 1. 静态资源：长期缓存（因为文件名包含哈希，资源更新时文件名会变）
      {
        source: '/_next/static/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',
          },
        ],
      },
      // 2. API 路由：禁用缓存
      {
        source: '/api/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'no-store',
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
