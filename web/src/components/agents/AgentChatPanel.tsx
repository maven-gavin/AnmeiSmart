import { memo } from 'react';
import { Button } from '@/components/ui/button';
import { ArrowLeft, Bot } from 'lucide-react';
import type { AgentConfig } from '@/service/agentConfigService';
import { useAgentChat } from '@/hooks/useAgentChat';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';
import { EmptyState } from './EmptyState';

interface AgentChatPanelProps {
  selectedAgent: AgentConfig;
  onBack: () => void;
}

export const AgentChatPanel = memo<AgentChatPanelProps>(({ 
  selectedAgent, 
  onBack 
}) => {
  const {
    messages,
    isResponding,
    isLoading,
    sendMessage,
    stopResponding,
  } = useAgentChat({ 
    agentConfig: selectedAgent,
    onError: (error) => console.error('Chat error:', error)
  });

  return (
    <div className="container mx-auto px-4 py-6">
      {/* 头部导航 */}
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button
            variant="outline"
            size="sm"
            onClick={onBack}
            className="flex items-center space-x-2"
          >
            <ArrowLeft className="h-4 w-4" />
            <span>返回探索</span>
          </Button>
          <div className="flex items-center space-x-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-orange-100">
              <Bot className="h-5 w-5 text-orange-600" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-800">{selectedAgent.appName}</h1>
              <p className="text-sm text-gray-600">{selectedAgent.environment}</p>
            </div>
          </div>
        </div>
      </div>

      {/* 聊天面板 */}
      <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
        <div className="flex h-[calc(100vh-220px)] flex-col">
          {/* 消息列表区域 */}
          <div className="flex-1 overflow-y-auto">
            {messages.length === 0 && !isLoading ? (
              <EmptyState agentConfig={selectedAgent} />
            ) : (
              <MessageList messages={messages} isLoading={isLoading} />
            )}
          </div>

          {/* 输入区域 */}
          <MessageInput
            onSend={sendMessage}
            disabled={isResponding}
            isResponding={isResponding}
            onStop={stopResponding}
            placeholder={`向 ${selectedAgent.appName} 提问...`}
          />
        </div>
      </div>
    </div>
  );
});

AgentChatPanel.displayName = 'AgentChatPanel';
