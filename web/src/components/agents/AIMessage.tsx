import { Bot } from 'lucide-react';
import type { AgentMessage, FeedbackRating, ApplicationParameters } from '@/types/agent-chat';
import { AgentThinking } from './AgentThinking';
import { MessageFeedback } from './MessageFeedback';
import { SuggestedQuestions } from './SuggestedQuestions';
import { StreamMarkdown } from '@/components/base/StreamMarkdown';
import { TextToSpeechButton } from './TextToSpeechButton';
import { TypingIndicator } from './TypingIndicator';
import { cn } from '@/service/utils';
import { useMemo } from 'react';

interface AIMessageProps {
  message: AgentMessage;
  agentConfigId: string;
  isLastMessage?: boolean;
  onSelectQuestion?: (question: string) => void;
  onFeedbackChange?: (messageId: string, rating: FeedbackRating) => void;
  config?: ApplicationParameters | null;  // 应用配置
}

export function AIMessage({ 
  message, 
  agentConfigId,
  isLastMessage = false,
  onSelectQuestion,
  onFeedbackChange,
  config
}: AIMessageProps) {
  const handleFeedbackChange = (rating: FeedbackRating) => {
    onFeedbackChange?.(message.id, rating);
  };

  // 判断是否启用 TTS
  const enableTTS = config?.text_to_speech?.enabled ?? false;
  
  // 处理历史消息：如果 thinkSections 未定义但 content 包含标签，解析并分离内容
  const { normalContent, thinkSections } = useMemo(() => {
    // 如果已经有 thinkSections，直接使用
    if (message.thinkSections !== undefined) {
      return {
        normalContent: message.content,
        thinkSections: message.thinkSections
      };
    }
    
    // 如果 content 包含标签，解析它
    if (message.content && message.content.includes('<think>')) {
      // 使用 StreamMarkdown 的 processSpecialTags 逻辑解析
      const thinkSections: string[] = [];
      let processedContent = '';
      let thinkContent = '';
      let isInThinkTag = false;
      let i = 0;
      
      const OPEN_TAG = '<think>';
      const CLOSE_TAG = '</think>';
      
      while (i < message.content.length) {
        // 检查是否遇到开始标签
        if (!isInThinkTag && message.content.substring(i, i + OPEN_TAG.length) === OPEN_TAG) {
          isInThinkTag = true;
          thinkContent = '';
          i += OPEN_TAG.length;
          continue;
        }
        
        // 检查是否遇到结束标签
        if (isInThinkTag && message.content.substring(i, i + CLOSE_TAG.length) === CLOSE_TAG) {
          // 保存思考内容
          if (thinkContent.trim()) {
            thinkSections.push(thinkContent.trim());
          }
          isInThinkTag = false;
          thinkContent = '';
          i += CLOSE_TAG.length;
          continue;
        }
        
        // 根据当前状态追加内容
        if (isInThinkTag) {
          thinkContent += message.content[i];
        } else {
          processedContent += message.content[i];
        }
        
        i++;
      }
      
      // 如果最后还在标签内（未闭合），确保不将未闭合的标签添加到 processedContent
      // 这种情况下，thinkContent 会被丢弃，processedContent 不包含标签
      
      return {
        normalContent: processedContent.trim(),
        thinkSections: thinkSections.length > 0 ? thinkSections : undefined
      };
    }
    
    // 否则直接返回原始内容（确保不包含任何标签）
    // 如果原始内容包含标签但格式不正确，至少不会导致 React 报错
    const safeContent = message.content?.replace(/<think>[\s\S]*?<\/redacted_reasoning>/g, '') || '';
    return {
      normalContent: safeContent.trim(),
      thinkSections: undefined
    };
  }, [message.content, message.thinkSections]);
  return (
    <div className="flex items-start space-x-3">
      <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-orange-100">
        <Bot className="h-5 w-5 text-orange-600" />
      </div>
      <div className="flex-1 max-w-[70%]">
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
            {(normalContent || (thinkSections && thinkSections.length > 0)) && (
              <StreamMarkdown 
                normalContent={normalContent}
                thinkSections={thinkSections}
                className="text-sm text-gray-900"
              />
            )}
            
            {/* 错误提示 */}
            {message.isError && (
              <p className="text-sm text-red-600">⚠️ 响应出错，请重试</p>
            )}
          </div>

          {/* 操作按钮 - 悬浮在卡片右上角 */}
          {!message.isStreaming && !message.isError && message.content && (
            <div className="absolute -right-2 -top-2 flex items-center space-x-1">
              {/* TTS 按钮 */}
              {enableTTS && (
                <TextToSpeechButton
                  text={message.content}
                  agentConfigId={agentConfigId}
                  messageId={message.id}
                />
              )}
              
              {/* 反馈按钮 */}
              <MessageFeedback
                messageId={message.id}
                agentConfigId={agentConfigId}
                initialFeedback={message.feedback?.rating}
                onFeedbackChange={handleFeedbackChange}
              />
            </div>
          )}
        </div>

        {/* 建议问题 - 只在最后一个消息时显示 */}
        {isLastMessage && !message.isStreaming && !message.isError && message.content && onSelectQuestion && (
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

