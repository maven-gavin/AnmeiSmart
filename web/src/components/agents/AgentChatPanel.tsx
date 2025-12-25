'use client';

import { memo, useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Receipt, BrainCircuit } from 'lucide-react';
import type { AgentConfig } from '@/service/agentConfigService';
import { useAgentChat } from '@/hooks/useAgentChat';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';
import { EmptyState } from './EmptyState';
import { AgentSidebar } from './AgentSidebar';
import { ConversationHistoryPanel } from './ConversationHistoryPanel';
import { ApplicationParameters } from '@/types/agent-chat';
import { DigitalHuman } from '@/types/digital-human';
import { AvatarCircle } from '@/components/ui/AvatarCircle';

interface AgentChatPanelProps {
  agents: AgentConfig[];
  isLoadingAgents?: boolean;
  selectedAgent?: AgentConfig | null;
  digitalHuman?: DigitalHuman | null;
  onSelectAgent?: (agent: AgentConfig) => void;
  hideSidebar?: boolean;
  className?: string;
}

export const AgentChatPanel = memo<AgentChatPanelProps>(({ 
  agents,
  isLoadingAgents = false,
  selectedAgent: externalSelectedAgent = null,
  digitalHuman = null,
  onSelectAgent: externalOnSelectAgent,
  hideSidebar = false,
  className = '',
}) => {
  // 内部状态管理（当没有外部传入时使用）
  const [internalSelectedAgent, setInternalSelectedAgent] = useState<AgentConfig | null>(null);
  
  // 使用外部传入的selectedAgent，如果没有则使用内部状态
  const selectedAgent = externalSelectedAgent !== undefined ? externalSelectedAgent : internalSelectedAgent;

  // 聊天 Hook - 始终调用，但传入 null 作为默认配置
  const chatState = useAgentChat({ 
    agentConfig: selectedAgent || {
      id: '',
      appName: '',
      environment: '',
      appId: '',
      baseUrl: '',
      timeoutSeconds: 30,
      maxRetries: 3,
      enabled: true,
      description: ''
    } as AgentConfig,
    onError: (error) => console.error('Chat error:', error)
  });

  // 从 chatState 中获取 appConfig
  const { appConfig } = chatState;

  // 选择智能体
  const handleSelectAgent = (agent: AgentConfig) => {
    if (externalOnSelectAgent) {
      // 如果有外部回调，使用外部回调
      externalOnSelectAgent(agent);
    } else {
      // 否则使用内部状态
      setInternalSelectedAgent(agent);
    }
  };

  // 创建新对话
  const handleCreateNewChat = () => {
    chatState.createNewConversation();
  };

  // 选择对话
  const handleSelectConversation = (conversationId: string) => {
    chatState.switchConversation(conversationId);
  };

  // 更新对话标题
  const handleConversationUpdate = (conversationId: string, title: string) => {
    // 刷新对话列表以反映标题更新
    chatState.loadConversations();
  };

  // 删除对话
  const handleDeleteConversation = async (conversationId: string) => {
    await chatState.deleteConversation(conversationId);
  };

  // 转换对话数据格式
  const conversationsForPanel = selectedAgent && chatState ? chatState.conversations.map(conv => {
    // 安全地创建日期对象
    let lastMessageAt: Date;
    try {
      lastMessageAt = conv.updatedAt ? new Date(conv.updatedAt) : new Date();
      // 检查日期是否有效
      if (isNaN(lastMessageAt.getTime())) {
        lastMessageAt = new Date();
      }
    } catch {
      lastMessageAt = new Date();
    }

    return {
      id: conv.id,
      title: conv.title || '未命名对话',
      agentId: selectedAgent.id,
      lastMessageAt,
      messageCount: conv.messageCount || 0,
    };
  }) : [];

  return (
    <div className={`flex h-screen overflow-hidden bg-gray-50 ${className}`}>
      {/* 左侧：智能体列表 */}
      {!hideSidebar && (
        <AgentSidebar
          agents={agents}
          selectedAgent={selectedAgent}
          onSelectAgent={handleSelectAgent}
          isLoading={isLoadingAgents}
        />
      )}

      {/* 中间：对话历史列表 */}
      {selectedAgent && (
          <ConversationHistoryPanel
          agentName={digitalHuman ? digitalHuman.name : selectedAgent.appName}
          agentConfigId={selectedAgent.id}
          conversations={conversationsForPanel}
          selectedConversationId={chatState.currentConversationId}
          onSelectConversation={handleSelectConversation}
          onCreateNewChat={handleCreateNewChat}
          onConversationUpdate={handleConversationUpdate}
          onDeleteConversation={handleDeleteConversation}
          isLoading={chatState.isConversationsLoading}
        />
      )}

      {/* 右侧：聊天区域 */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {selectedAgent ? (
          <>
            {/* 顶部标题栏 */}
            <div className="flex h-16 items-center justify-between border-b border-gray-100 bg-white px-6">
              <div className="flex items-center space-x-4">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-orange-50 to-orange-100 border border-orange-100 overflow-hidden shadow-sm">
                  {digitalHuman ? (
                    <AvatarCircle 
                      name={digitalHuman.name}
                      avatar={digitalHuman.avatar}
                      sizeClassName="w-full h-full"
                    />
                  ) : (
                    <Receipt className="h-5 w-5 text-orange-500" />
                  )}
                </div>
                <div className="flex flex-col">
                  <div className="flex items-center space-x-2">
                    <h1 className="text-lg font-bold text-gray-900 leading-none">
                      {digitalHuman ? digitalHuman.name : selectedAgent.appName}
                    </h1>
                    {digitalHuman && (
                      <Badge 
                        variant="outline" 
                        className="text-[10px] py-0 h-4 bg-orange-50 text-orange-600 border-orange-100"
                      >
                        数字人
                      </Badge>
                    )}
                  </div>
                  {digitalHuman && (
                    <span className="text-xs text-gray-400 mt-1 flex items-center">
                      <BrainCircuit className="h-3 w-3 mr-1" />
                      当前能力: {selectedAgent.appName}
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* 消息区域 */}
            <div className="flex flex-1 flex-col overflow-hidden bg-white">
              <div className="flex-1 overflow-y-auto">
                {chatState.messages.length === 0 && !chatState.isLoading ? (
                  <EmptyState 
                    agentConfig={selectedAgent} 
                    appConfig={appConfig || {} as ApplicationParameters}
                    onSendMessage={chatState.sendMessage}
                  />
                ) : (
                  <MessageList 
                    messages={chatState.messages} 
                    isLoading={chatState.isLoading}
                    agentConfigId={selectedAgent.id}
                    onSelectQuestion={chatState.sendMessage}
                    onFeedbackChange={(messageId, rating) => {
                      // 更新本地消息的反馈状态
                      console.log(`Message ${messageId} feedback: ${rating}`);
                    }}
                    config={appConfig}
                  />
                )}
              </div>

              {/* 输入区域 */}
              <div className="border-t border-gray-200">
                <MessageInput
                  onSend={chatState.sendMessage}
                  disabled={chatState.isResponding}
                  isResponding={chatState.isResponding}
                  onStop={chatState.stopResponding}
                  placeholder={`向 ${digitalHuman ? digitalHuman.name : selectedAgent.appName} 提问...`}
                  config={appConfig}
                />
              </div>
            </div>
          </>
        ) : (
          /* 未选择智能体时的空状态 */
          <div className="flex h-full items-center justify-center">
            <div className="text-center">
              <div className="mb-4 inline-flex h-16 w-16 items-center justify-center rounded-full bg-gray-100">
                <Receipt className="h-8 w-8 text-gray-400" />
              </div>
              <h3 className="mb-2 text-lg font-semibold text-gray-900">
                选择一个智能体开始
              </h3>
              <p className="text-sm text-gray-500">
                从左侧列表中选择一个智能体，开始您的对话
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
});

AgentChatPanel.displayName = 'AgentChatPanel';
