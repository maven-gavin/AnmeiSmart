'use client';

import { useEffect, useCallback } from 'react';
import { useAuthContext } from '@/contexts/AuthContext';
import AppLayout from '@/components/layout/AppLayout';
import { useAgentConfigs } from '@/hooks/useAgentConfigs';
import { useAgentFilters } from '@/hooks/useAgentFilters';
import { usePagination } from '@/hooks/usePagination';
import { useAgentView } from '@/hooks/useAgentView';
import { AgentExplore } from '@/components/agents/AgentExplore';
import { AgentChatPanel } from '@/components/agents/AgentChatPanel';
import { LoadingSpinner } from '@/components/agents/LoadingSpinner';
import type { AgentConfig } from '@/service/agentConfigService';
import { toast } from 'react-hot-toast';

export function AgentsPage() {
  const { user } = useAuthContext();
  const { configs: agentConfigs, isLoading } = useAgentConfigs();
  
  const { 
    filters, 
    filteredConfigs, 
    updateFilter, 
    resetFilters 
  } = useAgentFilters(agentConfigs);
  
  const {
    currentItems,
    totalPages,
    currentPage,
    hasNextPage,
    hasPreviousPage,
    goToPage,
    nextPage,
    previousPage,
    resetPage
  } = usePagination(filteredConfigs, 8);

  const {
    viewMode,
    selectedAgent,
    switchToChat,
    switchToExplore
  } = useAgentView();

  // 重置分页当筛选条件改变时
  useEffect(() => {
    resetPage();
  }, [filteredConfigs, resetPage]);

  const handleSearch = useCallback(() => {
    // 筛选逻辑已在useAgentFilters中处理
    resetPage();
  }, [resetPage]);

  const handleReset = useCallback(() => {
    resetFilters();
    resetPage();
  }, [resetFilters, resetPage]);

  const handleStartChat = useCallback((config: AgentConfig) => {
    switchToChat(config);
    toast.success(`开始与 ${config.appName} 对话`);
  }, [switchToChat]);

  if (isLoading && agentConfigs.length === 0) {
    return <LoadingSpinner />;
  }

  return (
    <AppLayout requiredRole={user?.currentRole}>
      {viewMode === 'explore' ? (
        <AgentExplore
          filters={filters}
          currentItems={currentItems}
          currentPage={currentPage}
          totalPages={totalPages}
          hasNextPage={hasNextPage}
          hasPreviousPage={hasPreviousPage}
          onFilterChange={updateFilter}
          onReset={handleReset}
          onSearch={handleSearch}
          onStartChat={handleStartChat}
          onPageChange={goToPage}
          onNext={nextPage}
          onPrevious={previousPage}
        />
      ) : (
        <AgentChatPanel
          agents={agentConfigs}
          isLoadingAgents={isLoading}
          selectedAgent={selectedAgent}
          onSelectAgent={handleStartChat}
        />
      )}
    </AppLayout>
  );
}

export default AgentsPage;
