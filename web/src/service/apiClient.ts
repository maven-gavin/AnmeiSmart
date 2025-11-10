/**
 * API 客户端
 * 提供统一的HTTP请求接口，支持自动认证和错误处理
 */
import { API_BASE_URL, SMARTBRAIN_API_BASE_URL } from '@/config'
import toast from 'react-hot-toast'
import type { AnnotationReply, MessageEnd, MessageReplace, ThoughtItem } from '@/types/chat'
import type { VisionFile } from '@/types/smart-brain-app'
import type {
  AgentLogResponse,
  IterationFinishedResponse,
  IterationNextResponse,
  IterationStartedResponse,
  LoopFinishedResponse,
  LoopNextResponse,
  LoopStartedResponse,
  NodeFinishedResponse,
  NodeStartedResponse,
  ParallelBranchFinishedResponse,
  ParallelBranchStartedResponse,
  TextChunkResponse,
  TextReplaceResponse,
  WorkflowFinishedResponse,
  WorkflowStartedResponse,
} from '@/types/smart-brain-workflow'
import type { FetchOptionType, ResponseError } from './fetch'
import { ContentType, base, baseOptions } from './fetch'
import { asyncRunSafe } from './utils'
import { tokenManager } from './tokenManager'

// =============== 类型定义 ===============

export type IOnDataMoreInfo = {
  conversationId?: string
  taskId?: string
  messageId: string
  errorMessage?: string
  errorCode?: string
}

export type IOnData = (message: string, isFirstMessage: boolean, moreInfo: IOnDataMoreInfo) => void
export type IOnThought = (though: ThoughtItem) => void
export type IOnFile = (file: VisionFile) => void
export type IOnMessageEnd = (messageEnd: MessageEnd) => void
export type IOnMessageReplace = (messageReplace: MessageReplace) => void
export type IOnAnnotationReply = (messageReplace: AnnotationReply) => void
export type IOnCompleted = (hasError?: boolean, errorMessage?: string) => void
export type IOnError = (msg: string, code?: string) => void

export type IOnWorkflowStarted = (workflowStarted: WorkflowStartedResponse) => void
export type IOnWorkflowFinished = (workflowFinished: WorkflowFinishedResponse) => void
export type IOnNodeStarted = (nodeStarted: NodeStartedResponse) => void
export type IOnNodeFinished = (nodeFinished: NodeFinishedResponse) => void
export type IOnIterationStarted = (workflowStarted: IterationStartedResponse) => void
export type IOnIterationNext = (workflowStarted: IterationNextResponse) => void
export type IOnNodeRetry = (nodeFinished: NodeFinishedResponse) => void
export type IOnIterationFinished = (workflowFinished: IterationFinishedResponse) => void
export type IOnParallelBranchStarted = (parallelBranchStarted: ParallelBranchStartedResponse) => void
export type IOnParallelBranchFinished = (parallelBranchFinished: ParallelBranchFinishedResponse) => void
export type IOnTextChunk = (textChunk: TextChunkResponse) => void
export type IOnTTSChunk = (messageId: string, audioStr: string, audioType?: string) => void
export type IOnTTSEnd = (messageId: string, audioStr: string, audioType?: string) => void
export type IOnTextReplace = (textReplace: TextReplaceResponse) => void
export type IOnLoopStarted = (workflowStarted: LoopStartedResponse) => void
export type IOnLoopNext = (workflowStarted: LoopNextResponse) => void
export type IOnLoopFinished = (workflowFinished: LoopFinishedResponse) => void
export type IOnAgentLog = (agentLog: AgentLogResponse) => void

/**
 * SSE流式响应处理器集合
 */
export interface StreamHandlers {
  onData?: IOnData
  onCompleted?: IOnCompleted
  onThought?: IOnThought
  onFile?: IOnFile
  onMessageEnd?: IOnMessageEnd
  onMessageReplace?: IOnMessageReplace
  onWorkflowStarted?: IOnWorkflowStarted
  onWorkflowFinished?: IOnWorkflowFinished
  onNodeStarted?: IOnNodeStarted
  onNodeFinished?: IOnNodeFinished
  onIterationStart?: IOnIterationStarted
  onIterationNext?: IOnIterationNext
  onIterationFinish?: IOnIterationFinished
  onLoopStart?: IOnLoopStarted
  onLoopNext?: IOnLoopNext
  onLoopFinish?: IOnLoopFinished
  onNodeRetry?: IOnNodeRetry
  onParallelBranchStarted?: IOnParallelBranchStarted
  onParallelBranchFinished?: IOnParallelBranchFinished
  onTextChunk?: IOnTextChunk
  onTTSChunk?: IOnTTSChunk
  onTTSEnd?: IOnTTSEnd
  onTextReplace?: IOnTextReplace
  onAgentLog?: IOnAgentLog
}

export type IOtherOptions = StreamHandlers & {
  isSmartBrainAPI?: boolean
  bodyStringify?: boolean
  needAllResponseContent?: boolean
  deleteContentType?: boolean
  silent?: boolean
  onData?: IOnData // for stream
  onError?: IOnError
  getAbortController?: (abortController: AbortController) => void
}

/**
 * SSE事件数据格式
 */
interface SSEEventData {
  event?: string
  status?: number
  message?: string
  code?: string
  answer?: string
  conversation_id?: string
  task_id?: string
  id?: string
  message_id?: string
  audio?: string
  audio_type?: string
  [key: string]: unknown
}

// =============== 工具函数 ===============

/**
 * Unicode转字符
 */
function unicodeToChar(text: string): string {
  if (!text) return ''
  return text.replace(/\\u[0-9a-f]{4}/g, (_match, p1) => {
    return String.fromCharCode(Number.parseInt(p1, 16))
  })
}

/**
 * 跳转到SSO登录页面
 */
function requiredWebSSOLogin(message?: string, code?: number): void {
  const params = new URLSearchParams()
  params.append('redirect_url', encodeURIComponent(`${globalThis.location.pathname}${globalThis.location.search}`))
  if (message) params.append('message', message)
  if (code) params.append('code', String(code))
  globalThis.location.href = `/login?${params.toString()}`
}

/**
 * 格式化文本（保留用于向后兼容）
 * @deprecated 建议移动到工具模块
 */
export function format(text: string): string {
  let res = text.trim()
  if (res.startsWith('\n')) res = res.replace('\n', '')
  return res.replaceAll('\n', '<br/>').replaceAll('```', '')
}

/**
 * 统一处理401认证错误
 */
async function handle401Error(
  errResp: Response,
  isSmartBrainAPI: boolean,
  silent?: boolean
): Promise<never> {
  const [parseErr, errRespData] = await asyncRunSafe<ResponseError>(errResp.json())
  const loginUrl = `${globalThis.location.origin}/login`
  
  if (parseErr) {
    globalThis.location.href = loginUrl
    return Promise.reject(errResp)
  }

  const { code, message } = errRespData

  // SmartBrain API特殊处理
  if (isSmartBrainAPI) {
    if (code === 'web_app_access_denied') {
      requiredWebSSOLogin(message, 403)
      return Promise.reject(errResp)
    }
    if (code === 'web_sso_auth_required') {
      tokenManager.clearTokens()
      requiredWebSSOLogin()
      return Promise.reject(errResp)
    }
    if (code === 'unauthorized') {
      tokenManager.clearTokens()
      globalThis.location.reload()
      return Promise.reject(errResp)
    }
  }

  // 通用SSO处理
  if (code === 'web_app_access_denied') {
    requiredWebSSOLogin(message, 403)
    return Promise.reject(errResp)
  }
  if (code === 'web_sso_auth_required') {
    tokenManager.clearTokens()
    requiredWebSSOLogin()
    return Promise.reject(errResp)
  }
  if (code === 'unauthorized_and_force_logout') {
    tokenManager.clearTokens()
    globalThis.location.reload()
    return Promise.reject(errResp)
  }

  // 尝试刷新token
  const [refreshErr] = await asyncRunSafe(tokenManager.refreshToken(isSmartBrainAPI))
  if (refreshErr === null) {
    // Token刷新成功，返回重试标记
    return Promise.reject(new Error('RETRY_REQUEST'))
  }

  // Token刷新失败，跳转登录
  if (globalThis.location.pathname !== '/login') {
    globalThis.location.href = loginUrl
    return Promise.reject(errResp)
  }

  if (!silent) {
    toast.error(message || '认证失败，请重新登录')
  }
  globalThis.location.href = loginUrl
  return Promise.reject(errResp)
}

// =============== SSE流式处理 ===============

/**
 * SSE事件处理器映射表
 */
const createEventHandlers = (
  handlers: StreamHandlers & { onData: IOnData },
  bufferObj: SSEEventData,
  isFirstMessage: { current: boolean }
) => {
  return {
    'message': () => {
      handlers.onData(unicodeToChar(bufferObj.answer || ''), isFirstMessage.current, {
        conversationId: bufferObj.conversation_id,
        taskId: bufferObj.task_id,
        messageId: bufferObj.id || '',
      })
      isFirstMessage.current = false
    },
    'agent_message': () => {
      handlers.onData(unicodeToChar(bufferObj.answer || ''), isFirstMessage.current, {
        conversationId: bufferObj.conversation_id,
        taskId: bufferObj.task_id,
        messageId: bufferObj.id || '',
      })
      isFirstMessage.current = false
    },
    'agent_thought': () => handlers.onThought?.(bufferObj as ThoughtItem),
    'message_file': () => handlers.onFile?.(bufferObj as VisionFile),
    'message_end': () => handlers.onMessageEnd?.(bufferObj as MessageEnd),
    'message_replace': () => handlers.onMessageReplace?.(bufferObj as MessageReplace),
    'workflow_started': () => handlers.onWorkflowStarted?.(bufferObj as WorkflowStartedResponse),
    'workflow_finished': () => handlers.onWorkflowFinished?.(bufferObj as WorkflowFinishedResponse),
    'node_started': () => handlers.onNodeStarted?.(bufferObj as NodeStartedResponse),
    'node_finished': () => handlers.onNodeFinished?.(bufferObj as NodeFinishedResponse),
    'iteration_started': () => handlers.onIterationStart?.(bufferObj as IterationStartedResponse),
    'iteration_next': () => handlers.onIterationNext?.(bufferObj as IterationNextResponse),
    'iteration_completed': () => handlers.onIterationFinish?.(bufferObj as IterationFinishedResponse),
    'loop_started': () => handlers.onLoopStart?.(bufferObj as LoopStartedResponse),
    'loop_next': () => handlers.onLoopNext?.(bufferObj as LoopNextResponse),
    'loop_completed': () => handlers.onLoopFinish?.(bufferObj as LoopFinishedResponse),
    'node_retry': () => handlers.onNodeRetry?.(bufferObj as NodeFinishedResponse),
    'parallel_branch_started': () => handlers.onParallelBranchStarted?.(bufferObj as ParallelBranchStartedResponse),
    'parallel_branch_finished': () => handlers.onParallelBranchFinished?.(bufferObj as ParallelBranchFinishedResponse),
    'text_chunk': () => handlers.onTextChunk?.(bufferObj as TextChunkResponse),
    'text_replace': () => handlers.onTextReplace?.(bufferObj as TextReplaceResponse),
    'agent_log': () => handlers.onAgentLog?.(bufferObj as AgentLogResponse),
    'tts_message': () => handlers.onTTSChunk?.(bufferObj.message_id || '', bufferObj.audio as string, bufferObj.audio_type as string),
    'tts_message_end': () => handlers.onTTSEnd?.(bufferObj.message_id || '', bufferObj.audio as string),
  }
}

/**
 * 处理SSE流式响应
 */
function handleStream(response: Response, handlers: StreamHandlers & { onData: IOnData }): void {
  if (!response.ok) {
    throw new Error('Network response was not ok')
  }

  const reader = response.body?.getReader()
  if (!reader) {
    handlers.onCompleted?.(true, 'Response body is null')
    return
  }

  const decoder = new TextDecoder('utf-8')
  let buffer = ''
  let bufferObj: SSEEventData = {}
  const isFirstMessage = { current: true }
  const eventHandlers = createEventHandlers(handlers, bufferObj, isFirstMessage)

  function read(): void {
    let hasError = false
    if (!reader) return
    
    reader.read().then((result) => {
      if (result.done) {
        handlers.onCompleted?.()
        return
      }

      buffer += decoder.decode(result.value, { stream: true })
      const lines = buffer.split('\n')

      try {
        for (const message of lines) {
          if (!message.startsWith('data: ')) continue

          try {
            bufferObj = JSON.parse(message.substring(6)) as SSEEventData
          } catch {
            // 处理消息截断情况
            handlers.onData('', isFirstMessage.current, {
              conversationId: bufferObj?.conversation_id,
              messageId: bufferObj?.message_id || '',
            })
            continue
          }

          // 处理错误状态
          if (bufferObj.status === 400 || !bufferObj.event) {
            handlers.onData('', false, {
              conversationId: undefined,
              messageId: '',
              errorMessage: bufferObj?.message,
              errorCode: bufferObj?.code,
            })
            hasError = true
            handlers.onCompleted?.(true, bufferObj?.message)
            continue
          }

          // 使用映射表处理事件
          const handler = eventHandlers[bufferObj.event as keyof typeof eventHandlers]
          if (handler) {
            handler()
          }
        }

        buffer = lines[lines.length - 1] || ''
      } catch (e) {
        handlers.onData('', false, {
          conversationId: undefined,
          messageId: '',
          errorMessage: String(e),
        })
        hasError = true
        handlers.onCompleted?.(true, String(e))
        return
      }

      if (!hasError) {
        read()
      }
    }).catch((error) => {
      handlers.onData('', false, {
        conversationId: undefined,
        messageId: '',
        errorMessage: String(error),
      })
      handlers.onCompleted?.(true, String(error))
    })
  }

  read()
}

// =============== 文件上传 ===============

/**
 * 上传选项
 */
interface UploadOptions {
  xhr: XMLHttpRequest
  method?: string
  url?: string
  headers?: Record<string, string>
  data?: FormData | Blob | File
  onprogress?: (event: ProgressEvent<EventTarget>) => void
}

/**
 * 文件上传
 */
export const upload = async (
  options: UploadOptions,
  isSmartBrainAPI = false,
  url?: string,
  searchParams?: string
): Promise<unknown> => {
  const urlPrefix = isSmartBrainAPI ? SMARTBRAIN_API_BASE_URL : API_BASE_URL
  const token = await tokenManager.getValidToken(isSmartBrainAPI)
  
  const defaultOptions: UploadOptions = {
    xhr: options.xhr,
    method: 'POST',
    url: (url ? `${urlPrefix}${url}` : `${urlPrefix}/files/upload`) + (searchParams || ''),
    headers: {
      Authorization: `Bearer ${token}`,
    },
    data: options.data,
  }

  const finalOptions = {
    ...defaultOptions,
    ...options,
    headers: { ...defaultOptions.headers, ...options.headers },
  }

  return new Promise((resolve, reject) => {
    const xhr = finalOptions.xhr
    xhr.open(finalOptions.method || 'POST', finalOptions.url!)
    
    for (const key in finalOptions.headers) {
      xhr.setRequestHeader(key, finalOptions.headers[key])
    }

    xhr.withCredentials = true
    xhr.responseType = 'json'
    xhr.onreadystatechange = function () {
      if (xhr.readyState === 4) {
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve(xhr.response)
        } else {
          reject(xhr)
        }
      }
    }
    
    if (finalOptions.onprogress) {
      xhr.upload.onprogress = finalOptions.onprogress
    }
    
    xhr.send(finalOptions.data)
  })
}

// =============== SSE POST ===============

/**
 * SSE流式POST请求
 */
export const ssePost = async (
  url: string,
  fetchOptions: FetchOptionType,
  otherOptions: IOtherOptions,
): Promise<void> => {
  const {
    isSmartBrainAPI = false,
    onData,
    onCompleted,
    onThought,
    onFile,
    onMessageEnd,
    onMessageReplace,
    onWorkflowStarted,
    onWorkflowFinished,
    onNodeStarted,
    onNodeFinished,
    onIterationStart,
    onIterationNext,
    onIterationFinish,
    onNodeRetry,
    onParallelBranchStarted,
    onParallelBranchFinished,
    onTextChunk,
    onTTSChunk,
    onTTSEnd,
    onTextReplace,
    onAgentLog,
    onError,
    getAbortController,
    onLoopStart,
    onLoopNext,
    onLoopFinish,
  } = otherOptions

  const abortController = new AbortController()
  const token = await tokenManager.getValidToken(isSmartBrainAPI)

  const options = Object.assign({}, baseOptions, {
    method: 'POST',
    signal: abortController.signal,
    headers: new Headers({
      Authorization: `Bearer ${token}`,
    }),
  } as RequestInit, fetchOptions)

  const contentType = (options.headers as Headers).get('Content-Type')
  if (!contentType) {
    (options.headers as Headers).set('Content-Type', ContentType.json)
  }

  getAbortController?.(abortController)

  const urlPrefix = isSmartBrainAPI ? SMARTBRAIN_API_BASE_URL : API_BASE_URL
  const urlWithPrefix = (url.startsWith('http://') || url.startsWith('https://'))
    ? url
    : `${urlPrefix}${url.startsWith('/') ? url : `/${url}`}`

  const { body } = options
  if (body) {
    options.body = JSON.stringify(body)
  }

  globalThis.fetch(urlWithPrefix, options as RequestInit)
    .then((res) => {
      if (!/^[23]\d{2}$/.test(String(res.status))) {
        if (res.status === 401) {
          tokenManager.refreshToken(isSmartBrainAPI)
            .then(() => {
              ssePost(url, fetchOptions, otherOptions)
            })
            .catch(() => {
              res.json().then((data: ResponseError) => {
                if (isSmartBrainAPI) {
                  if (data.code === 'web_app_access_denied') {
                    requiredWebSSOLogin(data.message, 403)
                  } else if (data.code === 'web_sso_auth_required') {
                    tokenManager.clearTokens()
                    requiredWebSSOLogin()
                  } else if (data.code === 'unauthorized') {
                    tokenManager.clearTokens()
                    globalThis.location.reload()
                  }
                }
              })
            })
        } else {
          res.json().then((data: { message?: string }) => {
            toast.error(data.message || 'Server Error')
          })
          onError?.('Server Error')
        }
        return
      }

      const handlers: StreamHandlers & { onData: IOnData } = {
        onData: (str: string, isFirstMessage: boolean, moreInfo: IOnDataMoreInfo) => {
          if (moreInfo.errorMessage) {
            onError?.(moreInfo.errorMessage, moreInfo.errorCode)
            const errorMsg = moreInfo.errorMessage
            if (
              errorMsg !== 'AbortError: The user aborted a request.' &&
              !errorMsg.includes('TypeError: Cannot assign to read only property')
            ) {
              toast.error(errorMsg)
            }
            return
          }
          onData?.(str, isFirstMessage, moreInfo)
        },
        onCompleted,
        onThought,
        onFile,
        onMessageEnd,
        onMessageReplace,
        onWorkflowStarted,
        onWorkflowFinished,
        onNodeStarted,
        onNodeFinished,
        onIterationStart,
        onIterationNext,
        onIterationFinish,
        onLoopStart,
        onLoopNext,
        onLoopFinish,
        onNodeRetry,
        onParallelBranchStarted,
        onParallelBranchFinished,
        onTextChunk,
        onTTSChunk,
        onTTSEnd,
        onTextReplace,
        onAgentLog,
      }

      return handleStream(res, handlers)
    })
    .catch((e) => {
      const errorStr = String(e)
      if (
        errorStr !== 'AbortError: The user aborted a request.' &&
        !errorStr.includes('TypeError: Cannot assign to read only property')
      ) {
        toast.error(errorStr)
      }
      onError?.(errorStr)
    })
}

// =============== 基础请求 ===============

/**
 * 基础请求函数
 */
export const request = async <T>(url: string, options: unknown = {}, otherOptions?: IOtherOptions): Promise<T> => {
  try {
    const otherOptionsForBaseFetch = otherOptions || {}
    const [err, resp] = await asyncRunSafe<T>(base(url, options as FetchOptionType, otherOptionsForBaseFetch))
    
    if (err === null) {
      return resp
    }

    // 处理 401 认证错误
    const errResp: Response = err as any
    if (errResp.status === 401) {
      const {
        isSmartBrainAPI = false,
        silent,
      } = otherOptionsForBaseFetch

      try {
        await handle401Error(errResp, isSmartBrainAPI, silent)
      } catch (retryError) {
        // 如果是重试标记，重新发起请求
        if (retryError instanceof Error && retryError.message === 'RETRY_REQUEST') {
          return base<T>(url, options as FetchOptionType, otherOptionsForBaseFetch)
        }
        throw retryError
      }
    }

    // 其他错误由 fetch.ts 中的 hook 处理（afterResponseErrorCode 和 beforeErrorToast）
    return Promise.reject(err)
  } catch (error) {
    // 如果是 ApiClientError，直接抛出（已经显示过 toast）
    if (error instanceof ApiClientError) {
      throw error
    }
    console.error(error)
    return Promise.reject(error)
  }
}

// =============== HTTP方法 ===============

/**
 * GET请求
 */
export const get = <T>(url: string, options: unknown = {}, otherOptions?: IOtherOptions): Promise<T> => {
  return request<T>(url, Object.assign({}, options as FetchOptionType, { method: 'GET' }), otherOptions)
}

/**
 * POST请求
 */
export const post = <T>(url: string, options: unknown = {}, otherOptions?: IOtherOptions): Promise<T> => {
  const normalizedOptions = normalizeBodyOptions(options)
  return request<T>(url, Object.assign({}, normalizedOptions, { method: 'POST' }), otherOptions)
}

/**
 * PUT请求
 */
export const put = <T>(url: string, options: unknown = {}, otherOptions?: IOtherOptions): Promise<T> => {
  const normalizedOptions = normalizeBodyOptions(options)
  return request<T>(url, Object.assign({}, normalizedOptions, { method: 'PUT' }), otherOptions)
}

/**
 * DELETE请求
 */
export const del = <T>(url: string, options: unknown = {}, otherOptions?: IOtherOptions): Promise<T> => {
  const normalizedOptions = normalizeBodyOptions(options)
  return request<T>(url, Object.assign({}, normalizedOptions, { method: 'DELETE' }), otherOptions)
}

/**
 * PATCH请求
 */
export const patch = <T>(url: string, options: unknown = {}, otherOptions?: IOtherOptions): Promise<T> => {
  const normalizedOptions = normalizeBodyOptions(options)
  return request<T>(url, Object.assign({}, normalizedOptions, { method: 'PATCH' }), otherOptions)
}

// =============== SmartBrain API方法工厂 ===============

/**
 * 创建SmartBrain API方法
 */
function createSmartBrainMethod(
  method: <U>(url: string, options?: unknown, otherOptions?: IOtherOptions) => Promise<U>
) {
  return <U>(url: string, options: unknown = {}, otherOptions?: IOtherOptions): Promise<U> => {
    return method<U>(url, options, { ...otherOptions, isSmartBrainAPI: true })
  }
}

export const getSmartBrain = createSmartBrainMethod(get)
export const postSmartBrain = createSmartBrainMethod(post)
export const putSmartBrain = createSmartBrainMethod(put)
export const delSmartBrain = createSmartBrainMethod(del)
export const patchSmartBrain = createSmartBrainMethod(patch)

// =============== 请求选项标准化 ===============

const FETCH_OPTION_KEYS = new Set([
  'body',
  'json',
  'params',
  'headers',
  'signal',
  'timeout',
  'cache',
  'credentials',
  'mode',
  'redirect',
  'referrer',
  'referrerPolicy',
  'integrity',
  'keepalive',
  'window',
  'hooks',
  'searchParams',
  'priority',
  'duplex',
  'throwHttpErrors',
])

/**
 * 标准化请求体选项
 */
const normalizeBodyOptions = (options: unknown): FetchOptionType => {
  if (!options || typeof options !== 'object' || Array.isArray(options)) {
    return options as FetchOptionType
  }

  const optionEntries = Object.entries(options)
  if (optionEntries.length === 0) {
    return options as FetchOptionType
  }

  const hasExplicitBody =
    'body' in (options as Record<string, unknown>) ||
    'json' in (options as Record<string, unknown>) ||
    'form' in (options as Record<string, unknown>)

  if (hasExplicitBody) {
    return options as FetchOptionType
  }

  const bodyPayload: Record<string, unknown> = {}
  const normalizedOptions: Record<string, unknown> = {}

  for (const [key, value] of optionEntries) {
    if (FETCH_OPTION_KEYS.has(key) || key === 'method') {
      normalizedOptions[key] = value
    } else {
      bodyPayload[key] = value
    }
  }

  if (Object.keys(bodyPayload).length > 0) {
    normalizedOptions.body = bodyPayload
  }

  return normalizedOptions as FetchOptionType
}

// =============== 响应处理 ===============

/**
 * 错误类型枚举（兼容旧的 ErrorType）
 */
export enum ErrorType {
  AUTHENTICATION = 'AUTHENTICATION',
  AUTHORIZATION = 'AUTHORIZATION',
  NETWORK = 'NETWORK',
  VALIDATION = 'VALIDATION',
  SERVER = 'SERVER',
  UNKNOWN = 'UNKNOWN',
}

/**
 * API客户端错误
 * 统一的错误类，兼容旧的 AppError 功能
 */
export class ApiClientError extends Error {
  code?: number
  status?: number
  responseData?: unknown
  type?: ErrorType
  timestamp: string

  constructor(
    message: string,
    options?: {
      code?: number
      status?: number
      responseData?: unknown
      type?: ErrorType
    }
  ) {
    super(message)
    this.name = 'ApiClientError'
    this.code = options?.code
    this.status = options?.status
    this.responseData = options?.responseData
    this.timestamp = new Date().toISOString()
    // 延迟推断类型，避免在构造函数中调用实例方法
    this.type = options?.type ?? this.inferErrorType()
  }

  /**
   * 根据错误码和状态码推断错误类型
   */
  private inferErrorType(): ErrorType {
    if (this.status === 401) {
      return ErrorType.AUTHENTICATION
    }
    if (this.status === 403) {
      return ErrorType.AUTHORIZATION
    }
    if (this.status === 422) {
      return ErrorType.VALIDATION
    }
    if (this.status !== undefined && this.status >= 500) {
      return ErrorType.SERVER
    }
    if (this.code !== undefined) {
      if (this.code >= 50000) {
        return ErrorType.SERVER
      }
      if (this.code >= 40000 && this.code < 50000) {
        // 业务错误根据具体错误码判断类型
        if (this.code === 40000) {
          return ErrorType.VALIDATION
        }
        if (this.code === 40003) {
          return ErrorType.AUTHORIZATION
        }
      }
    }
    return ErrorType.UNKNOWN
  }

  /**
   * 判断是否是业务错误（40000-49999）
   * 业务错误是预期的错误，比如验证失败、权限不足、资源不存在等
   */
  isBusinessError(): boolean {
    if (this.code === undefined) return false
    // 业务错误码范围：40000-49999
    return this.code >= 40000 && this.code < 50000
  }

  /**
   * 判断是否是系统错误（50000+）
   * 系统错误是意外的错误，比如服务器内部错误、网络错误等
   */
  isSystemError(): boolean {
    if (this.code === undefined) {
      // 如果没有错误码，根据 HTTP 状态码判断
      return this.status !== undefined && this.status >= 500
    }
    // 系统错误码范围：50000+
    return this.code >= 50000
  }

  /**
   * 转换为旧的 ApiError 格式（向后兼容）
   */
  toApiError(): {
    type: ErrorType
    status: number
    message: string
    detail?: string
    timestamp: string
  } {
    return {
      type: this.type ?? ErrorType.UNKNOWN,
      status: this.status ?? 0,
      message: this.message,
      detail: typeof this.responseData === 'string' ? this.responseData : JSON.stringify(this.responseData),
      timestamp: this.timestamp,
    }
  }
}

/**
 * 错误上报上下文
 */
export interface ErrorReportContext {
  /** 用户 ID */
  userId?: string
  /** 请求路径 */
  path?: string
  /** 请求方法 */
  method?: string
  /** 页面 URL */
  url?: string
}

/**
 * 错误处理选项
 */
export interface HandleApiErrorOptions {
  /**
   * 是否在控制台打印错误（默认：仅系统错误打印）
   */
  logError?: boolean
  /**
   * 是否显示 toast 提示（默认：业务错误不显示，系统错误显示）
   * 注意：业务错误的 toast 已经在 extractResponseData 中显示过了
   */
  showToast?: boolean
  /**
   * 是否上报错误（默认：仅系统错误上报）
   */
  reportError?: boolean
  /**
   * 错误上报上下文
   */
  reportContext?: ErrorReportContext
  /**
   * 自定义错误消息提取函数
   */
  getMessage?: (error: unknown) => string
}

/**
 * 统一处理 API 错误
 * 
 * @param error 错误对象
 * @param fallbackMessage 默认错误消息
 * @param options 处理选项
 * @returns 错误消息字符串
 * 
 * @example
 * ```typescript
 * try {
 *   await apiClient.post('/roles', data)
 *   toast.success('创建成功')
 * } catch (err) {
 *   const message = handleApiError(err, '创建失败')
 *   setFormError(message)
 * }
 * ```
 */
export function handleApiError(
  error: unknown,
  fallbackMessage: string = '操作失败',
  options: HandleApiErrorOptions = {}
): string {
  const { logError, showToast, getMessage } = options

  // 提取错误消息
  let errorMessage = fallbackMessage
  if (getMessage) {
    errorMessage = getMessage(error)
  } else if (error instanceof ApiClientError) {
    errorMessage = error.message
  } else if (error instanceof Error) {
    errorMessage = error.message
  }

  // 处理 ApiClientError
  if (error instanceof ApiClientError) {
    const isBusiness = error.isBusinessError()
    const isSystem = error.isSystemError()

    // 业务错误：已经在 extractResponseData 中显示了 toast，这里不再显示
    // 也不打印控制台错误（因为这是预期的错误）
    if (isBusiness) {
      // 业务错误不打印控制台日志（除非明确指定）
      if (logError === true) {
        console.error('业务错误:', errorMessage, error)
      }
      // 业务错误不重复显示 toast（除非明确指定）
      if (showToast === true) {
        toast.error(errorMessage)
      }
      return errorMessage
    }

    // 系统错误：需要打印控制台日志（方便调试），可以显示 toast，需要上报
    if (isSystem) {
      // 系统错误默认打印控制台日志（除非明确指定不打印）
      if (logError !== false) {
        console.error('系统错误:', errorMessage, error)
      }
      // 系统错误默认显示 toast（除非明确指定不显示）
      if (showToast !== false) {
        toast.error(errorMessage)
      }
      // 上报系统错误（异步，不阻塞）
      if (options.reportError !== false) {
        import('./errorReporter').then(({ reportError }) => {
          reportError(error, options.reportContext)
        })
      }
      return errorMessage
    }
  }

  // 其他错误（网络错误、未知错误等）：按系统错误处理
  if (logError !== false) {
    console.error('请求错误:', errorMessage, error)
  }
  if (showToast !== false) {
    toast.error(errorMessage)
  }
  // 上报未知错误
  if (options.reportError !== false) {
    import('./errorReporter').then(({ reportError }) => {
      reportError(error, options.reportContext)
    })
  }

  return errorMessage
}

/**
 * API响应信封格式
 * 
 * 后端统一返回格式，错误响应可能没有 data 字段
 */
type ApiEnvelope<T> = {
  code: number
  message: string
  data?: T  // data 字段是可选的，错误响应可能没有
  timestamp?: string
}

/**
 * 检查是否为API响应信封格式
 * 
 * 后端统一返回格式：{code: number, message: string, data?: T, timestamp?: string}
 * 错误响应可能没有 data 字段，所以只检查 code 和 message
 */
const isApiEnvelope = <T>(payload: unknown): payload is ApiEnvelope<T> => {
  if (!payload || typeof payload !== 'object') return false
  const maybe = payload as Record<string, unknown>
  // 只要包含 code 和 message 字段，就认为是 ApiEnvelope 格式
  // data 字段是可选的（错误响应可能没有 data）
  return typeof maybe.code === 'number' && typeof maybe.message === 'string'
}

/**
 * 从响应中提取业务数据
 * 
 * 处理统一的 ApiEnvelope 格式响应：
 * - code === 0: 成功，返回 data
 * - code !== 0: 业务错误，显示提示并抛出异常
 */
const extractResponseData = <T>(payload: unknown, silent?: boolean): T => {
  if (isApiEnvelope<T>(payload)) {
    if (payload.code === 0) {
      return payload.data as T
    }
    // 业务错误：HTTP 200 但 code !== 0
    // 根据错误码定义：
    // - 40000: VALIDATION_ERROR (验证错误)
    // - 40001: BUSINESS_ERROR (业务错误)
    // - 40003: PERMISSION_DENIED (权限拒绝)
    // - 40400: NOT_FOUND (未找到)
    // - 50000: SYSTEM_ERROR (系统错误)
    // - 50001: NETWORK_ERROR (网络错误)
    const errorMessage = payload.message || '请求失败'
    // 如果不是 silent 模式，自动显示错误提示
    if (!silent) {
      toast.error(errorMessage)
    }
    throw new ApiClientError(errorMessage, {
      code: payload.code,
      responseData: payload.data,
    })
  }
  return payload as T
}

/**
 * 包装响应数据
 */
const wrapResponse = <T>(raw: unknown, silent?: boolean): { data: T; ok: boolean; status: number } => ({
  data: extractResponseData<T>(raw, silent),
  ok: true,
  status: 200,
})

/**
 * 创建API客户端方法
 */
function createApiMethod(
  method: <U>(url: string, options?: unknown, otherOptions?: IOtherOptions) => Promise<U>
) {
  return async <U>(url: string, options: unknown = {}, otherOptions?: IOtherOptions) => {
    try {
      const result = await method<U>(url, options, otherOptions)
      return wrapResponse<U>(result, otherOptions?.silent)
    } catch (error) {
      // 如果是 ApiClientError，已经显示过 toast，直接重新抛出
      if (error instanceof ApiClientError) {
        throw error
      }
      // 其他错误继续抛出
      throw error
    }
  }
}

// =============== API客户端对象 ===============

/**
 * API客户端
 * 提供统一的HTTP请求接口，自动处理响应格式和错误
 */
export const apiClient = {
  get: createApiMethod(get),
  post: createApiMethod(post),
  put: createApiMethod(put),
  patch: createApiMethod(patch),
  delete: createApiMethod(del),
  del: createApiMethod(del),
  upload: async <T>(url: string, data: FormData, otherOptions?: IOtherOptions): Promise<{ data: T }> => {
    try {
      const options: UploadOptions = {
        data,
        xhr: new XMLHttpRequest(),
      }
      const result = await upload(options, otherOptions?.isSmartBrainAPI, url)
      return wrapResponse<T>(result, otherOptions?.silent)
    } catch (error) {
      // 如果是 ApiClientError，已经显示过 toast，直接重新抛出
      if (error instanceof ApiClientError) {
        throw error
      }
      // 其他错误继续抛出
      throw error
    }
  },
  ssePost,
  getSmartBrain: createApiMethod(getSmartBrain),
  postSmartBrain: createApiMethod(postSmartBrain),
  putSmartBrain: createApiMethod(putSmartBrain),
  patchSmartBrain: createApiMethod(patchSmartBrain),
  delSmartBrain: createApiMethod(delSmartBrain),
}
