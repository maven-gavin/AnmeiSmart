'use client';

import { useState } from 'react';
import { ThumbsUp, ThumbsDown } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { FeedbackRating } from '@/types/agent-chat';
import { toast } from 'react-hot-toast';

interface MessageFeedbackProps {
  messageId: string;
  agentConfigId: string;
  initialFeedback?: FeedbackRating;
  onFeedbackChange?: (rating: FeedbackRating) => void;
}

/**
 * 消息反馈组件
 * 用户可以对 AI 回复进行点赞或点踩
 */
export function MessageFeedback({
  messageId,
  agentConfigId,
  initialFeedback = null,
  onFeedbackChange
}: MessageFeedbackProps) {
  const [feedback, setFeedback] = useState<FeedbackRating>(initialFeedback);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleFeedback = async (rating: 'like' | 'dislike') => {
    // 如果点击相同的按钮，取消反馈
    const newRating = feedback === rating ? null : rating;
    
    setIsSubmitting(true);
    try {
      // 动态导入服务，避免循环依赖
      const { submitMessageFeedback } = await import('@/service/agentChatService');
      
      if (newRating) {
        await submitMessageFeedback(agentConfigId, messageId, newRating);
        toast.success('反馈已提交');
      }
      
      setFeedback(newRating);
      onFeedbackChange?.(newRating);
    } catch (error) {
      console.error('提交反馈失败:', error);
      toast.error('提交反馈失败');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex items-center gap-1">
      {/* 点赞按钮 */}
      <button
        onClick={() => handleFeedback('like')}
        disabled={isSubmitting}
        className={cn(
          "group relative flex h-7 w-7 items-center justify-center rounded-lg transition-all",
          "hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-50",
          feedback === 'like'
            ? "bg-green-100 text-green-600 hover:bg-green-200"
            : "text-gray-500 hover:text-gray-700"
        )}
        title="赞同"
      >
        <ThumbsUp 
          size={16} 
          className={cn(
            "transition-transform",
            feedback === 'like' && "fill-current"
          )}
        />
      </button>

      {/* 点踩按钮 */}
      <button
        onClick={() => handleFeedback('dislike')}
        disabled={isSubmitting}
        className={cn(
          "group relative flex h-7 w-7 items-center justify-center rounded-lg transition-all",
          "hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-50",
          feedback === 'dislike'
            ? "bg-red-100 text-red-600 hover:bg-red-200"
            : "text-gray-500 hover:text-gray-700"
        )}
        title="反对"
      >
        <ThumbsDown 
          size={16} 
          className={cn(
            "transition-transform",
            feedback === 'dislike' && "fill-current"
          )}
        />
      </button>
    </div>
  );
}

