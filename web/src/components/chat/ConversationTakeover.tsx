'use client';

import { useState, useEffect, useCallback } from 'react';
import { 
  takeoverConversation,
  switchBackToAI,
  syncConsultantTakeoverStatus,
  isConsultantMode
} from '@/service/chatService';

interface ConversationTakeoverProps {
  conversationId?: string | null;
  className?: string;
}

export default function ConversationTakeover({ 
  conversationId, 
  className = "flex-shrink-0" 
}: ConversationTakeoverProps) {
  const [isTakeover, setIsTakeover] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // 切换会话时，从数据库获取接管状态
  useEffect(() => {
    const fetchTakeoverStatus = async () => {
      if (!conversationId) {
        setIsTakeover(false);
        return;
      }

      try {
        console.log('ConversationTakeover: 获取会话接管状态', conversationId);
        const status = await isConsultantMode(conversationId);
        console.log('ConversationTakeover: 当前接管状态', status);
        setIsTakeover(status);
      } catch (error) {
        console.error('获取接管状态失败:', error);
        setIsTakeover(false);
      }
    };

    fetchTakeoverStatus();
  }, [conversationId]);

  // 切换接管状态
  const toggleTakeoverMode = useCallback(async () => {
    if (!conversationId || isLoading) return;

    try {
      setIsLoading(true);
      console.log('ConversationTakeover: 切换接管状态', { 
        conversationId, 
        currentStatus: isTakeover 
      });

      let success = false;
      
      if (isTakeover) {
        // 切换回AI助手
        console.log('ConversationTakeover: 切换回AI助手');
        success = await switchBackToAI(conversationId);
      } else {
        // 用户接管
        console.log('ConversationTakeover: 用户接管');
        success = await takeoverConversation(conversationId);
      }

      if (success) {
        // 同步数据库状态
        await syncConsultantTakeoverStatus(conversationId);
        
        // 更新本地状态
        const newStatus = !isTakeover;
        setIsTakeover(newStatus);
        
        console.log('ConversationTakeover: 状态切换成功', { 
          oldStatus: isTakeover, 
          newStatus 
        });
      } else {
        console.error('ConversationTakeover: 状态切换失败');
      }
    } catch (error) {
      console.error('切换接管模式失败:', error);
    } finally {
      setIsLoading(false);
    }
  }, [conversationId, isTakeover, isLoading]);

  return (
    <button 
      className={`${className} ${
        isTakeover 
          ? 'text-green-500' 
          : 'text-gray-500 hover:text-gray-700'
      } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
      onClick={toggleTakeoverMode}
      disabled={isLoading || !conversationId}
      title={
        isLoading 
          ? '正在切换...' 
          : isTakeover 
            ? "切换回AI助手" 
            : "接管会话"
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
          d={isTakeover 
            ? "M13 10V3L4 14h7v7l9-11h-7z" // 闪电图标，表示切换回AI
            : "M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" // 用户图标，表示用户接管
          }
        />
      </svg>
    </button>
  );
}
