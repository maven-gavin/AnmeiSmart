import { useState, useEffect, useCallback } from 'react';
import { Conversation } from '@/types/chat';
import { 
  getConversations, 
  getConversationDetails, 
  markConversationAsRead,
  updateUnreadCountInCache,
  updateLastMessageInCache
} from '@/service/chatService';

export const useConversationState = () => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loadingConversations, setLoadingConversations] = useState(true);
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null);

  // 刷新会话列表
  const refreshConversations = useCallback(async (silent = false) => {
    try {
      if (!silent) setLoadingConversations(true);
      const data = await getConversations();
      setConversations(data);
    } catch (error) {
      console.error('刷新会话列表失败:', error);
    } finally {
      if (!silent) setLoadingConversations(false);
    }
  }, []);

  // 初始加载
  useEffect(() => {
    refreshConversations();
  }, [refreshConversations]);

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
  const clearUnreadCount = async (conversationId: string) => {
    // 1. 乐观更新：立即更新 UI
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

    // 2. 调用后端 API
    try {
      await markConversationAsRead(conversationId);
    } catch (error) {
      console.error('标记会话已读失败:', error);
      // 如果失败，理论上应该回滚 UI，但未读数这种状态回滚可能打扰用户体验，
      // 且下次刷新会恢复，所以这里仅记录日志
    }
  };

  // 更新未读消息数
  const updateUnreadCount = (conversationId: string, increment: number = 1) => {
    setConversations(prev => prev.map(conv => {
      if (conv.id === conversationId) {
        // 1. 更新本地状态
        const newCount = (conv.unreadCount || 0) + increment;
        
        // 2. 更新全局缓存 (异步)
        updateUnreadCountInCache(conversationId, increment).catch(e => 
          console.error('更新未读消息缓存失败:', e)
        );
        
        return { ...conv, unreadCount: newCount };
      }
      return conv;
    }));
  };

  // 更新最后一条消息（用于实时预览）
  const updateLastMessage = (conversationId: string, message: any) => {
    setConversations(prev => prev.map(conv => {
      if (conv.id === conversationId) {
        // 1. 更新全局缓存 (异步)
        updateLastMessageInCache(conversationId, message).catch(e =>
          console.error('更新最后一条消息缓存失败:', e)
        );

        // 2. 更新本地状态
        return { 
          ...conv, 
          lastMessage: message,
          updatedAt: message.timestamp || new Date().toISOString()
        };
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
    updateUnreadCount,
    updateLastMessage,
    refreshConversations // 新增：暴露刷新方法
  };
};
