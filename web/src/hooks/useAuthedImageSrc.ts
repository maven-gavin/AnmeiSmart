/* eslint-disable no-console */
'use client'

import { useEffect, useMemo, useState } from 'react'
import { apiClient } from '@/service/apiClient'
import { normalizeAvatarUrl } from '@/utils/avatarUrl'

const FILE_ID_REGEX =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i

const PREVIEW_FILE_ID_REGEX = /\/files\/([0-9a-f-]{32,36})\/preview\b/i

// 简单的内存级缓存：避免列表/表单重复拉取同一头像
const blobUrlCache = new Map<string, string>()
const inflight = new Map<string, Promise<string>>()

function extractFileId(input?: string | null): string | undefined {
  const raw = typeof input === 'string' ? input.trim() : ''
  if (!raw) return undefined

  // data:/blob: 直接可用
  if (raw.startsWith('data:') || raw.startsWith('blob:')) return undefined

  // 纯 file_id
  if (FILE_ID_REGEX.test(raw) || (/^[0-9a-f]{32}$/i.test(raw) && !raw.includes('/'))) {
    return raw
  }

  // /files/{id}/preview（可能是绝对或相对）
  const m = raw.match(PREVIEW_FILE_ID_REGEX)
  if (m?.[1]) return m[1]

  return undefined
}

async function getOrCreateBlobUrl(fileId: string): Promise<string> {
  const cached = blobUrlCache.get(fileId)
  if (cached) return cached

  const existing = inflight.get(fileId)
  if (existing) return existing

  const p = (async () => {
    const resp = await apiClient.get<Blob>(`/files/${fileId}/preview`, {}, { skipContentType: true, silent: true })
    const blob = resp.data
    if (!blob) throw new Error('文件预览为空')
    const url = URL.createObjectURL(blob)
    blobUrlCache.set(fileId, url)
    return url
  })().finally(() => {
    inflight.delete(fileId)
  })

  inflight.set(fileId, p)
  return p
}

/**
 * 把「file_id 或 /files/{id}/preview」变成浏览器可直接显示的 `blob:` URL（自动携带鉴权）
 *
 * - 输入可能是 file_id / 绝对URL / 相对URL / dataURL / blobURL
 * - 对非受保护链接（比如 /files/public/...）会原样返回
 */
export function useAuthedImageSrc(src?: string | null): string | undefined {
  const normalized = useMemo(() => {
    // 兼容旧逻辑：如果传的是 avatar 字段（file_id / url），先 normalize 一下
    return normalizeAvatarUrl(src) ?? (typeof src === 'string' ? src.trim() : '')
  }, [src])

  const [finalSrc, setFinalSrc] = useState<string | undefined>(() => {
    if (!normalized) return undefined
    if (normalized.startsWith('data:') || normalized.startsWith('blob:')) return normalized
    // 先乐观返回：若是 public url 直接可用
    return normalized
  })

  useEffect(() => {
    let cancelled = false

    async function run() {
      if (!normalized) {
        if (!cancelled) setFinalSrc(undefined)
        return
      }

      if (normalized.startsWith('data:') || normalized.startsWith('blob:')) {
        if (!cancelled) setFinalSrc(normalized)
        return
      }

      const fileId = extractFileId(normalized) ?? extractFileId(src)
      if (!fileId) {
        if (!cancelled) setFinalSrc(normalized)
        return
      }

      try {
        const blobUrl = await getOrCreateBlobUrl(fileId)
        if (!cancelled) setFinalSrc(blobUrl)
      } catch (e) {
        console.warn('[useAuthedImageSrc] load failed:', e)
        if (!cancelled) setFinalSrc(undefined)
      }
    }

    run()
    return () => {
      cancelled = true
    }
  }, [normalized, src])

  return finalSrc
}


