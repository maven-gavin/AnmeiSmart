'use client';

import { useRef, useEffect } from 'react';
import { AgentChatPanel } from '@/components/agents/AgentChatPanel';
import { ChevronUp, BrainCircuit, Sparkles, Settings2, MessageSquare, Info } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useDigitalHuman } from '@/contexts/DigitalHumanContext';
import { AvatarCircle } from '@/components/ui/AvatarCircle';
import { Badge } from '@/components/ui/badge';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';

export function DigitalHumanDrawer() {
  const drawerRef = useRef<HTMLDivElement>(null);
  const { 
    currentDigitalHuman: digitalHuman, 
    currentActiveAgent: activeAgent, 
    isDrawerOpen, 
    closeDigitalHuman,
    availableAgents,
    switchActiveAgent
  } = useDigitalHuman();

  // Prevent body scroll when drawer is open
  useEffect(() => {
    if (isDrawerOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isDrawerOpen]);

  if (!isDrawerOpen || !digitalHuman) return null;

  return (
    <div 
      className="fixed inset-0 z-40 bg-black/40 backdrop-blur-[4px] transition-all duration-300"
      onClick={(e) => {
        if (e.target === e.currentTarget) closeDigitalHuman();
      }}
    >
      <div 
        ref={drawerRef}
        className={cn(
          "fixed inset-x-0 bottom-0 z-50 flex flex-col bg-white shadow-2xl transition-all duration-500 ease-out",
          "h-full animate-in slide-in-from-top-full border-t border-gray-100 overflow-hidden",
          isDrawerOpen ? "translate-y-0" : "translate-y-full"
        )}
        onClick={(e) => e.stopPropagation()}
      >
        {/* 工作站头部 (Workstation Header) */}
        <div className="relative flex-shrink-0 bg-gradient-to-b from-gray-50/80 to-white px-8 pt-6 pb-4 border-b border-gray-100/50">
          <div className="flex items-start justify-between">
            <div className="flex items-center space-x-6">
              <div className="relative group">
                <div className="absolute -inset-1 bg-gradient-to-r from-orange-400 to-rose-400 rounded-full blur opacity-25 group-hover:opacity-50 transition duration-1000 group-hover:duration-200"></div>
                <AvatarCircle
                  name={digitalHuman.name}
                  avatar={digitalHuman.avatar}
                  sizeClassName="w-20 h-20"
                  className="relative ring-4 ring-white shadow-xl"
                />
                <div className="absolute -bottom-1 -right-1 h-6 w-6 rounded-full bg-green-500 border-4 border-white shadow-sm" />
              </div>

              <div className="flex flex-col space-y-2">
                <div className="flex items-center space-x-3">
                  <h2 className="text-2xl font-bold text-gray-900 tracking-tight">{digitalHuman.name}</h2>
                  <Badge variant="secondary" className="bg-orange-50 text-orange-600 border-orange-100/50 font-medium py-0.5 px-2">
                    <Sparkles className="h-3 w-3 mr-1" />
                    数字员工
                  </Badge>
                </div>
                
                <p className="text-sm text-gray-500 max-w-xl line-clamp-2 leading-relaxed italic">
                  “{digitalHuman.description || '为您提供专业的智能服务'}”
                </p>

                {/* 能力切换器 (Capability Switcher) - 平滑切换逻辑 */}
                <div className="flex items-center gap-2 mt-2 pt-2">
                  <span className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mr-2 flex items-center">
                    <BrainCircuit className="h-3 w-3 mr-1" />
                    能力矩阵
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {availableAgents.map((agent) => (
                      <TooltipProvider key={agent.id}>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <button
                              onClick={() => switchActiveAgent(agent)}
                              className={cn(
                                "flex items-center space-x-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all duration-300 border",
                                activeAgent?.id === agent.id
                                  ? "bg-orange-500 text-white border-orange-500 shadow-md shadow-orange-200 scale-105"
                                  : "bg-white text-gray-600 border-gray-100 hover:border-orange-200 hover:bg-orange-50/30"
                              )}
                            >
                              <span>{agent.appName}</span>
                            </button>
                          </TooltipTrigger>
                          <TooltipContent side="bottom" className="text-xs bg-gray-900 text-white border-none px-3 py-2">
                            <p className="font-semibold mb-1">{agent.appName}</p>
                            <p className="text-gray-400 opacity-90">{agent.description || '暂无描述'}</p>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* 功能快捷入口 */}
            <div className="flex items-center space-x-3 pr-2">
              <button className="p-3 rounded-2xl bg-gray-50 text-gray-400 hover:text-orange-500 hover:bg-orange-50 transition-all duration-300">
                <Settings2 className="h-5 w-5" />
              </button>
              <button className="p-3 rounded-2xl bg-gray-50 text-gray-400 hover:text-orange-500 hover:bg-orange-50 transition-all duration-300">
                <Info className="h-5 w-5" />
              </button>
              <div className="w-px h-8 bg-gray-100 mx-2" />
              <button 
                onClick={closeDigitalHuman}
                className="group p-3 rounded-2xl bg-gray-900 text-white hover:bg-orange-600 transition-all duration-500 shadow-lg shadow-gray-200 hover:shadow-orange-200"
              >
                <ChevronUp className="h-6 w-6 group-hover:-translate-y-1 transition-transform" />
              </button>
            </div>
          </div>

          {/* 装饰性背景 */}
          <div className="absolute top-0 right-0 -z-10 opacity-[0.03] pointer-events-none">
            <Sparkles className="w-64 h-64 text-orange-500" />
          </div>
        </div>

        {/* 主体聊天区域 (Workstation Content) */}
        <div className="relative flex-1 overflow-hidden bg-white">
          {activeAgent ? (
            <AgentChatPanel 
              agents={[]} 
              selectedAgent={activeAgent}
              digitalHuman={digitalHuman}
              hideSidebar={true}
              className="!h-full"
            />
          ) : (
            <div className="flex h-full flex-col items-center justify-center p-10 text-center animate-in fade-in duration-700">
              <div className="mb-8 rounded-[2rem] bg-orange-50 p-10 relative">
                <BrainCircuit className="h-20 w-20 text-orange-400" />
                <div className="absolute -top-2 -right-2 bg-rose-500 text-white p-2 rounded-full shadow-lg">
                  <Sparkles className="h-5 w-5" />
                </div>
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-4 tracking-tight">
                该数字人尚未配置大脑
              </h3>
              <p className="text-gray-500 max-w-md text-lg leading-relaxed">
                请在“数字人管理”中为 <span className="text-orange-600 font-bold">{digitalHuman.name}</span> 关联并启用至少一个智能体能力，才能开始对话。
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
