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
  
  // 跟踪初始化状态，避免重复初始化
  const isInitializedRef = useRef(false);
  
  // 检查URL中是否有会话ID参数
  const conversationId = searchParams?.get('conversationId');
  
  // 如果没有会话ID，获取会话列表并选择第一个
  useEffect(() => {
    // 防止在同一渲染周期内多次执行初始化
    if (isInitializedRef.current) {
      return;
    }
    
    const initializeChat = async () => {
      try {
        if (!conversationId) {
          setIsLoading(true);
          isInitializedRef.current = true;
          
          // 添加超时处理
          const timeoutPromise = new Promise<never>((_, reject) => {
            setTimeout(() => reject(new Error('获取会话列表超时')), 8000);
          });
          
          // 获取会话列表，带超时处理
          const conversationsPromise = getConversations();
          
          try {
            // 等待会话列表或超时
            const conversations = await Promise.race([conversationsPromise, timeoutPromise]);
            
            // 如果有会话，选择第一个
            if (conversations && conversations.length > 0) {
              console.log('找到会话列表，选择第一个:', conversations[0].id);
              
              // 重定向到带会话ID的URL，使用replace避免创建历史记录
              router.replace(`/consultant/chat?conversationId=${conversations[0].id}`, { scroll: false });
            } else {
              console.log('没有找到会话，需要创建一个');
              // 这种情况下让ChatWindow自己创建会话
              setIsLoading(false);
            }
          } catch (error) {
            console.error('获取会话列表超时或失败:', error);
            // 超时或失败时，让ChatWindow自己创建会话
            setIsLoading(false);
          }
        } else {
          // 已有会话ID，直接渲染
          setIsLoading(false);
        }
      } catch (error) {
        console.error('初始化聊天页面出错:', error);
        setError('加载会话列表失败');
        setIsLoading(false);
      }
    };
    
    initializeChat();
    
    // 组件卸载时清理
    return () => {
      isInitializedRef.current = false;
    };
  }, [conversationId, router]);
  
  // 显示加载状态
  if (isLoading && !conversationId) {
    return (
      <div className="fixed inset-0 flex h-screen w-full items-center justify-center bg-white z-50">
        <LoadingSpinner />
        <span className="ml-2 text-gray-600">加载会话列表...</span>
      </div>
    );
  }
  
  // 显示错误状态
  if (error) {
    return (
      <div className="flex h-screen w-full flex-col items-center justify-center">
        <div className="text-red-500 mb-4">{error}</div>
        <button
          onClick={() => {
            setError(null);
            setIsLoading(true);
            isInitializedRef.current = false;
            router.refresh();
          }}
          className="rounded-md bg-orange-500 px-4 py-2 text-white hover:bg-orange-600"
        >
          重试
        </button>
      </div>
    );
  }
  
  return (
    <ChatLayout
      conversationList={<ConversationList />}
      chatWindow={<ChatWindow />}
      customerProfile={<CustomerProfile />}
    />
  )
} 