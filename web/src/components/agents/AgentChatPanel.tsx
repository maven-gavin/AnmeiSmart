import { memo } from 'react';
import { Button } from '@/components/ui/button';
import { ArrowLeft, Bot, MessageCircle } from 'lucide-react';
import { AgentConfig } from '@/service/agentConfigService';

interface AgentChatPanelProps {
  selectedAgent: AgentConfig;
  onBack: () => void;
}

export const AgentChatPanel = memo<AgentChatPanelProps>(({ 
  selectedAgent, 
  onBack 
}) => {
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

      {/* 聊天面板占位内容 */}
      <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
        {/* 聊天消息区域 */}
        <div className="flex h-[500px] flex-col">
          {/* 消息列表区域 */}
          <div className="flex-1 p-6">
            <div className="flex h-full items-center justify-center">
              <div className="text-center">
                <MessageCircle className="mx-auto h-16 w-16 text-gray-300" />
                <h3 className="mt-4 text-lg font-medium text-gray-900">
                  与 {selectedAgent.appName} 开始对话
                </h3>
                <p className="mt-2 text-sm text-gray-500">
                  这里是聊天面板，功能正在开发中...
                </p>
                <div className="mt-4 rounded-lg bg-gray-50 p-4">
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Agent 信息:</h4>
                  <div className="space-y-1 text-xs text-gray-600">
                    <p><span className="font-medium">ID:</span> {selectedAgent.appId}</p>
                    <p><span className="font-medium">环境:</span> {selectedAgent.environment}</p>
                    <p><span className="font-medium">状态:</span> {selectedAgent.enabled ? '启用' : '禁用'}</p>
                    <p><span className="font-medium">地址:</span> {selectedAgent.baseUrl}</p>
                    {selectedAgent.description && (
                      <p><span className="font-medium">描述:</span> {selectedAgent.description}</p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* 输入区域 */}
          <div className="border-t border-gray-200 p-4">
            <div className="flex space-x-4">
              <input
                type="text"
                placeholder="输入消息..."
                className="flex-1 rounded-lg border border-gray-300 px-4 py-2 focus:border-orange-500 focus:outline-none focus:ring-1 focus:ring-orange-500"
                disabled
              />
              <Button 
                className="bg-orange-500 hover:bg-orange-600"
                disabled
              >
                发送
              </Button>
            </div>
            <p className="mt-2 text-xs text-gray-500">
              聊天功能正在开发中，敬请期待...
            </p>
          </div>
        </div>
      </div>
    </div>
  );
});

AgentChatPanel.displayName = 'AgentChatPanel';
