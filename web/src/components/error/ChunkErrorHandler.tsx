'use client';

import { useEffect } from 'react';

/**
 * 处理 Next.js chunk 加载失败的全局错误处理器
 * 
 * 在企业微信等浏览器环境中，可能会遇到缓存问题导致旧的 HTML 引用新的 chunk 文件，
 * 但该 chunk 文件在新的构建中已经不存在了。这个组件会自动检测并处理这种情况。
 */
export function ChunkErrorHandler() {
  useEffect(() => {
    // 监听 chunk 加载失败错误
    const handleChunkError = (event: ErrorEvent) => {
      const error = event.error || event.message;
      const errorStr = String(error);

      // 检查是否是 chunk 加载失败
      const isChunkError = 
        errorStr.includes('Loading chunk') ||
        errorStr.includes('Loading CSS chunk') ||
        errorStr.includes('Failed to fetch dynamically imported module') ||
        errorStr.includes('Failed to fetch');

      if (isChunkError) {
        console.warn('检测到 chunk 加载失败，尝试刷新页面:', errorStr);
        
        // 检查是否已经尝试过刷新（避免无限循环）
        const hasRetried = sessionStorage.getItem('chunk-error-retry');
        const retryCount = parseInt(hasRetried || '0', 10);

        if (retryCount < 2) {
          // 标记已重试
          sessionStorage.setItem('chunk-error-retry', String(retryCount + 1));
          
          // 延迟刷新，给用户一点反馈时间
          setTimeout(() => {
            // 清除可能的缓存问题
            if ('caches' in window) {
              caches.keys().then((names) => {
                names.forEach((name) => {
                  caches.delete(name);
                });
              });
            }
            
            // 强制刷新页面（不使用缓存）
            window.location.reload();
          }, 1000);
        } else {
          // 重试次数过多，清除标记，让用户手动刷新
          sessionStorage.removeItem('chunk-error-retry');
          console.error('Chunk 加载失败，已重试多次，请手动刷新页面');
        }
      }
    };

    // 监听未捕获的错误
    window.addEventListener('error', handleChunkError, true);

    // 监听 Promise 拒绝（动态导入失败会触发）
    const handleUnhandledRejection = (event: PromiseRejectionEvent) => {
      const reason = event.reason;
      const reasonStr = String(reason);

      const isChunkError = 
        reasonStr.includes('Loading chunk') ||
        reasonStr.includes('Loading CSS chunk') ||
        reasonStr.includes('Failed to fetch dynamically imported module') ||
        reasonStr.includes('Failed to fetch') ||
        (reason instanceof TypeError && reason.message.includes('Failed to fetch'));

      if (isChunkError) {
        console.warn('检测到 Promise 中的 chunk 加载失败，尝试刷新页面:', reasonStr);
        
        const hasRetried = sessionStorage.getItem('chunk-error-retry');
        const retryCount = parseInt(hasRetried || '0', 10);

        if (retryCount < 2) {
          sessionStorage.setItem('chunk-error-retry', String(retryCount + 1));
          
          setTimeout(() => {
            if ('caches' in window) {
              caches.keys().then((names) => {
                names.forEach((name) => {
                  caches.delete(name);
                });
              });
            }
            
            window.location.reload();
          }, 1000);
        } else {
          sessionStorage.removeItem('chunk-error-retry');
          console.error('Chunk 加载失败，已重试多次，请手动刷新页面');
        }
        
        // 阻止错误冒泡到控制台
        event.preventDefault();
      }
    };

    window.addEventListener('unhandledrejection', handleUnhandledRejection);

    // 页面成功加载后，清除重试标记（说明不是 chunk 错误）
    const handleLoad = () => {
      // 延迟清除，确保所有 chunk 都已加载
      setTimeout(() => {
        sessionStorage.removeItem('chunk-error-retry');
      }, 3000);
    };

    window.addEventListener('load', handleLoad);

    // 清理函数
    return () => {
      window.removeEventListener('error', handleChunkError, true);
      window.removeEventListener('unhandledrejection', handleUnhandledRejection);
      window.removeEventListener('load', handleLoad);
    };
  }, []);

  return null;
}

