'use client';

import { useRef, useEffect, useState } from 'react';
import { AgentChatPanel } from '@/components/agents/AgentChatPanel';
import { ChevronUp, BrainCircuit } from 'lucide-react';
import { cn } from '@/lib/utils';
import { DigitalHuman } from '@/types/digital-human';
import { AgentConfig } from '@/service/agentConfigService';

interface DigitalHumanDrawerProps {
  isOpen: boolean;
  digitalHuman: DigitalHuman | null;
  onClose: () => void;
  onDigitalHumanChange: (item: DigitalHuman) => void;
  allDigitalHumans: DigitalHuman[];
}

export function DigitalHumanDrawer({
  isOpen,
  digitalHuman,
  onClose,
  onDigitalHumanChange,
  allDigitalHumans
}: DigitalHumanDrawerProps) {
  const drawerRef = useRef<HTMLDivElement>(null);
  const [activeAgent, setActiveAgent] = useState<AgentConfig | null>(null);

  // 当数字人改变时，自动选择优先级最高的智能体
  useEffect(() => {
    if (digitalHuman && digitalHuman.agent_configs && digitalHuman.agent_configs.length > 0) {
      // 找到已启用的优先级最高的智能体 (优先级数字越小越高)
      const activeConfigs = digitalHuman.agent_configs
        .filter(c => c.is_active)
        .sort((a, b) => a.priority - b.priority);
      
      if (activeConfigs.length > 0) {
        // 转换后端格式到前端 AgentConfig 格式
        const topConfig = activeConfigs[0].agent_config;
        setActiveAgent({
          id: topConfig.id,
          appName: topConfig.app_name,
          appId: topConfig.app_id,
          environment: topConfig.environment,
          description: topConfig.description,
          enabled: topConfig.enabled,
          baseUrl: '', // 这些在聊天钩子中可能需要，但通常后端会处理
          timeoutSeconds: 30,
          maxRetries: 3,
          createdAt: '',
          updatedAt: ''
        } as AgentConfig);
      } else {
        setActiveAgent(null);
      }
    } else {
      setActiveAgent(null);
    }
  }, [digitalHuman]);

  // Handle click outside to close
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      // Logic for closing on background click is already handled by the overlay div
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [onClose]);

  // Prevent body scroll when drawer is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  if (!isOpen || !digitalHuman) return null;

  return (
    <div 
      className="fixed top-16 inset-x-0 bottom-0 z-40 bg-black/30 backdrop-blur-[2px] transition-all duration-300"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div 
        ref={drawerRef}
        className={cn(
          "relative w-full bg-white shadow-2xl transition-all duration-500 ease-out flex flex-col",
          "h-full animate-in slide-in-from-top-full border-t border-gray-100 overflow-hidden"
        )}
      >
        <div className="relative flex-1 overflow-hidden">
          {activeAgent ? (
            <AgentChatPanel 
              agents={[]} // 不再需要左侧侧边栏
              selectedAgent={activeAgent}
              digitalHuman={digitalHuman}
              onSelectAgent={setActiveAgent}
              hideSidebar={true}
              className="!h-full"
            />
          ) : (
            <div className="flex h-full flex-col items-center justify-center p-10 text-center">
              <div className="mb-6 rounded-full bg-orange-50 p-6">
                <BrainCircuit className="h-12 w-12 text-orange-400" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                该数字人尚未配置大脑
              </h3>
              <p className="text-gray-500 max-w-md">
                请在“数字人管理”中为 {digitalHuman.name} 关联并启用至少一个智能体能力，才能开始对话。
              </p>
            </div>
          )}
          
          {/* Collapse Button - Absolute positioned at bottom left */}
          <button
            onClick={onClose}
            className="absolute bottom-8 left-8 z-50 flex items-center justify-center h-12 w-12 rounded-full bg-white border border-gray-100 shadow-xl hover:bg-gray-50 text-gray-400 hover:text-orange-500 transition-all hover:scale-110 active:scale-95 group"
            title="收起"
          >
            <ChevronUp className="h-7 w-7 group-hover:-translate-y-1 transition-transform" />
          </button>
        </div>
      </div>
    </div>
  );
}

