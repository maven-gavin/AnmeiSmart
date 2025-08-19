'use client';

import React from 'react';
import AgentConfigPanel from '@/components/settings/AgentConfigPanel';
import { useAgentConfigs } from '@/hooks/useAgentConfigs';

export default function AgentsPage() {
  const {
    configs: agentConfigs,
    isLoading: isAgentLoading,
    createConfig: createAgentConfig,
    updateConfig: updateAgentConfig,
    deleteConfig: deleteAgentConfig,
    testConnection: testAgentConnection
  } = useAgentConfigs();

  return (
    <div className="container mx-auto p-6">
      {isAgentLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="text-lg">加载中...</div>
        </div>
      ) : (
        <AgentConfigPanel
          configs={agentConfigs}
          onCreateConfig={createAgentConfig}
          onUpdateConfig={updateAgentConfig}
          onDeleteConfig={deleteAgentConfig}
          onTestConnection={testAgentConnection}
        />
      )}
    </div>
  );
}
