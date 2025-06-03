'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import ChatWindow from '@/components/chat/ChatWindow'
import CustomerList from '@/components/chat/CustomerList'
import CustomerProfile from '@/components/chat/CustomerProfile'
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import { useAuth } from '@/contexts/AuthContext';
import { authService } from '@/service/authService';

export default function ChatPageClient() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  const searchParams = useSearchParams();
  const [error, setError] = useState<string | null>(null);
  
  // 会话切换状态
  const [isSwitchingConversation, setIsSwitchingConversation] = useState(false);
  const prevConversationIdRef = useRef<string | null>(null);
  
  // 主要状态：选中的客户ID和会话ID
  const [selectedCustomerId, setSelectedCustomerId] = useState<string | null>(null);
  const [selectedConversationId, setSelectedConversationId] = useState<string | null>(null);

  // 从URL参数获取初始值
  const urlCustomerId = searchParams?.get('customerId');
  const urlConversationId = searchParams?.get('conversationId');

  // 监听URL参数变化，保持状态同步
  useEffect(() => {
    if (urlCustomerId !== selectedCustomerId) {
      console.log(`URL客户ID变化: ${urlCustomerId}`);
      setSelectedCustomerId(urlCustomerId);
    }
    if (urlConversationId !== selectedConversationId) {
      console.log(`URL会话ID变化: ${urlConversationId}`);
      setSelectedConversationId(urlConversationId);
    }
  }, [urlCustomerId, urlConversationId, selectedCustomerId, selectedConversationId]);

  // 处理会话ID变化时的切换动画
  useEffect(() => {
    if (!selectedConversationId || !prevConversationIdRef.current) {
      prevConversationIdRef.current = selectedConversationId;
      return;
    }
    
    if (selectedConversationId !== prevConversationIdRef.current) {
      // 显示切换状态
      setIsSwitchingConversation(true);
      
      // 300ms后隐藏切换状态
      const timer = setTimeout(() => {
        setIsSwitchingConversation(false);
        prevConversationIdRef.current = selectedConversationId;
      }, 300);
      
      return () => clearTimeout(timer);
    }
  }, [selectedConversationId]);

  // 处理客户和会话变化的统一回调
  const handleCustomerChange = useCallback((customerId: string, conversationId?: string) => {
    console.log(`客户变化: customerId=${customerId}, conversationId=${conversationId}`);
    
    // 更新本地状态
    setSelectedCustomerId(customerId);
    setSelectedConversationId(conversationId || null);
    
    // 更新URL
    const url = conversationId 
      ? `/consultant/chat?customerId=${customerId}&conversationId=${conversationId}`
      : `/consultant/chat?customerId=${customerId}`;
    
    router.push(url, { scroll: false });
  }, [router]);

  // 权限检查
  useEffect(() => {
    // 等待认证完成
    if (authLoading) {
      console.log('认证加载中，等待认证完成...');
      return;
    }
    
    // 检查登录状态
    if (!authService.isLoggedIn()) {
      console.log('用户未登录，重定向到登录页面');
      router.push('/login');
      return;
    }

    // 检查用户角色
    if (user && user.currentRole !== 'consultant') {
      console.log(`用户角色不是consultant(${user.currentRole})，重定向到首页`);
      setError('无权访问顾问聊天页面');
      const timer = setTimeout(() => {
        router.push('/');
      }, 1500);
      
      return () => clearTimeout(timer);
    }
  }, [authLoading, user, router]);

  // 如果有错误，显示错误信息
  if (error) {
    return (
      <div className="flex h-full flex-col items-center justify-center bg-gray-50">
        <div className="text-red-500 text-lg mb-4">{error}</div>
        <div className="text-gray-500 text-sm">正在重定向...</div>
      </div>
    );
  }
  
  // 如果还在认证中，显示加载状态
  if (authLoading) {
    return (
      <div className="flex h-full flex-col items-center justify-center bg-gray-50">
        <LoadingSpinner size="lg" />
        <p className="mt-4 text-gray-600">加载中...</p>
      </div>
    );
  }

  return (
    <div className="h-full w-full relative">
      {/* 顾问聊天布局 */}
      <div className="flex h-full flex-col bg-gray-50">
        {/* 聊天头部 */}
        <div className="border-b border-gray-200 bg-white p-4 shadow-sm">
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
              <ChatWindow 
                key={selectedConversationId}
                conversationId={selectedConversationId}
              />
            ) : (
              <div className="flex h-full items-center justify-center bg-gray-50">
                <div className="text-center">
                  <svg className="mx-auto h-16 w-16 text-gray-300 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                  <h3 className="text-lg font-medium text-gray-700 mb-2">选择客户开始对话</h3>
                  <p className="text-gray-500">从左侧客户列表中选择一位客户</p>
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
              <CustomerProfile customerId={selectedCustomerId} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
} 