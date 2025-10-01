import { memo } from 'react';
import { Bot, Globe, Plus, Settings } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { AgentConfig } from '@/service/agentConfigService';

interface AgentCardProps {
  config: AgentConfig;
  onStartChat: (config: AgentConfig) => void;
}

// 状态样式映射
const getStatusStyle = (enabled: boolean): string => {
  return enabled 
    ? 'bg-green-100 text-green-800' 
    : 'bg-gray-100 text-gray-800';
};

// 环境样式映射
const getEnvironmentStyle = (env: string): string => {
  const styles: Record<string, string> = {
    dev: 'bg-blue-100 text-blue-800',
    test: 'bg-yellow-100 text-yellow-800',
    prod: 'bg-red-100 text-red-800'
  };
  return styles[env] || 'bg-gray-100 text-gray-800';
};

// 获取智能体类型
const getAgentType = (environment: string): string => {
  const types: Record<string, string> = {
    dev: '开发环境',
    test: '测试环境', 
    prod: '生产环境'
  };
  return types[environment] || '未知类型';
};

export const AgentCard = memo<AgentCardProps>(({ config, onStartChat }) => {
  return (
    <div className="group relative overflow-hidden rounded-lg border border-gray-200 bg-white p-6 shadow-sm transition-all duration-200 hover:shadow-md hover:border-orange-300">
      {/* 智能体图标和基本信息 */}
      <div className="flex items-start space-x-4">
        <div className="flex-shrink-0">
          <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-orange-100">
            <Bot className="h-6 w-6 text-orange-600" />
          </div>
        </div>
        <div className="min-w-0 flex-1">
          <h3 className="text-lg font-semibold text-gray-900 truncate">
            {config.appName}
          </h3>
          <p className="text-sm text-gray-600">
            {getAgentType(config.environment)}
          </p>
        </div>
      </div>

      {/* 描述信息 */}
      <div className="mt-4">
        <p 
          className="text-sm text-gray-500 overflow-hidden" 
          style={{
            display: '-webkit-box',
            WebkitLineClamp: 2,
            WebkitBoxOrient: 'vertical'
          }}
        >
          {config.description || '暂无描述信息'}
        </p>
      </div>

      {/* 状态和环境标签 */}
      <div className="mt-4 flex items-center justify-between">
        <span className={`rounded-full ${getEnvironmentStyle(config.environment)} px-3 py-1 text-xs font-medium`}>
          {config.environment}
        </span>
        <span className={`rounded-full ${getStatusStyle(config.enabled)} px-3 py-1 text-xs font-medium`}>
          {config.enabled ? '启用' : '禁用'}
        </span>
      </div>

      {/* 基础信息 */}
      <div className="mt-4 space-y-2">
        <div className="flex items-center text-xs text-gray-500">
          <Settings className="mr-2 h-3 w-3" />
          <span className="truncate">ID: {config.appId}</span>
        </div>
        <div className="flex items-center text-xs text-gray-500">
          <Globe className="mr-2 h-3 w-3" />
          <span className="truncate">{config.baseUrl}</span>
        </div>
      </div>

      {/* 悬浮按钮 */}
      <div className="absolute inset-x-0 bottom-0 transform translate-y-full transition-transform duration-200 group-hover:translate-y-0">
        <div className="bg-gradient-to-t from-white via-white to-transparent p-4 pt-8">
          <Button
            onClick={() => onStartChat(config)}
            className="w-full bg-orange-500 hover:bg-orange-600 text-white"
            size="sm"
          >
            <Plus className="mr-2 h-4 w-4" />
            Start Chat
          </Button>
        </div>
      </div>
    </div>
  );
});

AgentCard.displayName = 'AgentCard';
