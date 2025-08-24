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

  return {
    conversations,
    loadingConversations,
    selectedConversation,
    getConversation,
    setSelectedConversation
  };
};
