'use client';

import { useState, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { cn } from '@/service/utils'
import { getConversations } from '@/service/chatService'
import { Conversation } from '@/types/chat'
import { useAuth } from '@/contexts/AuthContext'

export default function ConversationList() {
  const searchParams = useSearchParams()
  const initialSelectedId = searchParams?.get('conversationId') || '1'
  const [selectedId, setSelectedId] = useState<string>(initialSelectedId)
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const router = useRouter()
  const { logout } = useAuth()
  
  // 加载会话列表
  const loadConversations = async () => {
    try {
      setLoading(true)
      const data = await getConversations()
      setConversations(data)
      setError(null)
    } catch (err) {
      console.error('获取会话列表失败:', err)
      // 如果收到401错误，可能是token过期，执行登出操作
      if (err instanceof Error && err.message.includes('401')) {
        console.log('Token已过期，跳转到登录页')
        await logout()
      } else {
        setError('获取会话列表失败')
      }
      setConversations([])
    } finally {
      setLoading(false)
    }
  }
  
  // 处理会话选择
  const handleConversationSelect = (conversationId: string) => {
    setSelectedId(conversationId)
    // 更新URL参数，不刷新页面
    router.push(`?conversationId=${conversationId}`, { scroll: false })
  }
  
  // 监听URL参数变化
  useEffect(() => {
    const conversationId = searchParams?.get('conversationId')
    if (conversationId) {
      setSelectedId(conversationId)
    }
  }, [searchParams])
  
  // 初始加载会话列表
  useEffect(() => {
    loadConversations()
  }, [])
  
  // 定期刷新会话列表
  useEffect(() => {
    const intervalId = setInterval(() => {
      loadConversations()
    }, 30000) // 每30秒刷新一次
    
    return () => clearInterval(intervalId)
  }, [])
  
  // 显示加载状态
  if (loading && conversations.length === 0) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-gray-300 border-t-orange-500"></div>
      </div>
    )
  }
  
  // 显示错误信息
  if (error && conversations.length === 0) {
    return (
      <div className="flex h-full flex-col items-center justify-center p-4 text-center">
        <div className="text-red-500 mb-4">{error}</div>
        <button
          onClick={loadConversations}
          className="rounded-md bg-orange-500 px-4 py-2 text-white hover:bg-orange-600"
        >
          重试
        </button>
      </div>
    )
  }
  
  return (
    <div className="flex h-full flex-col">
      {/* 搜索框 */}
      <div className="p-3">
        <input
          type="text"
          placeholder="搜索会话..."
          className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-orange-500 focus:outline-none"
        />
      </div>
      
      {/* 会话列表 */}
      <div className="flex-1 overflow-y-auto">
        {conversations.length === 0 ? (
          <div className="flex h-full items-center justify-center text-gray-500">
            暂无会话
          </div>
        ) : (
          conversations.map(conversation => (
            <button
              key={conversation.id}
              onClick={() => handleConversationSelect(conversation.id)}
              className={cn(
                'flex w-full items-center space-x-3 border-b border-gray-100 p-3 text-left hover:bg-orange-50',
                selectedId === conversation.id && 'bg-orange-50'
              )}
            >
              <div className="relative flex-shrink-0">
                <img
                  src={conversation.user.avatar}
                  alt={conversation.user.name}
                  className="h-12 w-12 rounded-full bg-gray-100 flex items-center justify-center"
                  onError={(e) => {
                    // 如果头像加载失败，使用首字母替代
                    const target = e.target as HTMLImageElement;
                    target.onerror = null; // 防止循环错误
                    const nameInitial = conversation.user.name.charAt(0);
                    target.style.fontSize = '16px';
                    target.style.fontWeight = 'bold';
                    target.style.display = 'flex';
                    target.style.alignItems = 'center';
                    target.style.justifyContent = 'center';
                    target.style.backgroundColor = '#FF9800';
                    target.style.color = '#FFFFFF';
                    target.src = 'data:image/svg+xml;charset=UTF-8,' + 
                      encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48"></svg>');
                    setTimeout(() => {
                      (target.parentNode as HTMLElement).innerHTML = `<div class="h-12 w-12 rounded-full flex items-center justify-center text-white font-bold" style="background-color: #FF9800">${nameInitial}</div>`;
                    }, 0);
                  }}
                />
                {conversation.unreadCount > 0 && (
                  <span className="absolute -right-1 -top-1 flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-xs text-white">
                    {conversation.unreadCount}
                  </span>
                )}
              </div>
              
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <h4 className="font-medium truncate">{conversation.user.name}</h4>
                  <span className="text-xs text-gray-500 flex-shrink-0 ml-1">
                    {new Date(conversation.updatedAt).toLocaleTimeString()}
                  </span>
                </div>
                
                <p className="truncate text-sm text-gray-600">
                  {conversation.lastMessage?.content || '暂无消息'}
                </p>
                
                <div className="mt-1 flex flex-wrap gap-1">
                  {conversation.user.tags.map(tag => (
                    <span
                      key={tag}
                      className="rounded-full bg-orange-100 px-2 py-0.5 text-xs text-orange-700"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            </button>
          ))
        )}
      </div>
    </div>
  )
} 