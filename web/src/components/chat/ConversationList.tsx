'use client';

import { useState } from 'react'
import { cn } from '@/lib/utils'
import { mockConversations } from '@/lib/mockData'

export default function ConversationList() {
  const [selectedId, setSelectedId] = useState<string>('1') // 默认选中第一个会话
  
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
        {mockConversations.map(conversation => (
          <button
            key={conversation.id}
            onClick={() => setSelectedId(conversation.id)}
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
                {conversation.lastMessage.content}
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
        ))}
      </div>
    </div>
  )
} 