import { API_BASE_URL } from '@/config'

/**
 * 将存储的头像（file_id或URL）归一化为"浏览器可直接访问"的地址
 *
 * 支持三种格式：
 * 1. file_id（UUID格式，36字符）- 新格式，优先使用
 * 2. 后端 public 代理地址 - 直接返回
 * 3. Minio 直链 - 转换为代理地址（向后兼容）
 */
export function normalizeAvatarUrl(avatar?: string | null): string | undefined {
  const raw = typeof avatar === 'string' ? avatar.trim() : ''
  if (!raw) return undefined

  // 如果是file_id格式（UUID，36字符，可能包含连字符）
  // 检查是否为UUID格式：36字符，包含连字符或32字符的十六进制
  const isFileId = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(raw) ||
                   /^[0-9a-f]{32}$/i.test(raw) ||
                   (raw.length >= 32 && raw.length <= 36 && !raw.includes('://') && !raw.includes('/'))
  
  if (isFileId) {
    // 使用file_id访问
    return `${API_BASE_URL}/files/${raw}/preview`
  }

  // 已是我们提供的 public 代理
  if (raw.includes('/files/public/') || raw.includes('/files/download/') || raw.includes('/files/') && raw.includes('/preview')) {
    return raw
  }

  // 兼容 Minio 直链：http(s)://{endpoint}/{bucket}/{object_name}
  try {
    const u = new URL(raw)
    const parts = u.pathname.split('/').filter(Boolean) // [bucket, ...object]
    if (parts.length < 2) return raw

    const objectName = parts.slice(1).join('/')
    if (!objectName.includes('/avatars/')) return raw

    return `${API_BASE_URL}/files/public/${objectName}`
  } catch {
    // 非完整URL（相对路径等），原样返回
    return raw
  }
}


