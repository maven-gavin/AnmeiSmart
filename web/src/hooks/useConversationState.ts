import { useState, useEffect } from 'react';
import { Conversation } from '@/types/chat';
import { getConversations, getConversationDetails } from '@/service/chatService';

export const useConversationState = () => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loadingConversations, setLoadingConversations] = useState(true);
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null);

  // 加载会话列表
  useEffect(() => {
    const loadConversations = async () => {
      try {
        setLoadingConversations(true);
        const data = await getConversations();
        setConversations(data);
      } catch (error) {
        console.error('加载会话列表失败:', error);
      } finally {
        setLoadingConversations(false);
      }
    };

    loadConversations();
  }, []);

  // 获取指定会话详情
  const getConversation = async (conversationId: string): Promise<Conversation | null> => {
    try {
      const conversation = await getConversationDetails(conversationId);
      setSelectedConversation(conversation);
      return conversation;
    } catch (error) {
      console.error('获取会话详情失败:', error);
      return null;
    }
  };

  // 清除未读消息数
  const clearUnreadCount = (conversationId: string) => {
    setConversations(prev => prev.map(conv => {
      if (conv.id === conversationId && conv.unreadCount > 0) {
        return { ...conv, unreadCount: 0 };
      }
      return conv;
    }));
    
    // 如果当前选中的会话就是目标会话，也更新选中状态
    if (selectedConversation?.id === conversationId && selectedConversation.unreadCount > 0) {
      setSelectedConversation(prev => prev ? { ...prev, unreadCount: 0 } : null);
    }
  };

  // 更新未读消息数
  const updateUnreadCount = (conversationId: string, increment: number = 1) => {
    setConversations(prev => prev.map(conv => {
      if (conv.id === conversationId) {
        return { ...conv, unreadCount: (conv.unreadCount || 0) + increment };
      }
      return conv;
    }));
  };

  return {
    conversations,
    loadingConversations,
    selectedConversation,
    getConversation,
    setSelectedConversation,
    clearUnreadCount,
    updateUnreadCount
  };
};
