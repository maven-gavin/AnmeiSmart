import type { AfterResponseHook, BeforeErrorHook, BeforeRequestHook, Hooks, HTTPError } from 'ky'
import ky from 'ky'
import type { IOtherOptions } from './apiClient'
import toast from 'react-hot-toast'
import { API_BASE_URL, SMARTBRAIN_API_BASE_URL } from '@/config'
import { tokenManager } from './tokenManager'

const TIME_OUT = 100000

export const ContentType = {
  json: 'application/json',
  stream: 'text/event-stream',
  audio: 'audio/mpeg',
  form: 'application/x-www-form-urlencoded; charset=UTF-8',
  download: 'application/octet-stream', // for download
  downloadZip: 'application/zip', // for download
  upload: 'multipart/form-data', // for upload
}

export type FetchOptionType = Omit<RequestInit, 'body'> & {
  params?: Record<string, any>
  body?: BodyInit | Record<string, any> | null
}

const afterResponse204: AfterResponseHook = async (_request: Request, _options: RequestInit, response: Response) => {
  if (response.status === 204) return Response.json({ result: 'success' })
}

export type ResponseError = {
  code: string
  message: string
  status: number
}

const afterResponseErrorCode = (otherOptions: IOtherOptions): AfterResponseHook => {
  return async (_request: Request, _options: RequestInit, response: Response) => {
    const clonedResponse = response.clone()
    if (!/^([23])\d{2}$/.test(String(clonedResponse.status))) {
      // 检查是否是blob响应（图片、视频、音频等）
      const contentType = clonedResponse.headers.get('content-type') || ''
      const isBlobResponse = 
        contentType.startsWith('image/') ||
        contentType.startsWith('video/') ||
        contentType.startsWith('audio/') ||
        contentType === 'application/pdf' ||
        contentType === 'application/octet-stream' ||
        otherOptions.skipContentType
      
      if (isBlobResponse) {
        // 对于blob响应，直接拒绝，不尝试解析JSON
        return Promise.reject(response)
      }
      
      const bodyJson = clonedResponse.json() as Promise<ResponseError>
      switch (clonedResponse.status) {
        case 403:
          bodyJson.then((data: ResponseError) => {
            if (!otherOptions.silent)
              toast.error(data.message)
            if (data.code === 'already_setup')
              globalThis.location.href = `${globalThis.location.origin}/signin`
          }).catch(() => {
            // 如果解析JSON失败，显示通用错误
            if (!otherOptions.silent)
              toast.error('请求失败')
          })
          break
        case 401:
          return Promise.reject(response)
        // fall through
        default:
          bodyJson.then((data: ResponseError) => {
            if (!otherOptions.silent)
              toast.error(data.message)
          }).catch(() => {
            // 如果解析JSON失败，显示通用错误
            if (!otherOptions.silent)
              toast.error('请求失败')
          })
          return Promise.reject(response)
      }
    }
  }
}

const beforeErrorToast = (otherOptions: IOtherOptions): BeforeErrorHook => {
  return (error: HTTPError<unknown>) => {
    if (!otherOptions.silent)
      toast.error(error.message)
    return error
  }
}


const beforeRequestSmartBrainAuthorization: BeforeRequestHook = async (request: Request) => {
  const token = await tokenManager.getValidToken()
  request.headers.set('Authorization', `Bearer ${token}`)
}

const beforeRequestAuthorization: BeforeRequestHook = async (request: Request) => {
  const accessToken = await tokenManager.getValidToken()
  request.headers.set('Authorization', `Bearer ${accessToken}`)
}

const baseHooks: Hooks = {
  afterResponse: [
    afterResponse204,
  ],
}

const baseClient = ky.create({
  hooks: baseHooks,
  timeout: TIME_OUT,
})

export const baseOptions: RequestInit = {
  method: 'GET',
  mode: 'cors',
  credentials: 'include', // always send cookies、HTTP Basic authentication.
  headers: new Headers({
    'Content-Type': ContentType.json,
  }),
  redirect: 'follow',
}

async function base<T>(url: string, options: FetchOptionType = {}, otherOptions: IOtherOptions = {}): Promise<T> {
  const { params, body, headers, ...init } = Object.assign({}, baseOptions, options)
  const {
    isSmartBrainAPI = false,
    bodyStringify = true,
    needAllResponseContent,
    deleteContentType,
    getAbortController,
    skipAuth = false,
    skipContentType = false,
  } = otherOptions

  let base: string
  if (isSmartBrainAPI)
    base = SMARTBRAIN_API_BASE_URL
  else
    base = API_BASE_URL

  if (getAbortController) {
    const abortController = new AbortController()
    getAbortController(abortController)
    options.signal = abortController.signal
  }

  const fetchPathname = base + (url.startsWith('/') ? url : `/${url}`)

  if (deleteContentType)
    (headers as Headers).delete('Content-Type')

  const authHooks: BeforeRequestHook[] = []
  if (!skipAuth) {
    authHooks.push(isSmartBrainAPI ? beforeRequestSmartBrainAuthorization : beforeRequestAuthorization)
  }

  const client = baseClient.extend({
    hooks: {
      ...baseHooks,
      beforeError: [
        ...baseHooks.beforeError || [],
        beforeErrorToast(otherOptions),
      ],
      beforeRequest: [
        ...baseHooks.beforeRequest || [],
        ...authHooks,
      ],
      afterResponse: [
        ...baseHooks.afterResponse || [],
        afterResponseErrorCode(otherOptions),
      ],
    },
  })

  const res = await client(fetchPathname, {
    ...init,
    headers,
    credentials: (options.credentials || 'include'),
    retry: {
      methods: [],
    },
    ...(bodyStringify ? { json: body } : { body: body as BodyInit }),
    searchParams: params,
    fetch(resource: RequestInfo | URL, options?: RequestInit): Promise<Response> {
      if (resource instanceof Request && options) {
        const mergedHeaders = new Headers(options.headers || {})
        resource.headers.forEach((value, key) => {
          mergedHeaders.append(key, value)
        })
        options.headers = mergedHeaders
      }
      return globalThis.fetch(resource, options)
    },
  })

  if (needAllResponseContent)
    return res as T
  
  // 如果设置了skipContentType，强制返回blob
  if (skipContentType) {
    return await res.blob() as T
  }
  
  const contentType = res.headers.get('content-type')
  if (
    contentType && (
      [ContentType.download, ContentType.audio, ContentType.downloadZip].includes(contentType) ||
      contentType.startsWith('image/') ||
      contentType.startsWith('video/') ||
      contentType.startsWith('audio/') ||
      contentType === 'application/pdf'
    )
  )
    return await res.blob() as T

  return await res.json() as T
}

export { base }
