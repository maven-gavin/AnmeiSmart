'use client';

import { Suspense, useState, useEffect } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import AppLayout from '@/components/layout/AppLayout';
import ChatWindow from '@/components/chat/ChatWindow';
import ConversationHistoryList from '@/components/chat/ConversationHistoryList';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import { ErrorDisplay } from '@/components/ui/ErrorDisplay';
import { useRoleGuard } from '@/hooks/useRoleGuard';
import { ChatWebSocketStatus } from '@/components/chat/ChatWebSocketStatus';

function CustomerChatContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  
  // 使用公共的权限检查Hook
  const { isAuthorized, error, loading } = useRoleGuard({
    requiredRole: 'customer',
    requireAuth: true,
    redirectTo: '/login?redirect=/chat/customer'
  });
  
  const [selectedConversationId, setSelectedConversationId] = useState<string | null>(
    searchParams?.get('conversationId') || null
  );
  const [showHistory, setShowHistory] = useState(true);

  // 监听URL参数变化
  useEffect(() => {
    const conversationId = searchParams?.get('conversationId');
    setSelectedConversationId(conversationId);
  }, [searchParams]);

  // 处理会话选择
  const handleConversationSelect = (conversationId: string) => {
    setSelectedConversationId(conversationId);
    router.push(`/chat/customer?conversationId=${conversationId}`, { scroll: false });
  };

  // 权限检查未通过时显示错误
  if (!isAuthorized && error) {
    return <ErrorDisplay error={error} />;
  }

  // 加载状态
  if (loading) {
    return <LoadingSpinner fullScreen />;
  }

  return (
    <div className="flex h-full flex-col bg-gray-50">
      {/* 聊天头部 */}
      <div className="border-b border-gray-200 bg-white p-4 shadow-sm">
        <div className="flex items-center justify-between">
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
          
          <div className="flex items-center space-x-3">
            <ChatWebSocketStatus />
            
            {/* 切换历史会话显示的按钮 */}
            <button
              onClick={() => setShowHistory(!showHistory)}
              className="flex items-center px-3 py-2 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-md transition-colors"
              title={showHistory ? "隐藏历史会话" : "显示历史会话"}
            >
              <svg className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {showHistory ? "隐藏历史" : "显示历史"}
            </button>
          </div>
        </div>
      </div>
      
      {/* 主要内容区域 */}
      <div className="flex-1 overflow-hidden flex">
        {/* 左侧：历史会话列表 */}
        {showHistory && (
          <div className="w-80 flex-shrink-0 border-r border-gray-200 bg-white">
            <ConversationHistoryList 
              onConversationSelect={handleConversationSelect}
              selectedConversationId={selectedConversationId}
            />
          </div>
        )}
        
        {/* 右侧：聊天窗口 */}
        <div className="flex-1 overflow-hidden">
          {selectedConversationId ? (
            <ChatWindow 
              key={selectedConversationId}
              conversationId={selectedConversationId} 
            />
          ) : (
            <div className="flex h-full items-center justify-center bg-gray-50">
              <div className="text-center">
                <svg className="mx-auto h-16 w-16 text-gray-300 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
                <h3 className="text-lg font-medium text-gray-700 mb-2">开始新的对话</h3>
                <p className="text-gray-500 mb-4">选择历史会话或开始新的咨询</p>
                <button
                  onClick={() => router.push('/chat/customer')}
                  className="inline-flex items-center px-4 py-2 bg-orange-500 text-white rounded-md hover:bg-orange-600 transition-colors"
                >
                  <svg className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                  开始新对话
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function CustomerChatPage() {
  return (
    <AppLayout requiredRole="customer">
      <Suspense fallback={<LoadingSpinner fullScreen />}>
        <CustomerChatContent />
      </Suspense>
    </AppLayout>
  );
} 