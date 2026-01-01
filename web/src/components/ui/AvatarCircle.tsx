/* eslint-disable @next/next/no-img-element */
'use client'

import { cn } from '@/lib/utils'
import { useAuthedImageSrc } from '@/hooks/useAuthedImageSrc'

export interface AvatarCircleProps {
  name: string
  avatar?: string | null
  sizeClassName?: string
  className?: string
  imgClassName?: string
}

/**
 * 统一头像组件
 *
 * 业务规则：
 * - avatarUrl（normalize 后）非空：只渲染 <img>（加载失败出现碎图也接受）
 * - avatarUrl 为空：显示 name 首字母
 */
export function AvatarCircle({
  name,
  avatar,
  sizeClassName = 'w-10 h-10',
  className,
  imgClassName,
}: AvatarCircleProps) {
  const avatarUrl = useAuthedImageSrc(avatar)
  const fallbackChar = (name?.trim()?.charAt(0) || '?').toUpperCase()

  return (
    <div
      className={cn(
        'flex items-center justify-center rounded-full bg-gradient-to-br from-orange-400 to-orange-600 text-white font-semibold overflow-hidden',
        sizeClassName,
        className,
      )}
    >
      {avatarUrl ? (
        <img
          src={avatarUrl}
          alt={name}
          className={cn('w-full h-full rounded-full object-cover', imgClassName)}
        />
      ) : (
        fallbackChar
      )}
    </div>
  )
}


