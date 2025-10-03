'use client';

import { useState, useEffect } from 'react';
import { Lightbulb, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { toast } from 'react-hot-toast';

interface SuggestedQuestionsProps {
  messageId: string;
  agentConfigId: string;
  onSelectQuestion: (question: string) => void;
}

/**
 * 建议问题组件
 * 显示 AI 建议的后续问题，用户可以快速选择
 */
export function SuggestedQuestions({
  messageId,
  agentConfigId,
  onSelectQuestion
}: SuggestedQuestionsProps) {
  const [questions, setQuestions] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);

  useEffect(() => {
    const loadQuestions = async () => {
      if (!messageId || !agentConfigId) return;
      
      setLoading(true);
      setError(false);
      
      try {
        // 动态导入服务
        const { getSuggestedQuestions } = await import('@/service/agentChatService');
        const data = await getSuggestedQuestions(agentConfigId, messageId);
        setQuestions(data || []);
      } catch (err) {
        console.error('加载建议问题失败:', err);
        setError(true);
        // 静默失败，不影响主要功能
      } finally {
        setLoading(false);
      }
    };

    loadQuestions();
  }, [messageId, agentConfigId]);

  // 加载中状态
  if (loading) {
    return (
      <div className="mt-3 flex items-center gap-2 text-sm text-gray-500">
        <Loader2 size={14} className="animate-spin" />
        <span>加载建议问题...</span>
      </div>
    );
  }

  // 错误或无建议问题
  if (error || !questions || questions.length === 0) {
    return null;
  }

  return (
    <div className="mt-4 space-y-2">
      {/* 标题 */}
      <div className="flex items-center gap-1.5 text-sm font-medium text-gray-700">
        <Lightbulb size={14} className="text-orange-500" />
        <span>您可能还想问：</span>
      </div>

      {/* 问题列表 */}
      <div className="flex flex-wrap gap-2">
        {questions.map((question, index) => (
          <Button
            key={index}
            variant="outline"
            size="sm"
            onClick={() => onSelectQuestion(question)}
            className="h-auto whitespace-normal text-left px-3 py-2 
                     bg-orange-50 hover:bg-orange-100 
                     border-orange-200 hover:border-orange-300
                     text-orange-700 hover:text-orange-800
                     transition-colors"
          >
            {question}
          </Button>
        ))}
      </div>
    </div>
  );
}

