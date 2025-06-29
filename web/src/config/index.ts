// API基础URL
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';

// WebSocket URL
export const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_URL || 
  (typeof window !== 'undefined' && window.location.protocol === 'https:' ? 'wss:' : 'ws:') + 
  '//' + 
  (process.env.NEXT_PUBLIC_API_BASE_URL ? 
    process.env.NEXT_PUBLIC_API_BASE_URL.replace(/^https?:\/\//, '').replace('/api/v1', '') : 
    'localhost:8000'
  );

// 文件相关配置
export const FILE_CONFIG = {
  MAX_FILE_SIZE: 50 * 1024 * 1024, // 50MB
  CHUNK_SIZE: 2 * 1024 * 1024, // 2MB
  SUPPORTED_IMAGE_TYPES: ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
  SUPPORTED_DOCUMENT_TYPES: ['application/pdf', 'text/plain'],
  API_ENDPOINTS: {
    upload: '/files/upload',
    preview: '/files/preview',
    download: '/files/download',
    info: '/files/info',
    delete: '/files/delete'
  }
} as const;

// 应用配置
export const APP_CONFIG = {
  appName: '安美智能咨询系统',
  version: '1.0.0',
} as const;

// 认证配置
export const AUTH_CONFIG = {
  TOKEN_STORAGE_KEY: 'auth_token',
  USER_STORAGE_KEY: 'auth_user',
  REFRESH_TOKEN_KEY: 'refresh_token'
} as const; 