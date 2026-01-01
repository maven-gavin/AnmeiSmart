'use client';

import { useCallback, useEffect, useState } from 'react';
import toast from 'react-hot-toast';

// 错误类型枚举
export enum ErrorType {
  CHUNK_LOAD = 'chunk_load',
  RUNTIME = 'runtime',
  PROMISE_REJECTION = 'promise_rejection',
  NETWORK = 'network',
  SYNTAX = 'syntax',
  UNKNOWN = 'unknown',
}

// 错误日志接口
export interface ErrorLog {
  id: string;
  type: ErrorType;
  message: string;
  stack?: string;
  source?: string;
  lineno?: number;
  colno?: number;
  timestamp: string;
  time: string;
  fullInfo: string;
}

export const STORAGE_KEY = '__anmei_client_error_logs__';
const MAX_LOGS = 50;

// 错误类型配置
const ERROR_TYPE_CONFIG: Record<ErrorType, { name: string; color: string }> = {
  [ErrorType.CHUNK_LOAD]: { name: '资源加载', color: 'bg-orange-100 text-orange-800 border-orange-300' },
  [ErrorType.RUNTIME]: { name: '运行时', color: 'bg-red-100 text-red-800 border-red-300' },
  [ErrorType.PROMISE_REJECTION]: { name: 'Promise 拒绝', color: 'bg-yellow-100 text-yellow-800 border-yellow-300' },
  [ErrorType.NETWORK]: { name: '网络', color: 'bg-blue-100 text-blue-800 border-blue-300' },
  [ErrorType.SYNTAX]: { name: '语法', color: 'bg-purple-100 text-purple-800 border-purple-300' },
  [ErrorType.UNKNOWN]: { name: '未知', color: 'bg-gray-100 text-gray-800 border-gray-300' },
};

// 工具函数：从 sessionStorage 读取日志
const loadLogsFromStorage = (): ErrorLog[] => {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed.slice(-MAX_LOGS) : [];
  } catch {
    return [];
  }
};

// 工具函数：保存日志到 sessionStorage
const saveLogsToStorage = (logs: ErrorLog[]) => {
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(logs));
  } catch {
    // ignore
  }
};

// 工具函数：复制文本到剪贴板
const copyToClipboard = async (text: string, successMsg: string) => {
  try {
    await navigator.clipboard.writeText(text);
    toast.success(successMsg);
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
      toast.success(successMsg);
    } catch {
      toast.error('复制失败，请手动复制');
    }
    document.body.removeChild(textArea);
  }
};

// 判断错误类型
const detectErrorType = (error: string | Error, source?: string): ErrorType => {
  const errorStr = String(error);
  
  if (
    errorStr.includes('Loading chunk') ||
    errorStr.includes('Loading CSS chunk') ||
    errorStr.includes('ChunkLoadError') ||
    errorStr.includes('Failed to fetch dynamically imported module') ||
    source?.includes('/_next/static/')
  ) {
    return ErrorType.CHUNK_LOAD;
  }
  
  if (errorStr.includes('SyntaxError') || errorStr.includes('Unexpected token')) {
    return ErrorType.SYNTAX;
  }
  
  if (
    errorStr.includes('NetworkError') ||
    errorStr.includes('Failed to fetch') ||
    errorStr.includes('Network request failed')
  ) {
    return ErrorType.NETWORK;
  }
  
  if (errorStr.includes('UnhandledPromiseRejection')) {
    return ErrorType.PROMISE_REJECTION;
  }
  
  return error instanceof Error ? ErrorType.RUNTIME : ErrorType.UNKNOWN;
};

// 生成完整错误信息
const generateFullErrorInfo = (
  error: string | Error,
  type: ErrorType,
  source?: string,
  lineno?: number,
  colno?: number,
  stack?: string
): string => {
  const errorObj = error instanceof Error ? error : new Error(String(error));
  const stackInfo = stack || errorObj.stack;
  
  const parts = [
    `错误类型: ${type}`,
    `时间: ${new Date().toLocaleString('zh-CN')}`,
    `错误消息: ${errorObj.message || String(error)}`,
    errorObj.name && `错误名称: ${errorObj.name}`,
    source && `来源: ${source}`,
    lineno !== undefined && `行号: ${lineno}`,
    colno !== undefined && `列号: ${colno}`,
    stackInfo && `\n堆栈信息:\n${stackInfo}`,
  ].filter(Boolean);
  
  return parts.join('\n');
};

/**
 * 统一的全局错误处理器
 * 
 * 功能：
 * 1. 捕获所有类型的 JavaScript 错误
 * 2. 显示完整的错误堆栈信息，便于在无法查看 console 的设备上分析错误
 * 3. 支持错误日志的折叠/展开、复制功能，方便复制错误信息给 AI 分析
 */
export function ErrorHandler() {
  const [errorLogs, setErrorLogs] = useState<ErrorLog[]>([]);
  const [isExpanded, setIsExpanded] = useState(false);

  // 添加错误日志
  const addErrorLog = useCallback((
    error: string | Error,
    source?: string,
    lineno?: number,
    colno?: number
  ) => {
    const type = detectErrorType(error, source);
    const now = new Date();
    const errorObj = error instanceof Error ? error : new Error(String(error));
    const stack = errorObj.stack;
    
    const log: ErrorLog = {
      id: `${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
      type,
      message: errorObj.message || String(error),
      stack,
      source,
      lineno,
      colno,
      timestamp: now.toISOString(),
      time: now.toLocaleTimeString('zh-CN'),
      fullInfo: generateFullErrorInfo(error, type, source, lineno, colno, stack),
    };
    
    setErrorLogs((prev) => {
      const next = [...prev, log].slice(-MAX_LOGS);
      saveLogsToStorage(next);
      return next;
    });
    
    setIsExpanded(true);
  }, []);

  // 复制单个错误
  const copyErrorLog = useCallback((log: ErrorLog) => {
    copyToClipboard(log.fullInfo, '错误信息已复制到剪贴板');
  }, []);

  // 复制所有错误
  const copyAllErrors = useCallback(() => {
    if (errorLogs.length === 0) return;
    const allErrors = errorLogs.map(log => log.fullInfo).join('\n\n' + '='.repeat(50) + '\n\n');
    copyToClipboard(allErrors, '所有错误信息已复制到剪贴板');
  }, [errorLogs]);

  // 清除所有错误日志
  const clearErrorLogs = useCallback(() => {
    setErrorLogs([]);
    saveLogsToStorage([]);
    setIsExpanded(false);
    toast.success('错误日志已清除');
  }, []);

  useEffect(() => {
    // 读取历史日志
    const logs = loadLogsFromStorage();
    if (logs.length > 0) {
      setErrorLogs(logs);
      setIsExpanded(true);
    }

    const isResourceElement = (target: EventTarget | null): target is HTMLElement => {
      if (!(target instanceof HTMLElement)) return false;
      const tag = target.tagName;
      return tag === 'IMG' || tag === 'SCRIPT' || tag === 'LINK' || tag === 'VIDEO' || tag === 'AUDIO' || tag === 'SOURCE';
    };

    // 监听运行时错误（仅处理真正的 ErrorEvent，避免把资源 error 当成 runtime）
    const handleError = (event: Event) => {
      // 资源加载失败会走 error 事件，但不是 ErrorEvent，且 target 是具体元素
      if (isResourceElement(event.target)) return;
      if (!(event instanceof ErrorEvent)) return;

      const error = event.error || new Error(event.message || 'Unknown error');
      addErrorLog(error, event.filename || undefined, event.lineno || undefined, event.colno || undefined);
    };

    // 监听未处理的 Promise 拒绝
    const handleUnhandledRejection = (event: PromiseRejectionEvent) => {
      const reason = event.reason;
      const error = reason instanceof Error ? reason : new Error(String(reason));
      addErrorLog(error);
    };

    // 监听资源加载失败（过滤 blob:/data:，避免本地预览/快速切换导致“假失败”污染日志与打断体验）
    const handleResourceError = (event: Event) => {
      const target = event.target;
      if (!isResourceElement(target)) return;

      const anyTarget = target as any;
      const src: string =
        (typeof anyTarget.currentSrc === 'string' && anyTarget.currentSrc) ||
        (typeof anyTarget.src === 'string' && anyTarget.src) ||
        target.getAttribute('src') ||
        target.getAttribute('href') ||
        '';

      if (!src) return;
      if (src.startsWith('blob:') || src.startsWith('data:')) return;

      addErrorLog(new Error(`资源加载失败: ${src}`), src);
    };

    window.addEventListener('error', handleError, true);
    window.addEventListener('unhandledrejection', handleUnhandledRejection);
    window.addEventListener('error', handleResourceError, true);

    return () => {
      window.removeEventListener('error', handleError, true);
      window.removeEventListener('unhandledrejection', handleUnhandledRejection);
      window.removeEventListener('error', handleResourceError, true);
    };
  }, [addErrorLog]);

  if (errorLogs.length === 0) {
    return null;
  }

  const config = ERROR_TYPE_CONFIG;

  return (
    <div className="fixed bottom-0 left-0 right-0 z-[9999] pointer-events-none">
      <div className="mx-auto max-w-2xl p-4 pointer-events-auto">
        <div className="rounded-lg border border-orange-300 bg-white shadow-lg">
          {/* 头部 */}
          <div className="flex items-center justify-between border-b border-orange-200 bg-orange-50 px-4 py-3">
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-orange-500 animate-pulse"></div>
              <h3 className="text-sm font-medium text-orange-900">
                错误日志 ({errorLogs.length})
              </h3>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={copyAllErrors}
                className="text-xs text-orange-700 hover:text-orange-900 px-2 py-1 rounded hover:bg-orange-100 transition-colors"
                aria-label="复制所有错误"
                title="复制所有错误"
              >
                复制全部
              </button>
              <button
                onClick={clearErrorLogs}
                className="text-xs text-orange-700 hover:text-orange-900 px-2 py-1 rounded hover:bg-orange-100 transition-colors"
                aria-label="清除日志"
                title="清除日志"
              >
                清除
              </button>
              <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="text-orange-600 hover:text-orange-800 transition-transform"
                aria-label={isExpanded ? '收起' : '展开'}
                title={isExpanded ? '收起' : '展开'}
              >
                <svg
                  className={`h-4 w-4 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 9l-7 7-7-7"
                  />
                </svg>
              </button>
            </div>
          </div>

          {/* 错误列表 */}
          {isExpanded && (
            <div className="max-h-96 overflow-y-auto p-4">
              <div className="space-y-3">
                {errorLogs.slice().reverse().map((log) => {
                  const typeConfig = config[log.type];
                  return (
                    <div key={log.id} className="rounded border border-gray-200 bg-gray-50 p-3">
                      <div className="mb-2 flex items-start justify-between gap-2">
                        <div className="flex-1 min-w-0">
                          <div className="mb-1 flex items-center gap-2 flex-wrap">
                            <span
                              className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${typeConfig.color}`}
                            >
                              {typeConfig.name}
                            </span>
                            <span className="text-xs text-gray-500">{log.time}</span>
                          </div>
                          <p className="text-sm text-gray-800 break-words font-medium">
                            {log.message}
                          </p>
                          {log.source && (
                            <p className="text-xs text-gray-500 mt-1 break-all">
                              来源: {log.source}
                              {log.lineno !== undefined && ` (${log.lineno}:${log.colno || 0})`}
                            </p>
                          )}
                        </div>
                        <button
                          onClick={() => copyErrorLog(log)}
                          className="flex-shrink-0 text-xs text-gray-600 hover:text-gray-900 px-2 py-1 rounded hover:bg-gray-200 transition-colors"
                          aria-label="复制错误"
                          title="复制错误"
                        >
                          复制
                        </button>
                      </div>
                      {log.stack && (
                        <details className="mt-2">
                          <summary className="cursor-pointer text-xs text-gray-500 hover:text-gray-700 select-none">
                            查看堆栈信息
                          </summary>
                          <pre className="mt-2 overflow-auto rounded bg-gray-100 p-2 text-xs text-gray-800 whitespace-pre-wrap break-words max-h-48 border border-gray-200">
                            {log.stack}
                          </pre>
                        </details>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* 收起状态下的简要信息 */}
          {!isExpanded && (
            <div className="px-4 py-2">
              <p className="text-xs text-gray-600">
                最近错误: {errorLogs[errorLogs.length - 1]?.message || ''}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
