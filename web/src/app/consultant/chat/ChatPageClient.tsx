'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import ChatWindow from '@/components/chat/ChatWindow'
import CustomerList from '@/components/chat/CustomerList'
import CustomerProfile from '@/components/chat/CustomerProfile'
import { getConversations, createConversation, getCustomerList, getCustomerConversations } from '@/service/chatService';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import { useAuth } from '@/contexts/AuthContext';
import { authService } from '@/service/authService';

export default function ChatPageClient() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  const searchParams = useSearchParams();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // 会话切换状态
  const [isSwitchingConversation, setIsSwitchingConversation] = useState(false);
  const prevConversationIdRef = useRef<string | null>(null);
  
  // 跟踪初始化状态，避免重复初始化
  const isInitializedRef = useRef(false);
  
  // 保存上次处理的会话ID和客户ID
  const lastProcessedConversationIdRef = useRef<string | null>(null);
  const conversationId = searchParams?.get('conversationId');
  const customerId = searchParams?.get('customerId');
  const [selectedCustomerId, setSelectedCustomerId] = useState<string | null>(customerId);

  // 当会话ID变化时，显示切换状态
  useEffect(() => {
    if (!conversationId || !prevConversationIdRef.current) {
      prevConversationIdRef.current = conversationId;
      return;
    }
    
    if (conversationId !== prevConversationIdRef.current) {
      // 显示切换状态
      setIsSwitchingConversation(true);
      
      // 300ms后隐藏切换状态
      const timer = setTimeout(() => {
        setIsSwitchingConversation(false);
        prevConversationIdRef.current = conversationId;
      }, 300);
      
      return () => clearTimeout(timer);
    }
  }, [conversationId]);

  // 监听URL参数变化
  useEffect(() => {
    const urlCustomerId = searchParams?.get('customerId');
    const urlConversationId = searchParams?.get('conversationId');
    
    console.log(`URL参数变化: customerId=${urlCustomerId}, conversationId=${urlConversationId}`);
    
    // 如果URL中的客户ID与当前选中的不同，更新选中状态
    if (urlCustomerId !== selectedCustomerId) {
      console.log(`更新选中的客户ID: ${urlCustomerId}`);
      setSelectedCustomerId(urlCustomerId);
    }
    
    // 如果URL中同时包含customerId和conversationId，但lastProcessedConversationIdRef不同，
    // 说明这是一个新的会话选择，更新上次处理的会话ID
    if (urlCustomerId && urlConversationId && 
        lastProcessedConversationIdRef.current !== urlConversationId) {
      console.log(`更新上次处理的会话ID: ${urlConversationId}`);
      lastProcessedConversationIdRef.current = urlConversationId;
    }
  }, [searchParams, selectedCustomerId]);

  // 处理客户选择
  const handleCustomerSelect = (customerId: string, conversationId?: string) => {
    setSelectedCustomerId(customerId);
    
    if (conversationId) {
      // 如果有指定的会话ID，直接跳转
      router.push(`/consultant/chat?customerId=${customerId}&conversationId=${conversationId}`, { scroll: false });
    } else {
      // 如果没有会话ID，只更新客户ID
      router.push(`/consultant/chat?customerId=${customerId}`, { scroll: false });
    }
  };

  // 初始化聊天页面
  useEffect(() => {
    // 等待认证完成
    if (authLoading) {
      console.log('认证加载中，等待认证完成...');
      return;
    }
    
    // 检查登录状态
    if (!authService.isLoggedIn()) {
      console.log('用户未登录，不执行初始化');
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
    
    // 防止在同一渲染周期内多次执行初始化
    if (isInitializedRef.current) {
      console.log('已初始化，跳过重复初始化');
      return;
    }
    
    // 设置加载状态
    if (!isLoading) {
      setIsLoading(true);
    }
    
    console.log('开始初始化顾问聊天页面...');
    
    const initializeChat = async () => {
      try {
        // 如果已有conversationId和customerId，表示已经有特定的会话被选中
        if (customerId && conversationId) {
          console.log(`已有特定会话: 客户ID=${customerId}, 会话ID=${conversationId}`);
          setSelectedCustomerId(customerId);
          setIsLoading(false);
          return;
        }
        
        // 如果只有customerId但没有conversationId
        if (customerId && !conversationId) {
          console.log(`有客户ID但无会话ID: 客户ID=${customerId}，尝试获取该客户的会话`);
          try {
            const conversations = await getCustomerConversations(customerId);
            if (conversations && conversations.length > 0) {
              // 找到活跃的会话或使用第一个会话
              const activeConversation = conversations.find(conv => conv.status === 'active') || conversations[0];
              if (activeConversation) {
                console.log(`找到客户${customerId}的会话:`, activeConversation.id);
                // 更新URL，包含会话ID
                router.push(`/consultant/chat?customerId=${customerId}&conversationId=${activeConversation.id}`, { scroll: false });
                return;
              }
            } else {
              console.log(`客户${customerId}没有会话记录`);
            }
          } catch (error) {
            console.error(`获取客户${customerId}的会话失败:`, error);
          }
        }
        
        // 如果URL中没有客户ID参数，自动选择第一个客户
        if (!customerId) {
          console.log('URL中没有客户ID，尝试加载默认客户...');
          try {
            const customers = await getCustomerList();
            if (customers && customers.length > 0) {
              console.log('找到客户列表，选择第一个客户:', customers[0].name);
              
              // 获取该客户的会话
              const conversations = await getCustomerConversations(customers[0].id);
              console.log(`获取到客户${customers[0].id}的会话列表:`, conversations.length > 0 ? conversations.length + '个会话' : '无会话');
              
              // 找到活跃的会话或使用第一个会话
              const activeConversation = conversations.find(conv => conv.status === 'active') || conversations[0];
              
              if (activeConversation) {
                console.log('找到客户会话:', activeConversation.id);
                // 自动导航到该客户的会话页面，确保同时传递customerId和conversationId
                router.push(`/consultant/chat?customerId=${customers[0].id}&conversationId=${activeConversation.id}`, { scroll: false });
              } else {
                // 如果没有会话，只导航到客户页面
                console.log('未找到客户会话，只选择客户:', customers[0].id);
                router.push(`/consultant/chat?customerId=${customers[0].id}`, { scroll: false });
              }
            } else {
              console.log('没有找到客户列表或客户列表为空');
            }
          } catch (error) {
            console.error('加载默认客户失败:', error);
          }
        }
        
        // 顾问端不需要自动创建会话，等待客户选择
        console.log('顾问聊天页面初始化完成，等待选择客户');
      } catch (err) {
        console.error('初始化聊天失败:', err);
        setError('加载页面失败，请刷新页面重试');
      } finally {
        // 设置初始化标志，防止重复初始化
        isInitializedRef.current = true;
        setIsLoading(false);
      }
    };
    
    initializeChat();
    
    // 设置超时，如果10秒后仍在加载，则认为出现了问题
    const timeoutId = setTimeout(() => {
      if (isLoading) {
        console.log('加载超时，重置状态');
        setIsLoading(false);
        if (!error) {
          setError('加载超时，请刷新页面重试');
        }
      }
    }, 10000); // 10秒超时
    
    return () => {
      clearTimeout(timeoutId);
    };
  }, [conversationId, router, isLoading, error, authLoading, user, customerId]);
  
  // 监听认证状态变化，重置初始化状态
  useEffect(() => {
    if (!authLoading && user && isInitializedRef.current) {
      // 如果认证状态变化（例如令牌刷新后），但不重新初始化
      console.log('认证状态变化，但保持初始化状态');
    }
    
    // 如果用户登出，重置初始化状态
    if (!authLoading && !user) {
      console.log('用户已登出，重置初始化状态');
      isInitializedRef.current = false;
    }
  }, [authLoading, user]);

  if (error) {
    return (
      <div className="flex h-full flex-col items-center justify-center bg-gray-50">
        <div className="text-red-500 text-lg mb-4">{error}</div>
        <div className="text-gray-500 text-sm">正在重定向...</div>
      </div>
    );
  }
  
  // 强制稳定的布局结构，避免加载过程中的闪烁
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
              onCustomerSelect={handleCustomerSelect}
              selectedCustomerId={selectedCustomerId}
            />
          </div>
          
          {/* 中间：聊天窗口 */}
          <div className="flex-1 overflow-hidden relative">
            {conversationId ? (
              <ChatWindow 
                key={conversationId}
                conversationId={conversationId}
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
      
      {/* 全屏加载状态覆盖层 */}
      {(isLoading || authLoading) && (
        <div className="absolute inset-0 bg-white bg-opacity-70 flex items-center justify-center z-50">
          <div className="flex flex-col items-center">
            <LoadingSpinner size="lg" />
            <p className="mt-4 text-gray-600">加载中...</p>
          </div>
        </div>
      )}
      
      {/* 错误状态 */}
      {error && !isLoading && (
        <div className="absolute inset-0 bg-white bg-opacity-90 flex items-center justify-center z-50">
          <div className="text-center">
            <div className="text-red-500 text-lg mb-4">{error}</div>
            <button
              onClick={() => {
                setError(null);
                setIsLoading(true);
                isInitializedRef.current = false;
              }}
              className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors"
            >
              重试
            </button>
          </div>
        </div>
      )}
    </div>
  );
} 