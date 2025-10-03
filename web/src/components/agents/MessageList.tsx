import { useEffect, useRef } from 'react';
import type { AgentMessage, FeedbackRating } from '@/types/agent-chat';
import { UserMessage } from './UserMessage';
import { AIMessage } from './AIMessage';

interface MessageListProps {
  messages: AgentMessage[];
  isLoading?: boolean;
  agentConfigId: string;
  onSelectQuestion?: (question: string) => void;
  onFeedbackChange?: (messageId: string, rating: FeedbackRating) => void;
}

export function MessageList({ 
  messages, 
  isLoading, 
  agentConfigId,
  onSelectQuestion,
  onFeedbackChange
}: MessageListProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-orange-500 border-r-transparent"></div>
          <p className="mt-2 text-sm text-gray-600">加载中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      {messages.map((message) => (
        message.isAnswer ? (
          <AIMessage 
            key={message.id} 
            message={message} 
            agentConfigId={agentConfigId}
            onSelectQuestion={onSelectQuestion}
            onFeedbackChange={onFeedbackChange}
          />
        ) : (
          <UserMessage key={message.id} message={message} />
        )
      ))}
      <div ref={messagesEndRef} />
    </div>
  );
}

