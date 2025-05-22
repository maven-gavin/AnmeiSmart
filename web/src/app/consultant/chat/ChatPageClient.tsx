'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import ChatLayout from '@/components/chat/ChatLayout'
import ChatWindow from '@/components/chat/ChatWindow'
import ConversationList from '@/components/chat/ConversationList'
import CustomerProfile from '@/components/chat/CustomerProfile'
import { getConversations, createConversation } from '@/service/chatService';
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
  
  // 保存上次处理的会话ID
  const lastProcessedConversationIdRef = useRef<string | null>(null);
  const conversationId = searchParams?.get('conversationId');

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

  // 初始化聊天页面和会话
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
    
    // 防止在同一渲染周期内多次执行初始化
    if (isInitializedRef.current) {
      console.log('已初始化，跳过重复初始化');
      return;
    }
    
    // 设置加载状态
    if (!isLoading) {
      setIsLoading(true);
    }
    
    console.log('开始初始化聊天页面...');
    
    const initializeChat = async () => {
      try {
        // 先检查URL中是否有会话ID
        if (!conversationId) {
          console.log('URL中没有会话ID，尝试获取会话列表');
          
          // 如果URL中没有会话ID，获取会话列表
          const conversations = await getConversations();
          
          if (conversations && conversations.length > 0) {
            // 有会话时，选择第一个
            const firstConversationId = conversations[0].id;
            console.log(`找到会话列表，重定向到第一个会话: ${firstConversationId}`);
            
            // 记录处理的会话ID
            lastProcessedConversationIdRef.current = firstConversationId;
            router.replace(`?conversationId=${firstConversationId}`, { scroll: false });
          } else {
            // 没有会话时，创建一个新会话
            console.log('没有可用的会话，创建新会话');
            try {
              // 创建新会话
              const newConversation = await createConversation();
              console.log(`创建了新会话: ${newConversation.id}`);
              
              // 记录处理的会话ID
              lastProcessedConversationIdRef.current = newConversation.id;
              router.replace(`?conversationId=${newConversation.id}`, { scroll: false });
            } catch (createErr) {
              console.error('创建会话失败:', createErr);
              setError('无法创建新会话，请刷新页面重试');
            }
          }
        } else {
          // 记录当前处理的会话ID
          console.log(`URL中有会话ID: ${conversationId}`);
          lastProcessedConversationIdRef.current = conversationId;
        }
      } catch (err) {
        console.error('初始化聊天失败:', err);
        setError('加载会话失败，请刷新页面重试');
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
  }, [conversationId, router, isLoading, error, authLoading, user]);
  
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
  
  // 强制稳定的布局结构，避免加载过程中的闪烁
  return (
    <div className="h-full w-full relative">
      {/* 主聊天布局 - 即使在加载时也保持固定结构 */}
      <ChatLayout
        conversationList={<ConversationList />}
        chatWindow={
          <div className="relative h-full w-full">
            {conversationId ? (
              <ChatWindow 
                key={conversationId}
                conversationId={conversationId}
              />
            ) : (
              <div className="flex h-full items-center justify-center text-gray-400">
                正在加载会话...
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
          </div>
        }
        customerProfile={conversationId ? <CustomerProfile conversationId={conversationId} /> : null}
      />
      
      {/* 全屏加载状态覆盖层 */}
      {(isLoading || authLoading) && (
        <div className="absolute inset-0 bg-white bg-opacity-70 flex items-center justify-center z-50">
          <div className="flex flex-col items-center">
            <LoadingSpinner size="large" />
            <p className="mt-4 text-gray-600">加载中...</p>
          </div>
        </div>
      )}
      
      {/* 错误信息覆盖层 */}
      {error && (
        <div className="absolute inset-0 bg-white bg-opacity-90 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg shadow-lg max-w-md text-center">
            <div className="text-red-500 text-lg mb-4">{error}</div>
            <button
              onClick={() => {
                setError(null);
                isInitializedRef.current = false;
                window.location.reload();
              }}
              className="rounded-md bg-orange-500 px-4 py-2 text-white hover:bg-orange-600"
            >
              刷新页面
            </button>
          </div>
        </div>
      )}
    </div>
  );
} 