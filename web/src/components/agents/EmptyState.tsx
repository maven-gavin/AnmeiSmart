import { MessageCircle } from 'lucide-react';
import type { AgentConfig } from '@/service/agentConfigService';

interface EmptyStateProps {
  agentConfig: AgentConfig;
}

export function EmptyState({ agentConfig }: EmptyStateProps) {
  return (
    <div className="flex h-full items-center justify-center">
      <div className="text-center">
        <MessageCircle className="mx-auto h-16 w-16 text-gray-300" />
        <h3 className="mt-4 text-lg font-medium text-gray-900">
          与 {agentConfig.appName} 开始对话
        </h3>
        <p className="mt-2 text-sm text-gray-500">
          输入您的问题，AI 助手将为您提供帮助
        </p>
      </div>
    </div>
  );
}

