import { useState, useCallback } from 'react';
import { Message } from '@/types/chat';
import { getConversationMessages, markMessageAsImportant } from '@/service/chatService';
import toast from 'react-hot-toast';

export const useMessageState = (conversationId: string | null) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loadingMessages, setLoadingMessages] = useState(false);

  // 手动加载消息列表
  const loadMessages = useCallback(async (forceRefresh: boolean = false, silent: boolean = false) => {
    if (!conversationId) {
      setMessages([]);
      return;
    }

    try {
      if (!silent) setLoadingMessages(true);
      const data = await getConversationMessages(conversationId, forceRefresh);
      setMessages(data);
    } catch (error) {
      console.error('加载消息失败:', error);
    } finally {
      if (!silent) setLoadingMessages(false);
    }
  }, [conversationId]);

  // 保存消息（添加或更新）
  const saveMessage = useCallback((message: Message) => {
    setMessages(prev => {
      // 检查消息是否已存在（通过id或localId）
      const existingIndex = prev.findIndex(msg => 
        (message.id && msg.id === message.id) || 
        (message.localId && msg.localId === message.localId)
      );
      
      if (existingIndex >= 0) {
        // 消息已存在，更新它
        const updatedMessages = [...prev];
        updatedMessages[existingIndex] = { ...updatedMessages[existingIndex], ...message };
        return updatedMessages;
      } else {
        // 消息不存在，添加新消息
        return [...prev, message];
      }
    });
  }, []);

  // 切换消息重点标记
  const toggleMessageImportant = useCallback(async (messageId: string, currentStatus = false) => {
    if (!conversationId) return;

    try {
      const result = await markMessageAsImportant(conversationId, messageId, !currentStatus);
      if (result) {
        toast.success(!currentStatus ? '消息已标记为重点' : '已取消重点标记');
        // 更新本地消息状态
        setMessages(prev => 
          prev.map(msg => msg.id === messageId ? { ...msg, is_important: !currentStatus } : msg)
        );
      } else {
        toast.error('操作失败，请重试');
      }
    } catch (error) {
      console.error('标记重点消息失败:', error);
      toast.error('标记重点消息失败，请检查网络连接');
    }
  }, [conversationId]);

  return {
    // 基础消息状态
    messages,
    loadingMessages,
    saveMessage,
    setMessages,
    
    // 重点消息相关
    toggleMessageImportant,
    
    // 加载控制
    loadMessages
  };
};
