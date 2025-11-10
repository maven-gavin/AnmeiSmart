/**
 * API 错误处理 Hook
 * 简化错误处理逻辑，统一错误处理方式
 */

import { useState, useCallback } from 'react'
import { useAuthContext } from '@/contexts/AuthContext'
import { handleApiError, ApiClientError, type HandleApiErrorOptions, type ErrorReportContext } from '@/service/apiClient'

export interface UseApiErrorOptions extends HandleApiErrorOptions {
  /**
   * 错误发生时的回调
   */
  onError?: (message: string, error: unknown) => void
  /**
   * 是否自动包含用户信息到错误上报上下文（默认：true）
   */
  autoIncludeUserContext?: boolean
}

/**
 * API 错误处理 Hook
 * 
 * @example
 * ```typescript
 * const { handleError, errorMessage, clearError } = useApiError()
 * 
 * const handleSubmit = async () => {
 *   try {
 *     await apiClient.post('/roles', data)
 *     toast.success('创建成功')
 *   } catch (err) {
 *     handleError(err, '创建失败')
 *   }
 * }
 * ```
 */
export function useApiError(options: UseApiErrorOptions = {}) {
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const { user } = useAuthContext()
  const { autoIncludeUserContext = true, ...errorOptions } = options

  const handleError = useCallback(
    (error: unknown, fallbackMessage: string = '操作失败', context?: ErrorReportContext) => {
      // 自动包含用户信息到错误上报上下文
      const reportContext: ErrorReportContext | undefined = autoIncludeUserContext
        ? {
            ...context,
            userId: context?.userId ?? user?.id,
            url: context?.url ?? (typeof window !== 'undefined' ? window.location.href : undefined),
          }
        : context

      const message = handleApiError(error, fallbackMessage, {
        ...errorOptions,
        reportContext,
      })
      setErrorMessage(message)
      options.onError?.(message, error)
      return message
    },
    [options, autoIncludeUserContext, user]
  )

  const clearError = useCallback(() => {
    setErrorMessage(null)
  }, [])

  return {
    errorMessage,
    handleError,
    clearError,
  }
}

/**
 * API 操作 Hook（带加载状态和错误处理）
 * 
 * @example
 * ```typescript
 * const { execute, loading, error } = useApiAction()
 * 
 * const handleCreate = () => {
 *   execute(
 *     () => permissionService.createRole(data),
 *     undefined,
 *     {
 *       successMessage: '创建成功',
 *       onSuccess: () => {
 *         // 重置表单
 *         // 刷新列表
 *       }
 *     }
 *   )
 * }
 * ```
 */
export function useApiAction<T = void, P = void>(options?: UseApiErrorOptions) {
  const [loading, setLoading] = useState(false)
  const { errorMessage, handleError, clearError } = useApiError(options)
  const { user } = useAuthContext()

  const execute = useCallback(
    async (
      action: (params: P) => Promise<T>,
      params: P,
      callOptions?: {
        onSuccess?: (data: T) => void
        onError?: (message: string) => void
        successMessage?: string
        errorMessage?: string
        reportContext?: ErrorReportContext
      }
    ): Promise<T | undefined> => {
      setLoading(true)
      clearError()

      try {
        const data = await action(params)
        if (callOptions?.successMessage) {
          // 动态导入避免循环依赖
          import('react-hot-toast').then(({ default: toast }) => {
            toast.success(callOptions.successMessage!)
          })
        }
        callOptions?.onSuccess?.(data)
        return data
      } catch (err) {
        // 构建错误上报上下文
        const reportContext: ErrorReportContext | undefined = callOptions?.reportContext
          ? {
              ...callOptions.reportContext,
              userId: callOptions.reportContext.userId ?? user?.id,
              url: callOptions.reportContext.url ?? (typeof window !== 'undefined' ? window.location.href : undefined),
            }
          : undefined

        const message = handleError(err, callOptions?.errorMessage || '操作失败', reportContext)
        callOptions?.onError?.(message)
        return undefined
      } finally {
        setLoading(false)
      }
    },
    [handleError, clearError, user]
  )

  return {
    execute,
    loading,
    error: errorMessage,
    clearError,
  }
}

