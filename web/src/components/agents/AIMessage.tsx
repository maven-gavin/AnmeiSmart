import { Bot, Loader2 } from 'lucide-react';
import type { AgentMessage } from '@/types/agent-chat';
import { AgentThinking } from './AgentThinking';
import { cn } from '@/service/utils';

interface AIMessageProps {
  message: AgentMessage;
}

export function AIMessage({ message }: AIMessageProps) {
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
        
        {/* 消息内容 */}
        <div className={cn(
          "rounded-lg bg-white border border-gray-200 px-4 py-3",
          message.isError && "border-red-200 bg-red-50"
        )}>
          {message.isStreaming && !message.content && (
            <div className="flex items-center space-x-2 text-gray-500">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span className="text-sm">AI 正在思考...</span>
            </div>
          )}
          
          {message.content && (
            <div className="prose prose-sm max-w-none">
              <p className="text-sm text-gray-900 whitespace-pre-wrap">
                {message.content}
              </p>
            </div>
          )}
          
          {message.isError && (
            <p className="text-sm text-red-600">⚠️ 响应出错，请重试</p>
          )}
        </div>
        
        <p className="mt-1 text-xs text-gray-400">
          {new Date(message.timestamp).toLocaleTimeString()}
        </p>
      </div>
    </div>
  );
}

