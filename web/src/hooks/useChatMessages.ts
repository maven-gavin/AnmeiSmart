'use client';

import { useState, useCallback, useMemo } from 'react';
import { Message, Conversation } from '@/types/chat';
import { 
  getConversationMessages,
  markMessageAsImportant,
  getOrCreateConversation,
  sendTextMessage,
  sendImageMessage,
  sendVoiceMessage,
  getAIResponse,
  syncConsultantTakeoverStatus
} from '@/service/chatService';
import { useRouter } from 'next/navigation';

/**
 * 管理聊天消息的自定义Hook
 */
export function useChatMessages(conversationId: string | null) {
  const router = useRouter();
  
  // 基本状态
  const [messages, setMessages] = useState<Message[]>([]);
  const [importantMessages, setImportantMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [networkError, setNetworkError] = useState<string | null>(null);
  const [isConsultantTakeover, setIsConsultantTakeover] = useState(false);
  
  // 搜索相关状态
  const [searchResults, setSearchResults] = useState<Message[]>([]);
  const [selectedMessageId, setSelectedMessageId] = useState<string | null>(null);
  
  // 获取会话消息
  const fetchMessages = useCallback(async (forceRefresh: boolean = false) => {
    try {
      if (!conversationId) return;
      
      setIsLoading(true);
      setNetworkError(null); // 清除之前的错误
      
      // 获取消息
      try {
        const fetchedMessages = await getConversationMessages(conversationId, forceRefresh);
        setMessages(fetchedMessages);
        
        // 获取重点消息
        const important = fetchedMessages.filter(msg => msg.isImportant);
        setImportantMessages(important);
      } catch (error) {
        console.error('获取消息出错:', error);
        setNetworkError('加载消息失败，请重试');
      }
    
      // 检查顾问接管状态
      try {
        const isConsultantModeActive = await syncConsultantTakeoverStatus(conversationId);
        setIsConsultantTakeover(isConsultantModeActive);
      } catch (error) {
        console.error('同步顾问状态失败:', error);
      }
    } catch (error) {
      console.error('获取数据出错:', error);
    } finally {
      setIsLoading(false);
    }
  }, [conversationId]);
  
  // 静默获取消息函数，不设置加载状态
  const silentFetchMessages = useCallback(async () => {
    try {
      if (!conversationId) return;
      
      // 获取消息
      try {
        const fetchedMessages = await getConversationMessages(conversationId, true);
        setMessages(fetchedMessages);
        
        // 获取重点消息
        const important = fetchedMessages.filter(msg => msg.isImportant);
        setImportantMessages(important);
        
        // 同步顾问接管状态
        const isConsultantModeActive = await syncConsultantTakeoverStatus(conversationId);
        setIsConsultantTakeover(isConsultantModeActive);
      } catch (error) {
        console.error('静默获取消息出错:', error);
      }
    } catch (error) {
      console.error('静默获取数据出错:', error);
    }
  }, [conversationId]);
  
  // 切换消息重点标记
  const toggleMessageImportant = useCallback(async (messageId: string, currentStatus: boolean) => {
    if (!conversationId) return;
    
    try {
      // 乐观更新UI
      setMessages(prev => 
        prev.map(msg => 
          msg.id === messageId 
            ? { ...msg, isImportant: !currentStatus } 
            : msg
        )
      );
      
      // 更新重点消息列表
      if (!currentStatus) {
        // 添加到重点消息
        setImportantMessages(prev => [
          ...prev, 
          messages.find(msg => msg.id === messageId)!
        ]);
      } else {
        // 从重点消息中移除
        setImportantMessages(prev => 
          prev.filter(msg => msg.id !== messageId)
        );
      }
      
      // 调用API更新服务器状态
      await markMessageAsImportant(conversationId, messageId, !currentStatus);
    } catch (error) {
      console.error('更新消息重点状态失败:', error);
      // 发生错误时回滚UI状态
      fetchMessages(true);
    }
  }, [conversationId, messages, fetchMessages]);
  
  // 发送文本消息
  const sendTextMessageWithTyping = useCallback(async (message: string) => {
    if (!message.trim() || isSending) return null;
    
    try {
      setIsSending(true);
      
      // 如果没有会话ID，创建一个新会话
      let actualConversationId = conversationId;
      
      if (!actualConversationId) {
        try {
          const conversation = await getOrCreateConversation();
          actualConversationId = conversation.id;
          
          // 更新URL
          router.replace(`?conversationId=${conversation.id}`, { scroll: false });
        } catch (error) {
          console.error('创建会话失败:', error);
          setIsSending(false);
          return null;
        }
      }
      
      // 发送用户消息
      const userMessage = await sendTextMessage(actualConversationId, message);
      
      // 更新本地消息列表
      setMessages(prev => [...prev, userMessage]);
      
      // 在顾问未接管的情况下获取AI回复
      if (!isConsultantTakeover) {
        try {
          // 获取AI回复
          const aiResponse = await getAIResponse(actualConversationId, userMessage);
          
          if (aiResponse) {
            // 更新本地消息列表
            setMessages(prev => [...prev, aiResponse]);
          }
        } catch (error) {
          console.error('获取AI回复失败:', error);
        }
      }
      
      return userMessage;
    } catch (error) {
      console.error('发送消息失败:', error);
      return null;
    } finally {
      setIsSending(false);
    }
  }, [conversationId, isSending, isConsultantTakeover, router]);
  
  // 发送图片消息
  const sendImageMessageWithPreview = useCallback(async (imagePreview: string) => {
    if (!imagePreview || !conversationId || isSending) return null;
    
    setIsSending(true);
    try {
      // 发送图片消息
      await sendImageMessage(conversationId, imagePreview);
      
      // 更新消息列表
      silentFetchMessages();
      return true;
    } catch (error) {
      console.error('发送图片失败:', error);
      return null;
    } finally {
      setIsSending(false);
    }
  }, [conversationId, isSending, silentFetchMessages]);
  
  // 发送语音消息
  const sendVoiceMessageWithPreview = useCallback(async (audioPreview: string) => {
    if (!audioPreview || !conversationId || isSending) return null;
    
    setIsSending(true);
    try {
      // 发送语音消息
      await sendVoiceMessage(conversationId, audioPreview);
      
      // 更新消息列表
      silentFetchMessages();
      return true;
    } catch (error) {
      console.error('发送语音失败:', error);
      return null;
    } finally {
      setIsSending(false);
    }
  }, [conversationId, isSending, silentFetchMessages]);
  
  // 搜索聊天记录
  const searchChatMessages = useCallback((term: string) => {
    if (!term.trim()) {
      setSearchResults([]);
      setSelectedMessageId(null);
      return;
    }
    
    const normalizedTerm = term.toLowerCase();
    const results = messages.filter(msg => 
      typeof msg.content === 'string' && 
      msg.content.toLowerCase().includes(normalizedTerm) &&
      msg.type === 'text' // 只搜索文本消息
    );
    
    setSearchResults(results);
    
    // 如果有结果，选中第一条
    if (results.length > 0) {
      setSelectedMessageId(results[0].id);
    } else {
      setSelectedMessageId(null);
    }
  }, [messages]);
  
  // 分组后的消息
  const messageGroups = useMemo(() => {
    const formatMessageDate = (timestamp: string): string => {
      const date = new Date(timestamp);
      const today = new Date();
      const yesterday = new Date();
      yesterday.setDate(yesterday.getDate() - 1);
      
      // 格式化日期: 今天/昨天/具体日期
      if (date.toDateString() === today.toDateString()) {
        return '今天';
      } else if (date.toDateString() === yesterday.toDateString()) {
        return '昨天';
      } else {
        return `${date.getFullYear()}年${date.getMonth() + 1}月${date.getDate()}日`;
      }
    };
    
    const messagesToGroup = messages;
    const groups: { date: string; messages: Message[] }[] = [];
    
    // 按日期分组
    messagesToGroup.forEach((msg: Message) => {
      const dateStr = formatMessageDate(msg.timestamp);
      
      // 查找或创建日期组
      let group = groups.find(g => g.date === dateStr);
      if (!group) {
        group = { date: dateStr, messages: [] };
        groups.push(group);
      }
      
      group.messages.push(msg);
    });
    
    return groups;
  }, [messages]);
  
  return {
    messages,
    importantMessages,
    isLoading,
    isSending,
    networkError,
    isConsultantTakeover,
    searchResults,
    selectedMessageId,
    setSelectedMessageId,
    messageGroups,
    fetchMessages,
    silentFetchMessages,
    toggleMessageImportant,
    sendTextMessageWithTyping,
    sendImageMessageWithPreview,
    sendVoiceMessageWithPreview,
    searchChatMessages,
    setNetworkError,
    setIsConsultantTakeover
  };
} 