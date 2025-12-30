'use client';

import { useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import { ErrorLog, STORAGE_KEY } from '@/components/error/ErrorHandler';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const [errorDetails, setErrorDetails] = useState<string>('');
  const [recentLogs, setRecentLogs] = useState<ErrorLog[]>([]);
  const [isExpanded, setIsExpanded] = useState(false);

  useEffect(() => {
    // 生成错误详情
    const errorStr = String(error.message || error);
    const fullErrorInfo = `错误: ${errorStr}${error.stack ? `\n\n堆栈信息:\n${error.stack}` : ''}`;
    setErrorDetails(fullErrorInfo);

    // 读取 ErrorHandler 写入的错误日志
    try {
      const raw = sessionStorage.getItem(STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw);
        if (Array.isArray(parsed) && parsed.length > 0) {
          setRecentLogs(parsed.slice(-20));
        }
      }
    } catch {
      // ignore
    }
  }, [error]);

  // 复制错误信息
  const copyError = (text: string) => {
    const copyToClipboard = async () => {
      try {
        await navigator.clipboard.writeText(text);
        toast.success('错误信息已复制到剪贴板');
      } catch {
        // 降级方案
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.opacity = '0';
        document.body.appendChild(textArea);
        textArea.select();
        try {
          document.execCommand('copy');
          toast.success('错误信息已复制到剪贴板');
        } catch {
          toast.error('复制失败，请手动复制');
        }
        document.body.removeChild(textArea);
      }
    };
    copyToClipboard();
  };

  // 复制所有错误日志
  const copyAllLogs = () => {
    if (recentLogs.length === 0) return;
    const allLogs = recentLogs.map(log => log.fullInfo).join('\n\n' + '='.repeat(50) + '\n\n');
    copyError(allLogs);
  };

  // 清除缓存并刷新
  const handleRefresh = () => {
    if ('caches' in window) {
      caches.keys().then((names) => {
        names.forEach((name) => caches.delete(name));
      });
    }
    window.location.reload();
  };

  // 错误日志项组件
  const ErrorLogItem = ({ log }: { log: ErrorLog }) => (
    <div className="rounded border border-gray-200 bg-gray-50 p-2">
      <div className="mb-1 flex items-center justify-between">
        <span className="text-xs text-gray-500">{log.time}</span>
        <button
          onClick={() => copyError(log.fullInfo)}
          className="text-xs text-gray-600 hover:text-gray-900"
        >
          复制
        </button>
      </div>
      <p className="text-xs text-gray-800 break-words">{log.message}</p>
      {log.stack && (
        <details className="mt-1">
          <summary className="cursor-pointer text-xs text-gray-500 hover:text-gray-700">
            堆栈信息
          </summary>
          <pre className="mt-1 overflow-auto rounded bg-gray-100 p-2 text-xs text-gray-800 whitespace-pre-wrap break-words max-h-32">
            {log.stack}
          </pre>
        </details>
      )}
    </div>
  );

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="w-full max-w-md p-6">
        <div className="rounded-lg border border-red-200 bg-white p-6 shadow-sm">
          {/* 错误头部 */}
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
            <h2 className="ml-3 text-lg font-semibold text-gray-900">应用错误</h2>
          </div>

          {/* 错误信息 */}
          <div className="mb-4">
            <p className="text-sm text-gray-600 mb-2">
              {error.message || '发生了一个未知错误'}
            </p>
            {error.digest && (
              <p className="text-xs text-gray-500 mb-2">错误ID: {error.digest}</p>
            )}
            <p className="text-xs text-gray-500">
              建议：复制下方错误信息给 AI 分析，或尝试重试/刷新页面
            </p>
          </div>

          {/* 操作按钮 */}
          <div className="flex gap-3 mb-4">
            <button
              onClick={reset}
              className="flex-1 rounded-md bg-orange-500 px-4 py-2 text-sm font-medium text-white hover:bg-orange-600 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:ring-offset-2"
            >
              重试
            </button>
            <button
              onClick={handleRefresh}
              className="flex-1 rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:ring-offset-2"
            >
              刷新页面
            </button>
            <button
              onClick={() => {
                window.location.href = '/tasks';
              }}
              className="flex-1 rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:ring-offset-2"
            >
              返回任务管理
            </button>
          </div>

          {/* 错误详情 */}
          {errorDetails && (
            <details className="mt-4">
              <summary
                className="cursor-pointer text-xs text-gray-500 hover:text-gray-700 flex items-center justify-between"
                onClick={(e) => {
                  e.preventDefault();
                  setIsExpanded(!isExpanded);
                }}
              >
                <span>查看详细错误信息</span>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    copyError(errorDetails);
                  }}
                  className="text-xs text-orange-600 hover:text-orange-800 px-2 py-1 rounded hover:bg-orange-50"
                >
                  复制
                </button>
              </summary>
              <pre className="mt-2 overflow-auto rounded bg-gray-100 p-3 text-xs text-gray-800 whitespace-pre-wrap break-words max-h-48 border border-gray-200">
                {errorDetails}
              </pre>
            </details>
          )}

          {/* 最近错误日志 */}
          {recentLogs.length > 0 && (
            <details className="mt-4">
              <summary className="cursor-pointer text-xs text-gray-500 hover:text-gray-700 flex items-center justify-between">
                <span>查看最近错误日志 ({recentLogs.length} 条)</span>
                <button
                  onClick={copyAllLogs}
                  className="text-xs text-orange-600 hover:text-orange-800 px-2 py-1 rounded hover:bg-orange-50"
                >
                  复制全部
                </button>
              </summary>
              <div className="mt-2 space-y-2 max-h-48 overflow-y-auto">
                {recentLogs.slice().reverse().map((log) => (
                  <ErrorLogItem key={log.id} log={log} />
                ))}
              </div>
            </details>
          )}
        </div>
      </div>
    </div>
  );
}
