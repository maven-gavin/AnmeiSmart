import { useState, useCallback } from 'react';
import { Message } from '@/types/chat';
import { getConversationMessages, markMessageAsImportant } from '@/service/chatService';
import toast from 'react-hot-toast';

export const useMessageState = (conversationId: string | null) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [importantMessages, setImportantMessages] = useState<Message[]>([]);
  const [showImportantOnly, setShowImportantOnly] = useState(false);

  // 手动加载消息列表
  const loadMessages = useCallback(async (forceRefresh: boolean = false) => {
    if (!conversationId) {
      setMessages([]);
      setImportantMessages([]);
      return;
    }

    try {
      setLoadingMessages(true);
      const data = await getConversationMessages(conversationId, forceRefresh);
      setMessages(data);
      // 更新重点消息列表
      updateImportantMessages(data);
    } catch (error) {
      console.error('加载消息失败:', error);
    } finally {
      setLoadingMessages(false);
    }
  }, [conversationId]);

  // 更新重点消息列表
  const updateImportantMessages = useCallback((messageList?: Message[]) => {
    const targetMessages = messageList || messages;
    const important = targetMessages.filter(msg => msg.is_important);
    setImportantMessages(important);
  }, [messages]);

  // 添加消息到列表
  const addMessage = useCallback((message: Message) => {
    setMessages(prev => {
      const newMessages = [...prev, message];
      // 如果新消息是重点消息，更新重点消息列表
      if (message.is_important) {
        setImportantMessages(prevImportant => [...prevImportant, message]);
      }
      return newMessages;
    });
  }, []);

  // 更新消息
  const updateMessage = useCallback((messageId: string, updates: Partial<Message>) => {
    setMessages(prev => {
      const updatedMessages = prev.map(msg => 
        msg.id === messageId ? { ...msg, ...updates } : msg
      );
      
      // 如果更新涉及重点状态，更新重点消息列表
      if ('is_important' in updates) {
        updateImportantMessages(updatedMessages);
      }
      
      return updatedMessages;
    });
  }, [updateImportantMessages]);

  // 切换消息重点标记
  const toggleMessageImportant = useCallback(async (messageId: string, currentStatus = false) => {
    if (!conversationId) return;

    try {
      const result = await markMessageAsImportant(conversationId, messageId, !currentStatus);
      if (result) {
        toast.success(!currentStatus ? '消息已标记为重点' : '已取消重点标记');
        // 更新本地消息状态
        updateMessage(messageId, { is_important: !currentStatus });
      } else {
        toast.error('操作失败，请重试');
      }
    } catch (error) {
      console.error('标记重点消息失败:', error);
      toast.error('标记重点消息失败，请检查网络连接');
    }
  }, [conversationId, updateMessage]);

  // 切换是否只显示重点消息
  const toggleShowImportantOnly = useCallback(() => {
    setShowImportantOnly(prev => !prev);
  }, []);

  // 获取当前显示的消息（根据是否只显示重点消息）
  const getDisplayMessages = useCallback(() => {
    return showImportantOnly ? importantMessages : messages;
  }, [showImportantOnly, importantMessages, messages]);

  return {
    // 基础消息状态
    messages,
    loadingMessages,
    addMessage,
    updateMessage,
    setMessages,
    
    // 重点消息相关
    importantMessages,
    showImportantOnly,
    toggleMessageImportant,
    toggleShowImportantOnly,
    
    // 便捷方法
    getDisplayMessages,
    
    // 加载控制
    loadMessages
  };
};
