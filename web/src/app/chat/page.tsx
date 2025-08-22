'use client';

import { useState, useEffect, useRef, useCallback, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import AppLayout from '@/components/layout/AppLayout';
import ChatWindow from '@/components/chat/ChatWindow';
import CustomerProfile from '@/components/profile/CustomerProfile';
import ConversationHistoryList from '@/components/chat/ConversationHistoryList';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import { ErrorDisplay } from '@/components/ui/ErrorDisplay';
import { useRoleGuard } from '@/hooks/useRoleGuard';
import { useAuthContext } from '@/contexts/AuthContext';
import { ChatWebSocketStatus } from '@/components/chat/ChatWebSocketStatus';

function SmartCommunicationContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user } = useAuthContext();
  
  // 使用公共的权限检查Hook，但不限制特定角色
  const { isAuthorized, error, loading } = useRoleGuard({
    requireAuth: true,
    redirectTo: '/login?redirect=/chat'
  });
  
  // 获取当前用户角色
  const currentRole = user?.currentRole;
  const isConsultant = currentRole === 'consultant';
  
  // URL作为唯一状态源
  const selectedCustomerId = searchParams?.get('customerId');
  const selectedConversationId = searchParams?.get('conversationId');
  const selectedFriendId = searchParams?.get('friend');
  
  // UI状态管理
  const [isSwitchingConversation, setIsSwitchingConversation] = useState(false);
  const [showHistory, setShowHistory] = useState(true);
  const [loadingFriendConversation, setLoadingFriendConversation] = useState(false);
  const prevConversationIdRef = useRef<string | null>(selectedConversationId);
  
  // 处理好友会话创建
  useEffect(() => {
    if (selectedFriendId && !selectedConversationId) {
      createFriendConversation(selectedFriendId);
    }
  }, [selectedFriendId, selectedConversationId]);
  
  const createFriendConversation = async (friendId: string) => {
    setLoadingFriendConversation(true);
    try {
      const { startConversationWithFriend } = await import('@/service/contacts/chatIntegration');
      const conversation = await startConversationWithFriend(friendId);
      
      // 更新URL，移除friend参数，添加conversation参数
      router.replace(`/chat?conversationId=${conversation.id}`, { scroll: false });
    } catch (error) {
      console.error('创建好友会话失败:', error);
      // 可以显示错误提示
    } finally {
      setLoadingFriendConversation(false);
    }
  };
  
  const handleStartNewConsultation = async () => {
    setLoadingFriendConversation(true);
    try {
      // 调用咨询API创建新的咨询会话
      const { apiClient } = await import('@/service/apiClient');
      const response = await apiClient.post('/consultation/sessions');
      const consultation = response.data;
      
      // 跳转到新创建的咨询会话
      router.push(`/chat?conversationId=${consultation.id}`, { scroll: false });
    } catch (error) {
      console.error('创建咨询会话失败:', error);
      // 可以显示错误提示
      alert('创建咨询会话失败，请重试');
    } finally {
      setLoadingFriendConversation(false);
    }
  };

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

  // 客户变化处理（仅顾问角色使用）
  const handleCustomerChange = useCallback((customerId: string, conversationId?: string) => {
    const url = conversationId 
      ? `/chat?customerId=${customerId}&conversationId=${conversationId}`
      : `/chat?customerId=${customerId}`;
    
    router.push(url, { scroll: false });
  }, [router]);

  // 会话选择处理
  const handleConversationSelect = useCallback((conversationId: string) => {
    setIsSwitchingConversation(true);
    
    if (isConsultant && selectedCustomerId) {
      router.push(`/chat?customerId=${selectedCustomerId}&conversationId=${conversationId}`, { scroll: false });
    } else {
      router.push(`/chat?conversationId=${conversationId}`, { scroll: false });
    }
  }, [router, isConsultant, selectedCustomerId]);

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
              <h2 className="text-lg font-medium text-gray-800">智能沟通</h2>
              <p className="text-sm text-gray-500">让我们快乐沟通</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-3">
            <ChatWebSocketStatus />
            
            {/* TODO: 功能待修改为开始新的咨询，仅客户角色显示该按钮 */}
            <button
                  onClick={() => router.push('/chat')}
                  className="inline-flex items-center px-4 py-2 bg-orange-500 text-white rounded-md hover:bg-orange-600 transition-colors"
                >
              <svg className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              开始新的咨询
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
        <div className="flex-1 overflow-hidden relative">
          {loadingFriendConversation ? (
            <div className="flex h-full items-center justify-center bg-gray-50">
              <div className="text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
                <h3 className="text-lg font-medium text-gray-700 mb-2">正在创建会话...</h3>
                <p className="text-gray-500">请稍候，正在为您准备与好友的对话</p>
              </div>
            </div>
          ) : selectedConversationId ? (
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
                
                {/* 根据用户角色显示不同的操作按钮 */}
                <div className="space-y-2">
                  {currentRole === 'customer' && (
                    <button
                      onClick={handleStartNewConsultation}
                      className="inline-flex items-center px-4 py-2 bg-orange-500 text-white rounded-md hover:bg-orange-600 transition-colors"
                    >
                      <svg className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                      </svg>
                      开始新的咨询
                    </button>
                  )}
                  
                  {(currentRole === 'consultant' || currentRole === 'doctor') && (
                    <p className="text-sm text-gray-500">
                      等待客户发起咨询或选择历史会话
                    </p>
                  )}
                  
                  {currentRole === 'admin' && (
                    <p className="text-sm text-gray-500">
                      选择会话查看对话内容或管理咨询
                    </p>
                  )}
                </div>
              </div>
            </div>
          )}
          
          {/* 会话切换指示器 */}
          {isSwitchingConversation && (
            <div className="absolute inset-0 bg-gray-50 bg-opacity-50 flex items-center justify-center z-10">
              <div className="h-1 w-64 bg-gray-200 rounded overflow-hidden">
                <div className="h-full bg-orange-500 animate-loading-bar"></div>
              </div>
            </div>
          )}

          {/* 右侧：客户资料 */}
          {isConsultant && selectedCustomerId && (
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

export default function SmartCommunicationPage() {
  return (
    <AppLayout>
      <Suspense fallback={<LoadingSpinner fullScreen />}>
        <SmartCommunicationContent />
      </Suspense>
    </AppLayout>
  );
}
