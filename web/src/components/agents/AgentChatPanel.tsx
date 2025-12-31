'use client';

import { memo, useState, useEffect } from 'react';
import { Badge } from '@/components/ui/badge';
import { Receipt, BrainCircuit, ChevronLeft } from 'lucide-react';
import type { AgentConfig } from '@/service/agentConfigService';
import { useAgentChat } from '@/hooks/useAgentChat';
import { useMediaQuery } from '@/hooks/useMediaQuery';
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
  // 移动端检测
  const isMobile = useMediaQuery(768);

  // 移动端视图状态管理
  type MobileViewType = 'agent' | 'history' | 'chat';
  const [mobileView, setMobileView] = useState<MobileViewType>(() => {
    // 默认显示 history 视图
    return 'history';
  });

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
    // 移动端：选择对话后切换到 chat 视图
    if (isMobile) {
      setMobileView('chat');
    }
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

  // 移动端：选择智能体后切换到 history 视图
  useEffect(() => {
    if (isMobile && selectedAgent) {
      setMobileView('history');
    } else if (isMobile && !selectedAgent && !hideSidebar) {
      // 如果没有选择智能体且不隐藏侧边栏，显示 agent 视图
      setMobileView('agent');
    }
  }, [isMobile, selectedAgent, hideSidebar]);

  // 移动端：处理切换到 chat 视图
  const handleSwitchToChat = () => {
    if (isMobile) {
      setMobileView('chat');
    }
  };

  // 移动端：处理切换到 history 视图
  const handleSwitchToHistory = () => {
    if (isMobile) {
      setMobileView('history');
    }
  };

  // 移动端：处理切换到 agent 视图
  const handleSwitchToAgent = () => {
    if (isMobile && !hideSidebar) {
      setMobileView('agent');
    }
  };

  return (
    <div className={`flex h-screen overflow-hidden bg-gray-50 ${className}`}>
      {/* 移动端：根据视图状态显示不同内容 */}
      {isMobile ? (
        <>
          {/* Agent 视图：仅显示 AgentSidebar */}
          {!hideSidebar && mobileView === 'agent' && (
            <div className="w-full h-full flex-shrink-0">
              <AgentSidebar
                agents={agents}
                selectedAgent={selectedAgent}
                onSelectAgent={(agent) => {
                  handleSelectAgent(agent);
                  setMobileView('history');
                }}
                isLoading={isLoadingAgents}
              />
            </div>
          )}

          {/* History 视图：仅显示 ConversationHistoryPanel */}
          {mobileView === 'history' && (
            <>
              {selectedAgent ? (
                <div className="w-full h-full flex-shrink-0">
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
                    onSwitchToChat={handleSwitchToChat}
                  />
                </div>
              ) : (
                <div className="w-full h-full flex-shrink-0 flex items-center justify-center">
                  <div className="text-center">
                    <div className="mb-4 inline-flex h-16 w-16 items-center justify-center rounded-full bg-gray-100">
                      <Receipt className="h-8 w-8 text-gray-400" />
                    </div>
                    <h3 className="mb-2 text-lg font-semibold text-gray-900">
                      选择一个智能体开始
                    </h3>
                    <p className="text-sm text-gray-500">
                      {!hideSidebar ? '从左侧列表中选择一个智能体，开始您的对话' : '请先选择一个智能体'}
                    </p>
                  </div>
                </div>
              )}
            </>
          )}

          {/* Chat 视图：仅显示聊天区域 */}
          {mobileView === 'chat' && selectedAgent && (
            <div className="w-full h-full flex-shrink-0 flex flex-col overflow-hidden">
              {/* 顶部标题栏 */}
              <div className="flex h-16 items-center justify-between border-b border-gray-100 bg-white px-6">
                <div className="flex items-center space-x-4">
                  {/* 移动端：返回按钮 */}
                  <button
                    onClick={handleSwitchToHistory}
                    className="flex-shrink-0 p-1.5 rounded-md hover:bg-yellow-50 transition-colors"
                    title="返回对话列表"
                  >
                    <ChevronLeft className="h-5 w-5 text-yellow-400" />
                  </button>
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
                    {digitalHuman && digitalHuman.agent_configs && (
                      <div className="mt-2 flex items-center gap-2 flex-wrap">
                        {digitalHuman.agent_configs
                          .filter(c => c.is_active)
                          .sort((a, b) => a.priority - b.priority)
                          .map((config) => {
                            const isActive = selectedAgent?.id === config.agent_config.id;
                            const agentConfig: AgentConfig = {
                              id: config.agent_config.id,
                              appName: config.agent_config.app_name,
                              appId: config.agent_config.app_id,
                              environment: config.agent_config.environment,
                              description: config.agent_config.description,
                              enabled: config.agent_config.enabled,
                              baseUrl: '',
                              timeoutSeconds: 30,
                              maxRetries: 3,
                              createdAt: '',
                              updatedAt: ''
                            };
                            return (
                              <button
                                key={config.id}
                                onClick={() => handleSelectAgent(agentConfig)}
                                className={`
                                  px-3 py-1.5 rounded-full text-xs font-medium transition-all duration-200
                                  ${isActive 
                                    ? 'bg-orange-500 text-white shadow-sm hover:bg-orange-600' 
                                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200 hover:text-gray-900'
                                  }
                                `}
                                title={config.agent_config.description || config.agent_config.app_name}
                              >
                                {config.agent_config.app_name}
                              </button>
                            );
                          })}
                      </div>
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
            </div>
          )}

          {/* 移动端：未选择智能体时的空状态 */}
          {mobileView === 'chat' && !selectedAgent && (
            <div className="w-full h-full flex-shrink-0 flex items-center justify-center">
              <div className="text-center">
                <div className="mb-4 inline-flex h-16 w-16 items-center justify-center rounded-full bg-gray-100">
                  <Receipt className="h-8 w-8 text-gray-400" />
                </div>
                <h3 className="mb-2 text-lg font-semibold text-gray-900">
                  选择一个智能体开始
                </h3>
                <p className="text-sm text-gray-500">
                  {!hideSidebar ? '从左侧列表中选择一个智能体，开始您的对话' : '请先选择一个智能体'}
                </p>
              </div>
            </div>
          )}
        </>
      ) : (
        <>
          {/* 桌面端：保持原有布局 */}
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
                      {digitalHuman && digitalHuman.agent_configs && (
                        <div className="mt-2 flex items-center gap-2 flex-wrap">
                          {digitalHuman.agent_configs
                            .filter(c => c.is_active)
                            .sort((a, b) => a.priority - b.priority)
                            .map((config) => {
                              const isActive = selectedAgent?.id === config.agent_config.id;
                              const agentConfig: AgentConfig = {
                                id: config.agent_config.id,
                                appName: config.agent_config.app_name,
                                appId: config.agent_config.app_id,
                                environment: config.agent_config.environment,
                                description: config.agent_config.description,
                                enabled: config.agent_config.enabled,
                                baseUrl: '',
                                timeoutSeconds: 30,
                                maxRetries: 3,
                                createdAt: '',
                                updatedAt: ''
                              };
                              return (
                                <button
                                  key={config.id}
                                  onClick={() => handleSelectAgent(agentConfig)}
                                  className={`
                                    px-3 py-1.5 rounded-full text-xs font-medium transition-all duration-200
                                    ${isActive 
                                      ? 'bg-orange-500 text-white shadow-sm hover:bg-orange-600' 
                                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200 hover:text-gray-900'
                                    }
                                  `}
                                  title={config.agent_config.description || config.agent_config.app_name}
                                >
                                  {config.agent_config.app_name}
                                </button>
                              );
                            })}
                        </div>
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
        </>
      )}
    </div>
  );
});

AgentChatPanel.displayName = 'AgentChatPanel';
