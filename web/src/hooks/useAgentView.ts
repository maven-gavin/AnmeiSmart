import { useState, useCallback } from 'react';
import { AgentConfig } from '@/service/agentConfigService';

export type ViewMode = 'explore' | 'chat';

export function useAgentView() {
  const [viewMode, setViewMode] = useState<ViewMode>('explore');
  const [selectedAgent, setSelectedAgent] = useState<AgentConfig | null>(null);

  const switchToChat = useCallback((agent: AgentConfig) => {
    setSelectedAgent(agent);
    setViewMode('chat');
  }, []);

  const switchToExplore = useCallback(() => {
    setViewMode('explore');
    setSelectedAgent(null);
  }, []);

  return {
    viewMode,
    selectedAgent,
    switchToChat,
    switchToExplore
  };
}
