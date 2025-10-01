import { useState, useCallback, useMemo } from 'react';
import { AgentConfig } from '@/service/agentConfigService';

export interface FilterState {
  environment: string;
  appName: string;
  status: string;
}

export function useAgentFilters(allConfigs: AgentConfig[]) {
  const [filters, setFilters] = useState<FilterState>({
    environment: 'all',
    appName: '',
    status: 'all'
  });

  const filteredConfigs = useMemo(() => {
    let result = [...allConfigs];
    
    if (filters.environment && filters.environment !== 'all') {
      result = result.filter(config => 
        config.environment.toLowerCase().includes(filters.environment.toLowerCase())
      );
    }
    
    if (filters.appName) {
      result = result.filter(config => 
        config.appName.toLowerCase().includes(filters.appName.toLowerCase())
      );
    }
    
    if (filters.status && filters.status !== 'all') {
      const isEnabled = filters.status === 'enabled';
      result = result.filter(config => config.enabled === isEnabled);
    }
    
    return result;
  }, [allConfigs, filters]);

  const updateFilter = useCallback((key: keyof FilterState, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  }, []);

  const resetFilters = useCallback(() => {
    setFilters({
      environment: 'all',
      appName: '',
      status: 'all'
    });
  }, []);

  return {
    filters,
    filteredConfigs,
    updateFilter,
    resetFilters
  };
}
