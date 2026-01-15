'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { ConsultationHistoryItem } from '@/types/chat';
import { getCustomerConsultationHistory } from '@/service/chatService';
import { customerService, type CustomerProfile as ICustomerProfile } from '@/service/customerService';

export function useCustomerProfile(customerId?: string, currentConversationId?: string) {
  const [profile, setProfile] = useState<ICustomerProfile | null>(null);
  const [consultationHistory, setConsultationHistory] = useState<ConsultationHistoryItem[]>([]);
  const [currentConsultation, setCurrentConsultation] = useState<ConsultationHistoryItem | undefined>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const retryRef = useRef(0);

  const fetchProfile = useCallback(async () => {
    if (!customerId) {
      setLoading(false);
      setProfile(null);
      return;
    }

    setLoading(true);
    setError(null);
    
    try {
      console.log(`开始获取客户档案，客户ID: ${customerId}`);
      const profileData = await customerService.getCustomerProfile(customerId);
      
      if (profileData) {
        console.log('获取客户档案成功:', profileData);
        setProfile(profileData);
        retryRef.current = 0;
        
        const history = await getCustomerConsultationHistory(customerId);
        setConsultationHistory(history);

        // 指定当前的咨询总结
        const currentItem = history.find((item) => item.id === currentConversationId);
        setCurrentConsultation(currentItem);
      } else {
        setProfile(null);
        setError(null);
        if (retryRef.current < 1) {
          retryRef.current += 1;
          setTimeout(() => {
            fetchProfile();
          }, 1200);
        }
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '获取客户档案失败';
      setError(errorMessage);
      console.error('获取客户档案失败:', error);
    } finally {
      setLoading(false);
    }
  }, [customerId, currentConversationId]);
  
  useEffect(() => {
    fetchProfile();
  }, [fetchProfile]);

  return {
    profile,
    consultationHistory,
    currentConsultation,
    loading,
    error,
    refetch: fetchProfile
  };
} 