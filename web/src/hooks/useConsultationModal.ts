'use client';

import { useState, useCallback } from 'react';
import { ConsultationHistoryItem, Message } from '@/types/chat';
import { getConversationMessages } from '@/service/chatService';
import { useRouter } from 'next/navigation';

export function useConsultationModal(customerId?: string) {
  const router = useRouter();
  const [showHistoryModal, setShowHistoryModal] = useState(false);
  const [selectedHistory, setSelectedHistory] = useState<ConsultationHistoryItem | null>(null);
  const [showMessagesPreview, setShowMessagesPreview] = useState(false);
  const [historyMessages, setHistoryMessages] = useState<Message[]>([]);
  const [loadingMessages, setLoadingMessages] = useState(false);

  // 打开历史咨询详情
  const openHistoryDetail = useCallback((history: ConsultationHistoryItem) => {
    setSelectedHistory(history);
    setShowHistoryModal(true);
    setShowMessagesPreview(false);
    setHistoryMessages([]);
  }, []);

  // 关闭历史咨询详情
  const closeHistoryDetail = useCallback(() => {
    setShowHistoryModal(false);
    setSelectedHistory(null);
    setShowMessagesPreview(false);
    setHistoryMessages([]);
  }, []);

  // 查看历史会话消息
  const viewHistoryConversation = useCallback((conversationId: string) => {
    closeHistoryDetail();
    if (customerId) {
      router.push(`/consultant/chat?customerId=${customerId}&conversationId=${conversationId}`);
    }
  }, [customerId, router, closeHistoryDetail]);

  // 预览历史消息
  const previewHistoryMessages = useCallback(async (conversationId: string) => {
    if (showMessagesPreview && historyMessages.length > 0) {
      setShowMessagesPreview(false);
      return;
    }
    
    setLoadingMessages(true);
    
    try {
      const messages = await getConversationMessages(conversationId, true);
      setHistoryMessages(messages);
      setShowMessagesPreview(true);
    } catch (error) {
      console.error('获取历史消息失败:', error);
    } finally {
      setLoadingMessages(false);
    }
  }, [showMessagesPreview, historyMessages.length]);

  // 切换消息预览状态
  const toggleMessagesPreview = useCallback(() => {
    setShowMessagesPreview(!showMessagesPreview);
  }, [showMessagesPreview]);

  return {
    showHistoryModal,
    selectedHistory,
    showMessagesPreview,
    historyMessages,
    loadingMessages,
    openHistoryDetail,
    closeHistoryDetail,
    viewHistoryConversation,
    previewHistoryMessages,
    toggleMessagesPreview
  };
} 