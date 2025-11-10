/**
 * 错误上报服务
 * 用于将系统错误上报到监控系统
 */

import { ApiClientError } from './apiClient'

/**
 * 错误上报配置
 */
export interface ErrorReportConfig {
  /** 是否启用错误上报（默认：生产环境启用） */
  enabled?: boolean
  /** 上报接口地址 */
  endpoint?: string
  /** 应用标识 */
  appId?: string
  /** 环境标识 */
  environment?: string
}

/**
 * 错误上报数据
 */
export interface ErrorReport {
  /** 错误类型 */
  type: 'business' | 'system' | 'network' | 'unknown'
  /** 错误码 */
  code?: number
  /** HTTP 状态码 */
  status?: number
  /** 错误消息 */
  message: string
  /** 错误堆栈 */
  stack?: string
  /** 错误详情 */
  detail?: unknown
  /** 用户信息 */
  userId?: string
  /** 请求路径 */
  path?: string
  /** 请求方法 */
  method?: string
  /** 时间戳 */
  timestamp: string
  /** 用户代理 */
  userAgent?: string
  /** 页面 URL */
  url?: string
}

class ErrorReporter {
  private config: Required<ErrorReportConfig>

  constructor(config: ErrorReportConfig = {}) {
    this.config = {
      enabled: config.enabled ?? (process.env.NODE_ENV === 'production'),
      endpoint: config.endpoint ?? '/api/v1/errors/report',
      appId: config.appId ?? 'anmei-smart-web',
      environment: config.environment ?? process.env.NODE_ENV ?? 'development',
    }
  }

  /**
   * 上报错误
   */
  async report(error: unknown, context?: {
    userId?: string
    path?: string
    method?: string
    url?: string
  }): Promise<void> {
    if (!this.config.enabled) {
      return
    }

    try {
      const report = this.buildReport(error, context)
      await this.sendReport(report)
    } catch (reportError) {
      // 错误上报失败不应该影响主流程，只打印日志
      console.warn('错误上报失败:', reportError)
    }
  }

  /**
   * 构建错误报告
   */
  private buildReport(
    error: unknown,
    context?: {
      userId?: string
      path?: string
      method?: string
      url?: string
    }
  ): ErrorReport {
    let type: ErrorReport['type'] = 'unknown'
    let code: number | undefined
    let status: number | undefined
    let message = '未知错误'
    let stack: string | undefined
    let detail: unknown

    if (error instanceof ApiClientError) {
      if (error.isBusinessError()) {
        type = 'business'
      } else if (error.isSystemError()) {
        type = 'system'
      }
      code = error.code
      status = error.status
      message = error.message
      stack = error.stack
      detail = error.responseData
    } else if (error instanceof Error) {
      // 网络错误
      if (error.message.includes('network') || error.message.includes('fetch')) {
        type = 'network'
      } else {
        type = 'system'
      }
      message = error.message
      stack = error.stack
      detail = error
    } else {
      detail = error
    }

    return {
      type,
      code,
      status,
      message,
      stack,
      detail,
      userId: context?.userId,
      path: context?.path,
      method: context?.method,
      timestamp: new Date().toISOString(),
      userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : undefined,
      url: context?.url ?? (typeof window !== 'undefined' ? window.location.href : undefined),
    }
  }

  /**
   * 发送错误报告
   */
  private async sendReport(report: ErrorReport): Promise<void> {
    // 使用 fetch 发送，避免循环依赖
    const response = await fetch(this.config.endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        ...report,
        appId: this.config.appId,
        environment: this.config.environment,
      }),
      // 不等待响应，避免阻塞
      keepalive: true,
    })

    if (!response.ok) {
      throw new Error(`错误上报失败: ${response.status}`)
    }
  }

  /**
   * 更新配置
   */
  updateConfig(config: Partial<ErrorReportConfig>): void {
    this.config = { ...this.config, ...config }
  }
}

// 单例实例
export const errorReporter = new ErrorReporter()

/**
 * 上报错误（便捷函数）
 */
export function reportError(
  error: unknown,
  context?: {
    userId?: string
    path?: string
    method?: string
    url?: string
  }
): void {
  // 异步上报，不阻塞主流程
  errorReporter.report(error, context).catch(() => {
    // 静默失败
  })
}

