import { Bot, Loader2 } from 'lucide-react';
import type { AgentMessage, FeedbackRating } from '@/types/agent-chat';
import { AgentThinking } from './AgentThinking';
import { MessageFeedback } from './MessageFeedback';
import { SuggestedQuestions } from './SuggestedQuestions';
import { StreamMarkdown } from '@/components/base/StreamMarkdown';
import { cn } from '@/service/utils';

interface AIMessageProps {
  message: AgentMessage;
  agentConfigId: string;
  onSelectQuestion?: (question: string) => void;
  onFeedbackChange?: (messageId: string, rating: FeedbackRating) => void;
}

export function AIMessage({ 
  message, 
  agentConfigId,
  onSelectQuestion,
  onFeedbackChange 
}: AIMessageProps) {
  const handleFeedbackChange = (rating: FeedbackRating) => {
    onFeedbackChange?.(message.id, rating);
  };
  return (
    <div className="flex items-start space-x-3">
      <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-orange-100">
        <Bot className="h-5 w-5 text-orange-600" />
      </div>
      <div className="flex-1">
        {/* Agent 思考过程 */}
        {message.agentThoughts && message.agentThoughts.length > 0 && (
          <AgentThinking thoughts={message.agentThoughts} />
        )}
        
        {/* 消息内容卡片 */}
        <div className="relative">
          <div className={cn(
            "rounded-lg bg-white border border-gray-200 px-4 py-3",
            message.isError && "border-red-200 bg-red-50"
          )}>
            {/* 流式加载状态 */}
            {message.isStreaming && !message.content && (
              <div className="flex items-center gap-2">
                <div className="flex gap-1">
                  <span 
                    className="h-2 w-2 animate-bounce rounded-full bg-gray-400" 
                    style={{ animationDelay: '0ms' }}
                  />
                  <span 
                    className="h-2 w-2 animate-bounce rounded-full bg-gray-400" 
                    style={{ animationDelay: '150ms' }}
                  />
                  <span 
                    className="h-2 w-2 animate-bounce rounded-full bg-gray-400" 
                    style={{ animationDelay: '300ms' }}
                  />
                </div>
                <span className="text-sm text-gray-500">AI 正在思考...</span>
              </div>
            )}
            
            {/* 消息内容 - 使用流式 Markdown 渲染 */}
            {message.content && (
              <StreamMarkdown 
                content={message.content}
                className="text-sm text-gray-900"
              />
            )}
            
            {/* 错误提示 */}
            {message.isError && (
              <p className="text-sm text-red-600">⚠️ 响应出错，请重试</p>
            )}
          </div>

          {/* 反馈按钮 - 悬浮在卡片右上角 */}
          {!message.isStreaming && !message.isError && message.content && (
            <div className="absolute -right-2 -top-2">
              <MessageFeedback
                messageId={message.id}
                agentConfigId={agentConfigId}
                initialFeedback={message.feedback?.rating}
                onFeedbackChange={handleFeedbackChange}
              />
            </div>
          )}
        </div>

        {/* 建议问题 */}
        {!message.isStreaming && !message.isError && message.content && onSelectQuestion && (
          <SuggestedQuestions
            messageId={message.id}
            agentConfigId={agentConfigId}
            onSelectQuestion={onSelectQuestion}
          />
        )}
        
        {/* 时间戳 */}
        <p className="mt-1 text-xs text-gray-400">
          {new Date(message.timestamp).toLocaleTimeString()}
        </p>
      </div>
    </div>
  );
}

