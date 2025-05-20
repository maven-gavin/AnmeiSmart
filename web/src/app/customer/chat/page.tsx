'use client';

import { Suspense } from 'react';
import ChatWindow from '@/components/chat/ChatWindow';
import LoadingSpinner from '@/components/ui/LoadingSpinner';

export default function CustomerChatPage() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <div className="flex h-full flex-col bg-gray-50">
        {/* 聊天头部 */}
        <div className="border-b border-gray-200 bg-white p-4 shadow-sm">
          <div className="flex items-center">
            <div className="mr-3 rounded-full bg-orange-100 p-2">
              <svg className="h-6 w-6 text-orange-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
            </div>
            <div>
              <h2 className="text-lg font-medium text-gray-800">在线咨询</h2>
              <p className="text-sm text-gray-500">与专业顾问实时沟通</p>
            </div>
          </div>
        </div>
        
        {/* 使用统一的ChatWindow组件 */}
        <div className="flex-1 overflow-hidden">
          <ChatWindow />
        </div>
      </div>
    </Suspense>
  );
} 