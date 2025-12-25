import { API_BASE_URL } from '@/config'

/**
 * 将存储的头像 URL 归一化为“浏览器可直接访问”的地址
 *
 * 兼容两类存量数据：
 * - 直接存了 Minio 访问地址（可能是内网域名，浏览器无法访问）
 * - 已经是后端 public 代理地址（直接返回）
 */
export function normalizeAvatarUrl(avatar?: string | null): string | undefined {
  const raw = typeof avatar === 'string' ? avatar.trim() : ''
  if (!raw) return undefined

  // 已是我们提供的 public 代理
  if (raw.includes('/files/public/') || raw.includes('/files/download/')) return raw

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


