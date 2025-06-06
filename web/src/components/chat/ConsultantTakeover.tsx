'use client';

import { useState, useEffect, useCallback } from 'react';
import { useAuthContext } from '@/contexts/AuthContext';
import { 
  takeoverConversation,
  switchBackToAI,
  syncConsultantTakeoverStatus,
  isConsultantMode
} from '@/service/chatService';

interface ConsultantTakeoverProps {
  conversationId?: string | null;
  className?: string;
}

export default function ConsultantTakeover({ 
  conversationId, 
  className = "flex-shrink-0" 
}: ConsultantTakeoverProps) {
  const { user } = useAuthContext();
  const [isConsultantTakeover, setIsConsultantTakeover] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // 只对顾问角色显示
  const isConsultant = user?.currentRole === 'consultant';

  // 切换会话时，从数据库获取接管状态
  useEffect(() => {
    const fetchTakeoverStatus = async () => {
      if (!conversationId || !isConsultant) {
        setIsConsultantTakeover(false);
        return;
      }

      try {
        console.log('ConsultantTakeover: 获取会话接管状态', conversationId);
        const status = await isConsultantMode(conversationId);
        console.log('ConsultantTakeover: 当前接管状态', status);
        setIsConsultantTakeover(status);
      } catch (error) {
        console.error('获取顾问接管状态失败:', error);
        setIsConsultantTakeover(false);
      }
    };

    fetchTakeoverStatus();
  }, [conversationId, isConsultant]);

  // 切换顾问接管状态
  const toggleConsultantMode = useCallback(async () => {
    if (!conversationId || isLoading || !isConsultant) return;

    try {
      setIsLoading(true);
      console.log('ConsultantTakeover: 切换接管状态', { 
        conversationId, 
        currentStatus: isConsultantTakeover 
      });

      let success = false;
      
      if (isConsultantTakeover) {
        // 切换回AI助手
        console.log('ConsultantTakeover: 切换回AI助手');
        success = await switchBackToAI(conversationId);
      } else {
        // 顾问接管
        console.log('ConsultantTakeover: 顾问接管');
        success = await takeoverConversation(conversationId);
      }

      if (success) {
        // 同步数据库状态
        await syncConsultantTakeoverStatus(conversationId);
        
        // 更新本地状态
        const newStatus = !isConsultantTakeover;
        setIsConsultantTakeover(newStatus);
        
        console.log('ConsultantTakeover: 状态切换成功', { 
          oldStatus: isConsultantTakeover, 
          newStatus 
        });
      } else {
        console.error('ConsultantTakeover: 状态切换失败');
      }
    } catch (error) {
      console.error('切换顾问模式失败:', error);
    } finally {
      setIsLoading(false);
    }
  }, [conversationId, isConsultantTakeover, isLoading, isConsultant]);

  // 如果不是顾问角色，不渲染组件
  if (!isConsultant) {
    return null;
  }

  return (
    <button 
      className={`${className} ${
        isConsultantTakeover 
          ? 'text-green-500' 
          : 'text-gray-500 hover:text-gray-700'
      } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
      onClick={toggleConsultantMode}
      disabled={isLoading || !conversationId}
      title={
        isLoading 
          ? '正在切换...' 
          : isConsultantTakeover 
            ? "切换回AI助手" 
            : "顾问接管"
      }
    >
      <svg
        className="h-6 w-6"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d={isConsultantTakeover 
            ? "M13 10V3L4 14h7v7l9-11h-7z" // 闪电图标，表示切换回AI
            : "M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" // 用户图标，表示顾问接管
          }
        />
      </svg>
    </button>
  );
} 