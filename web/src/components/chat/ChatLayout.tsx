'use client';

import { type ReactNode } from 'react'

interface ChatLayoutProps {
  conversationList?: ReactNode;
  chatWindow?: ReactNode;
  customerProfile?: ReactNode;
}

export default function ChatLayout({
  conversationList,
  chatWindow,
  customerProfile
}: ChatLayoutProps = {}) {
  return (
    <div className="flex h-full max-h-screen flex-col overflow-hidden">      
      <div className="flex flex-1 overflow-hidden">
        {/* 左侧：会话列表 */}
        <div className="w-64 flex-shrink-0 overflow-hidden border-r border-gray-200 bg-white">
          {conversationList}
        </div>
        
        {/* 中部：聊天窗口 */}
        <div className="flex-1 overflow-hidden bg-gray-50">
          {chatWindow}
        </div>
        
        {/* 右侧：客户档案卡 */}
        <div className="w-80 flex-shrink-0 overflow-hidden border-l border-gray-200 bg-white">
          {customerProfile}
        </div>
      </div>
    </div>
  )
} 