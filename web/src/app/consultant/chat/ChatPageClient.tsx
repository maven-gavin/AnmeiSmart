'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import ChatLayout from '@/components/chat/ChatLayout'
import ChatWindow from '@/components/chat/ChatWindow'
import ConversationList from '@/components/chat/ConversationList'
import CustomerProfile from '@/components/chat/CustomerProfile'
import { getConversations } from '@/service/chatService';
import LoadingSpinner from '@/components/ui/LoadingSpinner';

export default function ChatPageClient() {
  const router = useRouter();
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

  useEffect(() => {
    // 防止在同一渲染周期内多次执行初始化
    if (isInitializedRef.current) {
      return;
    }
    
    const initializeChat = async () => {
      try {
        if (!conversationId) {
          // 如果URL中没有会话ID，获取第一个会话并重定向
          const conversations = await getConversations();
          
          if (conversations && conversations.length > 0) {
            const firstConversationId = conversations[0].id;
            console.log(`未指定会话ID，重定向到第一个会话: ${firstConversationId}`);
            
            // 如果上一次处理的会话ID与当前需要重定向的不同，则执行重定向
            if (lastProcessedConversationIdRef.current !== firstConversationId) {
              lastProcessedConversationIdRef.current = firstConversationId;
              router.replace(`?conversationId=${firstConversationId}`, { scroll: false });
            }
          } else {
            console.error('没有可用的会话');
            setError('没有可用的会话');
          }
        } else {
          // 记录当前处理的会话ID
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
    
    // 设置超时，如果5秒后仍在加载，则认为出现了问题
    const timeoutId = setTimeout(() => {
      if (isLoading) {
        console.log('加载超时，重置状态');
        setIsLoading(false);
        if (!error) {
          setError('加载超时，请刷新页面重试');
        }
      }
    }, 5000);
    
    return () => {
      clearTimeout(timeoutId);
    };
  }, [conversationId, router, isLoading, error]);
  
  // 强制稳定的布局结构，避免加载过程中的闪烁
  return (
    <div className="h-full w-full relative">
      {/* 主聊天布局 - 即使在加载时也保持固定结构 */}
      <ChatLayout
        conversationList={<ConversationList />}
        chatWindow={
          <div className="relative h-full w-full">
            <ChatWindow 
              key={conversationId || 'empty'}
              conversationId={conversationId || ''}
            />
            
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
        customerProfile={<CustomerProfile conversationId={conversationId || ''} />}
      />
      
      {/* 全屏加载状态覆盖层 */}
      {isLoading && (
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
              onClick={() => window.location.reload()}
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