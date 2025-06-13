'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import ChatWindow from '@/components/chat/ChatWindow'
import CustomerList from '@/components/chat/CustomerList'
import CustomerProfile from '@/components/profile/CustomerProfile'
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import { ErrorDisplay } from '@/components/ui/ErrorDisplay';
import { useRoleGuard } from '@/hooks/useRoleGuard';
import { ChatWebSocketStatus } from '@/components/chat/ChatWebSocketStatus';

export default function ChatPageClient() {
  const router = useRouter();
  const searchParams = useSearchParams();
  
  // 使用公共的权限检查Hook
  const { isAuthorized, error, loading } = useRoleGuard({
    requiredRole: 'consultant',
    requireAuth: true
  });
  
  // URL作为唯一状态源
  const selectedCustomerId = searchParams?.get('customerId');
  const selectedConversationId = searchParams?.get('conversationId');
  
  // 会话切换状态
  const [isSwitchingConversation, setIsSwitchingConversation] = useState(false);
  const prevConversationIdRef = useRef<string | null>(selectedConversationId);

  // 处理会话ID变化时的切换动画
  useEffect(() => {
    if (selectedConversationId !== prevConversationIdRef.current && prevConversationIdRef.current !== null) {
      setIsSwitchingConversation(true);
      
      const timer = setTimeout(() => {
        setIsSwitchingConversation(false);
        prevConversationIdRef.current = selectedConversationId;
      }, 300);
      
      return () => clearTimeout(timer);
    } else {
      prevConversationIdRef.current = selectedConversationId;
    }
  }, [selectedConversationId]);

  // 客户变化处理
  const handleCustomerChange = useCallback((customerId: string, conversationId?: string) => {
    const url = conversationId 
      ? `/consultant/chat?customerId=${customerId}&conversationId=${conversationId}`
      : `/consultant/chat?customerId=${customerId}`;
    
    router.push(url, { scroll: false });
  }, [router]);

  // 权限检查未通过时显示错误
  if (!isAuthorized && error) {
    return <ErrorDisplay error={error} />;
  }
  
  // 加载状态
  if (loading) {
    return (
      <div className="flex h-full flex-col items-center justify-center bg-gray-50">
        <LoadingSpinner size="lg" />
        <p className="mt-4 text-gray-600">加载中...</p>
      </div>
    );
  }

  return (
    <div className="h-full w-full relative">
      <div className="flex h-full flex-col bg-gray-50">
        {/* 聊天头部 */}
        <div className="border-b border-gray-200 bg-white p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <div className="mr-3 rounded-full bg-blue-100 p-2">
                <svg className="h-6 w-6 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
              </div>
              <div>
                <h2 className="text-lg font-medium text-gray-800">智能客服</h2>
                <p className="text-sm text-gray-500">管理客户咨询和会话</p>
              </div>
            </div>
            <ChatWebSocketStatus />
          </div>
        </div>
        
        {/* 主要内容区域 */}
        <div className="flex-1 overflow-hidden flex">
          {/* 左侧：客户列表 */}
          <div className="w-80 flex-shrink-0 border-r border-gray-200 bg-white">
            <CustomerList 
              onCustomerChange={handleCustomerChange}
              selectedCustomerId={selectedCustomerId}
              selectedConversationId={selectedConversationId}
            />
          </div>
          
          {/* 中间：聊天窗口 */}
          <div className="flex-1 overflow-hidden relative">
            {selectedConversationId ? (
              <ChatWindow conversationId={selectedConversationId} />
            ) : (
              <div className="flex h-full items-center justify-center bg-gray-50">
                <div className="text-center">
                  <svg className="mx-auto h-16 w-16 text-gray-300 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                  </svg>
                  <h3 className="text-lg font-medium text-gray-700 mb-2">欢迎使用智能客服</h3>
                  <p className="text-gray-500 mb-4">从左侧客户列表中选择一位客户开始对话</p>
                  <div className="text-sm text-gray-400">
                    <p>💬 查看客户咨询</p>
                    <p>🤖 AI智能回复</p>
                    <p>👨‍💼 顾问接管功能</p>
                  </div>
                </div>
              </div>
            )}
            
            {/* 会话切换指示器 */}
            {isSwitchingConversation && (
              <div className="absolute inset-0 bg-gray-50 bg-opacity-50 flex items-center justify-center z-10">
                <div className="h-1 w-64 bg-gray-200 rounded overflow-hidden">
                  <div className="h-full bg-blue-500 animate-loading-bar"></div>
                </div>
              </div>
            )}
          </div>
          
          {/* 右侧：客户资料 */}
          {selectedCustomerId && (
            <div className="w-80 flex-shrink-0 border-l border-gray-200 bg-white">
              <CustomerProfile 
                customerId={selectedCustomerId} 
                conversationId={selectedConversationId || undefined} 
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
} 