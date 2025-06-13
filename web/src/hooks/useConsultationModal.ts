'use client';

import { useState, useCallback } from 'react';
import { ConsultationHistoryItem } from '@/types/chat';
import { useRouter } from 'next/navigation';

export function useConsultationModal(customerId?: string) {
  const router = useRouter();
  const [showHistoryModal, setShowHistoryModal] = useState(false);
  const [selectedHistory, setSelectedHistory] = useState<ConsultationHistoryItem | null>(null);

  // 打开历史咨询详情
  const openHistoryDetail = useCallback((history: ConsultationHistoryItem) => {
    setSelectedHistory(history);
    setShowHistoryModal(true);
  }, []);

  // 关闭历史咨询详情
  const closeHistoryDetail = useCallback(() => {
    setShowHistoryModal(false);
    setSelectedHistory(null);
  }, []);

  // 查看历史会话消息
  const viewHistoryConversation = useCallback((conversationId: string) => {
    closeHistoryDetail();
    if (customerId) {
      router.push(`/consultant/chat?customerId=${customerId}&conversationId=${conversationId}`);
    }
  }, [customerId, router, closeHistoryDetail]);


  return {
    showHistoryModal,
    selectedHistory,
    openHistoryDetail,
    closeHistoryDetail,
    viewHistoryConversation,
  };
} 