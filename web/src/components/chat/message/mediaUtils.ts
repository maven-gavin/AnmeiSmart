export function isTempFileId(fileId?: string | null): boolean {
  return typeof fileId === 'string' && fileId.startsWith('temp_')
}

export function isDirectPreviewUrl(url: string): boolean {
  return (
    url.startsWith('blob:') ||
    url.startsWith('data:') ||
    url.startsWith('http://') ||
    url.startsWith('https://')
  )
}

export function revokeBlobUrl(url?: string | null) {
  if (typeof url === 'string' && url.startsWith('blob:')) {
    URL.revokeObjectURL(url)
  }
}

// 统一的媒体加载 key：
// - pending(temp_)：优先用 media_info.url（本地预览）
// - sent：优先 file_id，否则 url（如某些场景直接给了可用 URL）
export function getMediaLoadKey(mediaInfo?: { file_id?: string; url?: string } | null): string | null {
  if (!mediaInfo) return null

  const fileId = mediaInfo.file_id
  const url = mediaInfo.url

  if (isTempFileId(fileId)) {
    return url || null
  }

  return fileId || url || null
}


