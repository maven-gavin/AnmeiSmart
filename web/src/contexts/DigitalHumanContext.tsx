'use client';

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { DigitalHuman, DigitalHumanAgentConfig } from '@/types/digital-human';
import { AgentConfig } from '@/service/agentConfigService';

interface DigitalHumanContextType {
  currentDigitalHuman: DigitalHuman | null;
  currentActiveAgent: AgentConfig | null;
  isDrawerOpen: boolean;
  
  // 操作方法
  openDigitalHuman: (dh: DigitalHuman) => void;
  closeDigitalHuman: () => void;
  switchActiveAgent: (agentConfig: AgentConfig) => void;
  
  // 辅助数据
  availableAgents: AgentConfig[];
}

const DigitalHumanContext = createContext<DigitalHumanContextType | undefined>(undefined);

export function DigitalHumanProvider({ children }: { children: React.ReactNode }) {
  const [currentDigitalHuman, setCurrentDigitalHuman] = useState<DigitalHuman | null>(null);
  const [currentActiveAgent, setCurrentActiveAgent] = useState<AgentConfig | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  // 转换后端 AgentConfig 到前端格式
  const mapToFrontendAgent = useCallback((apiAgent: any): AgentConfig => {
    return {
      id: apiAgent.id,
      appName: apiAgent.app_name || apiAgent.appName,
      appId: apiAgent.app_id || apiAgent.appId,
      environment: apiAgent.environment,
      description: apiAgent.description,
      enabled: apiAgent.enabled,
      baseUrl: '', 
      timeoutSeconds: 30,
      maxRetries: 3,
      createdAt: '',
      updatedAt: ''
    } as AgentConfig;
  }, []);

  // 当选择数字人时，默认激活优先级最高的智能体
  const openDigitalHuman = useCallback((dh: DigitalHuman) => {
    setCurrentDigitalHuman(dh);
    setIsDrawerOpen(true);
    
    if (dh.agent_configs && dh.agent_configs.length > 0) {
      const activeConfigs = dh.agent_configs
        .filter(c => c.is_active)
        .sort((a, b) => a.priority - b.priority);
      
      if (activeConfigs.length > 0) {
        setCurrentActiveAgent(mapToFrontendAgent(activeConfigs[0].agent_config));
      } else {
        setCurrentActiveAgent(null);
      }
    } else {
      setCurrentActiveAgent(null);
    }
  }, [mapToFrontendAgent]);

  const closeDigitalHuman = useCallback(() => {
    setIsDrawerOpen(false);
    // 延迟清除数据，保证动画平滑
    setTimeout(() => {
      setCurrentDigitalHuman(null);
      setCurrentActiveAgent(null);
    }, 300);
  }, []);

  const switchActiveAgent = useCallback((agent: AgentConfig) => {
    setCurrentActiveAgent(agent);
  }, []);

  // 获取当前数字人所有可用的智能体能力
  const availableAgents = React.useMemo(() => {
    if (!currentDigitalHuman?.agent_configs) return [];
    return currentDigitalHuman.agent_configs
      .filter(c => c.is_active)
      .sort((a, b) => a.priority - b.priority)
      .map(c => mapToFrontendAgent(c.agent_config));
  }, [currentDigitalHuman, mapToFrontendAgent]);

  return (
    <DigitalHumanContext.Provider
      value={{
        currentDigitalHuman,
        currentActiveAgent,
        isDrawerOpen,
        openDigitalHuman,
        closeDigitalHuman,
        switchActiveAgent,
        availableAgents,
      }}
    >
      {children}
    </DigitalHumanContext.Provider>
  );
}

export function useDigitalHuman() {
  const context = useContext(DigitalHumanContext);
  if (context === undefined) {
    throw new Error('useDigitalHuman must be used within a DigitalHumanProvider');
  }
  return context;
}
