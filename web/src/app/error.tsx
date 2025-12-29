'use client';

import { useEffect, useState } from 'react';
import { ErrorDisplay } from '@/components/ui/ErrorDisplay';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const [isChunkError, setIsChunkError] = useState(false);

  useEffect(() => {
    // 记录错误到控制台
    console.error('应用错误:', error);

    // 检查是否是 chunk 加载错误
    const errorStr = String(error.message || error);
    const chunkErrorPatterns = [
      'Loading chunk',
      'Loading CSS chunk',
      'Failed to fetch dynamically imported module',
      'Failed to fetch',
      'missing:',
    ];

    const isChunkLoadingError = chunkErrorPatterns.some(pattern =>
      errorStr.includes(pattern)
    );

    if (isChunkLoadingError) {
      setIsChunkError(true);
      console.warn('检测到 chunk 加载错误，将尝试自动刷新页面');

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
        }, 1500);
      } else {
        // 重试次数过多，清除标记
        sessionStorage.removeItem('chunk-error-retry');
      }
    }
  }, [error]);

  // 如果是 chunk 加载错误且正在自动刷新，显示加载提示
  if (isChunkError) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50">
        <div className="w-full max-w-md p-6">
          <div className="rounded-lg border border-orange-200 bg-white p-6 shadow-sm">
            <div className="mb-4 flex items-center">
              <div className="rounded-full bg-orange-100 p-2">
                <svg
                  className="h-6 w-6 text-orange-600 animate-spin"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                  />
                </svg>
              </div>
              <h2 className="ml-3 text-lg font-semibold text-gray-900">
                正在重新加载页面
              </h2>
            </div>
            
            <div className="mb-4">
              <p className="text-sm text-gray-600 mb-2">
                检测到资源加载问题，正在自动刷新页面...
              </p>
              <p className="text-xs text-gray-500">
                如果页面没有自动刷新，请点击下面的按钮手动刷新
              </p>
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => {
                  if ('caches' in window) {
                    caches.keys().then((names) => {
                      names.forEach((name) => {
                        caches.delete(name);
                      });
                    });
                  }
                  sessionStorage.removeItem('chunk-error-retry');
                  window.location.reload();
                }}
                className="flex-1 rounded-md bg-orange-500 px-4 py-2 text-sm font-medium text-white hover:bg-orange-600 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:ring-offset-2"
              >
                立即刷新
              </button>
              <button
                onClick={() => {
                  sessionStorage.removeItem('chunk-error-retry');
                  window.location.href = '/home';
                }}
                className="flex-1 rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:ring-offset-2"
              >
                返回首页
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="w-full max-w-md p-6">
        <div className="rounded-lg border border-red-200 bg-white p-6 shadow-sm">
          <div className="mb-4 flex items-center">
            <div className="rounded-full bg-red-100 p-2">
              <svg
                className="h-6 w-6 text-red-600"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"
                />
              </svg>
            </div>
            <h2 className="ml-3 text-lg font-semibold text-gray-900">
              应用错误
            </h2>
          </div>
          
          <div className="mb-4">
            <p className="text-sm text-gray-600 mb-2">
              {error.message || '发生了一个未知错误'}
            </p>
            {error.digest && (
              <p className="text-xs text-gray-500">
                错误ID: {error.digest}
              </p>
            )}
          </div>

          <div className="flex gap-3">
            <button
              onClick={reset}
              className="flex-1 rounded-md bg-orange-500 px-4 py-2 text-sm font-medium text-white hover:bg-orange-600 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:ring-offset-2"
            >
              重试
            </button>
            <button
              onClick={() => {
                window.location.href = '/home';
              }}
              className="flex-1 rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:ring-offset-2"
            >
              返回首页
            </button>
          </div>

          {process.env.NODE_ENV === 'development' && (
            <details className="mt-4">
              <summary className="cursor-pointer text-xs text-gray-500 hover:text-gray-700">
                查看错误详情（开发模式）
              </summary>
              <pre className="mt-2 overflow-auto rounded bg-gray-100 p-2 text-xs text-gray-800">
                {error.stack}
              </pre>
            </details>
          )}
        </div>
      </div>
    </div>
  );
}

