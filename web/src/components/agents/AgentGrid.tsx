import { memo } from 'react';
import { Bot } from 'lucide-react';
import { AgentCard } from './AgentCard';
import { AgentConfig } from '@/service/agentConfigService';

interface AgentGridProps {
  configs: AgentConfig[];
  onStartChat: (config: AgentConfig) => void;
}

export const AgentGrid = memo<AgentGridProps>(({ configs, onStartChat }) => {
  if (configs.length === 0) {
    return (
      <div className="text-center py-12">
        <Bot className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">暂无智能体</h3>
        <p className="mt-1 text-sm text-gray-500">暂无配置数据</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      {configs.map((config) => (
        <AgentCard
          key={config.id}
          config={config}
          onStartChat={onStartChat}
        />
      ))}
    </div>
  );
});

AgentGrid.displayName = 'AgentGrid';
