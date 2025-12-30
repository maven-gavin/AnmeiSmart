'use client';

import { useEffect, useState } from 'react';

/**
 * 处理 Next.js chunk 加载失败的全局错误处理器
 * 
 * 在企业微信等浏览器环境中，可能会遇到缓存问题导致旧的 HTML 引用新的 chunk 文件，
 * 但该 chunk 文件在新的构建中已经不存在了。这个组件会自动检测并处理这种情况。
 */
export function ChunkErrorHandler() {
  const [errorLogs, setErrorLogs] = useState<Array<{ id: string; message: string; time: string }>>([]);
  const [showLogs, setShowLogs] = useState(false);
  const storageKey = '__anmei_client_error_logs__';

  // 添加错误日志到页面显示（同时写入 sessionStorage，便于 error.tsx 查看）
  const addErrorLog = (message: string) => {
    const log = {
      id: `${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
      message,
      time: new Date().toLocaleTimeString('zh-CN'),
    };
    setErrorLogs((prev) => {
      const next = [...prev, log].slice(-20);
      try {
        sessionStorage.setItem(storageKey, JSON.stringify(next));
      } catch {
        // ignore
      }
      return next;
    });
    setShowLogs(true);
  };

  useEffect(() => {
    // 页面启动时读取历史日志（避免自动刷新后日志丢失）
    try {
      const raw = sessionStorage.getItem(storageKey);
      if (raw) {
        const parsed = JSON.parse(raw);
        if (Array.isArray(parsed) && parsed.length > 0) {
          setErrorLogs(parsed.slice(-20));
          setShowLogs(true);
        }
      }
    } catch {
      // ignore
    }

    // 监听 chunk 加载失败错误
    const handleChunkError = (event: ErrorEvent) => {
      const error = event.error || event.message;
      const errorStr = String(error);
      const where = event.filename ? ` @${event.filename}:${event.lineno ?? ''}:${event.colno ?? ''}` : '';
      const stack = event.error && (event.error as any).stack ? `\n${String((event.error as any).stack)}` : '';

      // 注意：不要用 “Failed to fetch” 作为 chunk 失败判断，容易把 API/CORS/网络错误误判成 chunk 问题
      const isChunkError =
        errorStr.includes('Loading chunk') ||
        errorStr.includes('Loading CSS chunk') ||
        errorStr.includes('ChunkLoadError') ||
        errorStr.includes('Failed to fetch dynamically imported module') ||
        errorStr.includes('/_next/static/');

      if (isChunkError) {
        const errorMessage = `检测到 chunk 加载失败，尝试刷新页面: ${errorStr}`;
        addErrorLog(errorMessage);
        
        // 检查是否已经尝试过刷新（避免无限循环）
        const hasRetried = sessionStorage.getItem('chunk-error-retry');
        const retryCount = parseInt(hasRetried || '0', 10);

        if (retryCount < 2) {
          // 标记已重试
          sessionStorage.setItem('chunk-error-retry', String(retryCount + 1));
          addErrorLog(`正在尝试自动刷新页面 (第 ${retryCount + 1} 次重试)...`);
          
          // 延迟刷新，给用户一点反馈时间
          setTimeout(async () => {
            // 清除所有可能的缓存
            try {
              // 清除 Cache Storage（若存在）
              if ('caches' in window) {
                const cacheNames = await caches.keys();
                await Promise.all(
                  cacheNames.map(name => caches.delete(name))
                );
                addErrorLog('已清除浏览器 Cache Storage，准备刷新页面');
              }
            } catch (e) {
              addErrorLog(`清除缓存时出错: ${String(e)}`);
            }
            
            // 使用更强制的刷新方式：在 URL 后添加时间戳参数，确保绕过所有缓存
            const url = new URL(window.location.href);
            url.searchParams.set('_t', Date.now().toString());
            // 使用 replace 而不是 reload，避免浏览器缓存
            window.location.replace(url.toString());
          }, 1500);
        } else {
          // 重试次数过多，清除标记，让用户手动刷新
          sessionStorage.removeItem('chunk-error-retry');
          addErrorLog('Chunk 加载失败，已重试多次，请手动刷新页面');
        }
      } else {
        // 非 chunk 错误：也记录到页面日志，便于企业微信排查（不触发自动刷新）
        addErrorLog(`捕获到错误事件: ${errorStr}${where}${stack}`);
      }
    };

    // 监听未捕获的错误
    window.addEventListener('error', handleChunkError, true);

    // 监听 Promise 拒绝（动态导入失败会触发）
    const handleUnhandledRejection = (event: PromiseRejectionEvent) => {
      const reason = event.reason;
      const reasonStr = String(reason);
      const stack = reason && (reason as any).stack ? `\n${String((reason as any).stack)}` : '';

      const isChunkError =
        reasonStr.includes('Loading chunk') ||
        reasonStr.includes('Loading CSS chunk') ||
        reasonStr.includes('ChunkLoadError') ||
        reasonStr.includes('Failed to fetch dynamically imported module') ||
        reasonStr.includes('/_next/static/');

      if (isChunkError) {
        const errorMessage = `检测到 Promise 中的 chunk 加载失败: ${reasonStr}`;
        addErrorLog(errorMessage);
        
        const hasRetried = sessionStorage.getItem('chunk-error-retry');
        const retryCount = parseInt(hasRetried || '0', 10);

        if (retryCount < 2) {
          sessionStorage.setItem('chunk-error-retry', String(retryCount + 1));
          addErrorLog(`正在尝试自动刷新页面 (第 ${retryCount + 1} 次重试)...`);
          
          setTimeout(async () => {
            try {
              // 清除所有可能的缓存
              if ('caches' in window) {
                const cacheNames = await caches.keys();
                await Promise.all(
                  cacheNames.map(name => caches.delete(name))
                );
                addErrorLog('已清除浏览器 Cache Storage，准备刷新页面');
              }
            } catch (e) {
              addErrorLog(`清除缓存时出错: ${String(e)}`);
            }
            
            // 使用更强制的刷新方式：在 URL 后添加时间戳参数
            const url = new URL(window.location.href);
            url.searchParams.set('_t', Date.now().toString());
            window.location.replace(url.toString());
          }, 1500);
        } else {
          sessionStorage.removeItem('chunk-error-retry');
          addErrorLog('Chunk 加载失败，已重试多次，请手动刷新页面');
        }
        
        // 阻止错误冒泡到控制台
        event.preventDefault();
      } else {
        // 非 chunk promise 拒绝：也记录到页面日志，便于排查（不触发自动刷新）
        addErrorLog(`捕获到未处理 Promise 拒绝: ${reasonStr}${stack}`);
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

  // 如果没有错误日志，不显示任何内容
  if (!showLogs || errorLogs.length === 0) {
    return null;
  }

  return (
    <div className="fixed bottom-0 left-0 right-0 z-[9999] pointer-events-none">
      <div className="mx-auto max-w-md p-4 pointer-events-auto">
        <div className="rounded-lg border border-orange-300 bg-white shadow-lg">
          <div className="flex items-center justify-between border-b border-orange-200 bg-orange-50 px-4 py-2">
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-orange-500"></div>
              <h3 className="text-sm font-medium text-orange-900">错误日志</h3>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => {
                  try {
                    const text = errorLogs.map((x) => `[${x.time}] ${x.message}`).join('\n');
                    navigator.clipboard?.writeText(text);
                  } catch {
                    // ignore
                  }
                }}
                className="text-xs text-orange-700 hover:text-orange-900"
                aria-label="复制日志"
              >
                复制
              </button>
              <button
                onClick={() => setShowLogs(false)}
                className="text-orange-600 hover:text-orange-800"
                aria-label="关闭日志"
              >
                <svg
                  className="h-4 w-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>
          </div>
          <div className="max-h-48 overflow-y-auto p-4">
            <div className="space-y-2">
              {errorLogs.slice(-5).map((log) => (
                <div
                  key={log.id}
                  className="rounded border border-gray-200 bg-gray-50 p-2"
                >
                  <div className="mb-1 flex items-center justify-between text-xs text-gray-500">
                    <span>{log.time}</span>
                  </div>
                  <p className="text-xs text-gray-800 break-words">{log.message}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

