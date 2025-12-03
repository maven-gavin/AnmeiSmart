import { useState, useCallback, useRef } from 'react';
import { Message } from '@/types/chat';
import { getConversationMessages, markMessageAsImportant } from '@/service/chatService';
import toast from 'react-hot-toast';

export const useMessageState = (conversationId: string | null) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loadingMessages, setLoadingMessages] = useState(false);
  // 跟踪正在加载的会话ID，避免重复加载
  const loadingConversationIdRef = useRef<string | null>(null);
  // 跟踪上一次加载的消息数量，用于判断是否需要更新
  const prevMessagesLengthRef = useRef<number>(0);

  // 手动加载消息列表
  const loadMessages = useCallback(async (forceRefresh: boolean = false, silent: boolean = false) => {
    if (!conversationId) {
      setMessages([]);
      loadingConversationIdRef.current = null;
      prevMessagesLengthRef.current = 0;
      return;
    }

    // 如果正在加载同一个会话，且不是强制刷新，则跳过
    if (loadingConversationIdRef.current === conversationId && !forceRefresh) {
      console.log('消息正在加载中，跳过重复加载:', conversationId);
      return;
    }

    try {
      loadingConversationIdRef.current = conversationId;
      if (!silent) setLoadingMessages(true);
      
      const data = await getConversationMessages(conversationId, forceRefresh);
      
      // 只有当消息数量或内容真正变化时才更新状态
      // 避免相同内容的数组引用变化导致不必要的更新
      setMessages(prev => {
        // 如果消息数量相同，检查内容是否真的变化
        if (prev.length === data.length && prev.length > 0) {
          // 比较最后一条消息的ID，如果相同则认为内容未变化
          const prevLastId = prev[prev.length - 1]?.id;
          const dataLastId = data[data.length - 1]?.id;
          if (prevLastId === dataLastId) {
            console.log('消息内容未变化，跳过更新:', conversationId);
            return prev; // 返回原数组，避免触发更新
          }
        }
        
        // 消息数量或内容有变化，更新状态
        prevMessagesLengthRef.current = data.length;
        return data;
      });
    } catch (error) {
      console.error('加载消息失败:', error);
    } finally {
      if (!silent) setLoadingMessages(false);
      // 延迟重置加载标志，避免快速连续调用
      setTimeout(() => {
        if (loadingConversationIdRef.current === conversationId) {
          loadingConversationIdRef.current = null;
        }
      }, 100);
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
