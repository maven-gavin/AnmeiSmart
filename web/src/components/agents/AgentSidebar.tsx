import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';
import { Bot, Package } from 'lucide-react';
import type { AgentConfig } from '@/service/agentConfigService';
import { cn } from '@/lib/utils';

interface AgentSidebarProps {
  agents: AgentConfig[];
  selectedAgent: AgentConfig | null;
  onSelectAgent: (agent: AgentConfig) => void;
  isLoading?: boolean;
}

export function AgentSidebar({
  agents,
  selectedAgent,
  onSelectAgent,
  isLoading = false,
}: AgentSidebarProps) {
  if (isLoading) {
    return (
      <div className="flex h-full w-64 flex-col border-r border-gray-200 bg-gray-50">
        <div className="flex h-14 items-center border-b border-gray-200 px-4">
          <Package className="mr-2 h-5 w-5 text-gray-600" />
          <span className="font-semibold text-gray-900">WORKSPACE</span>
        </div>
        <div className="flex flex-1 items-center justify-center">
          <div className="text-center">
            <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-orange-500 border-r-transparent" />
            <p className="mt-2 text-sm text-gray-500">加载中...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full w-64 flex-col border-r border-gray-200 bg-gray-50">
      {/* Header */}
      <div className="flex h-14 items-center border-b border-gray-200 px-4">
        <Package className="mr-2 h-5 w-5 text-gray-600" />
        <span className="font-semibold text-gray-900">WORKSPACE</span>
      </div>

      {/* Agent List */}
      <ScrollArea className="flex-1">
        <div className="space-y-1 p-2">
          {agents.map((agent) => {
            const isSelected = selectedAgent?.id === agent.id;
            
            return (
              <Button
                key={agent.id}
                variant="ghost"
                className={cn(
                  'w-full justify-start space-x-3 px-3 py-2 h-auto',
                  isSelected
                    ? 'bg-white text-gray-900 shadow-sm hover:bg-white'
                    : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
                )}
                onClick={() => onSelectAgent(agent)}
              >
                <div
                  className={cn(
                    'flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg',
                    isSelected ? 'bg-orange-100' : 'bg-gray-200'
                  )}
                >
                  <Bot
                    className={cn(
                      'h-4 w-4',
                      isSelected ? 'text-orange-600' : 'text-gray-600'
                    )}
                  />
                </div>
                <div className="flex-1 overflow-hidden text-left">
                  <div className="truncate text-sm font-medium">
                    {agent.appName}
                  </div>
                </div>
              </Button>
            );
          })}
        </div>

        {agents.length === 0 && (
          <div className="flex flex-col items-center justify-center p-8 text-center">
            <Bot className="mb-3 h-12 w-12 text-gray-300" />
            <p className="text-sm text-gray-500">暂无可用智能体</p>
          </div>
        )}
      </ScrollArea>
    </div>
  );
}

