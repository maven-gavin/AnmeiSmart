'use client';

import { useState, useEffect, useRef } from 'react';
import { Search, ChevronLeft, ChevronRight } from 'lucide-react';
import agentConfigService, { AgentConfig } from '@/service/agentConfigService';
import { cn } from '@/lib/utils';

interface AgentToolbarProps {
  selectedAgentId?: string;
  onAgentSelect: (agent: AgentConfig) => void;
  onAgentsLoaded?: (agents: AgentConfig[]) => void;
}

export default function AgentToolbar({ 
  selectedAgentId, 
  onAgentSelect,
  onAgentsLoaded 
}: AgentToolbarProps) {
  const [agents, setAgents] = useState<AgentConfig[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const [showLeftArrow, setShowLeftArrow] = useState(false);
  const [showRightArrow, setShowRightArrow] = useState(false);

  useEffect(() => {
    const fetchAgents = async () => {
      try {
        setIsLoading(true);
        const data = await agentConfigService.getAgentConfigs();
        // Filter only enabled agents if needed, or show all
        const enabledAgents = data.filter(a => a.enabled);
        setAgents(enabledAgents);
        if (onAgentsLoaded) {
          onAgentsLoaded(enabledAgents);
        }
      } catch (error) {
        console.error('Failed to load agents', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchAgents();
  }, [onAgentsLoaded]);

  const filteredAgents = agents.filter(agent => 
    agent.appName.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const checkScroll = () => {
    if (scrollContainerRef.current) {
      const { scrollLeft, scrollWidth, clientWidth } = scrollContainerRef.current;
      setShowLeftArrow(scrollLeft > 0);
      // Allow a small buffer (1px) for calculation errors
      setShowRightArrow(scrollLeft < scrollWidth - clientWidth - 1);
    }
  };

  useEffect(() => {
    checkScroll();
    window.addEventListener('resize', checkScroll);
    return () => window.removeEventListener('resize', checkScroll);
  }, [filteredAgents]);

  const scroll = (direction: 'left' | 'right') => {
    if (scrollContainerRef.current) {
      const scrollAmount = 200;
      scrollContainerRef.current.scrollBy({
        left: direction === 'left' ? -scrollAmount : scrollAmount,
        behavior: 'smooth'
      });
    }
  };

  return (
    <div className="flex flex-1 items-center mx-6 overflow-hidden h-10 bg-gray-50/50 rounded-lg border border-gray-100 p-1">
      {/* Search Component */}
      <div className="relative flex items-center w-48 flex-shrink-0 border-r border-gray-200 pr-2 mr-2">
        <Search className="absolute left-2 h-4 w-4 text-gray-400" />
        <input
          type="text"
          placeholder="搜索智能体..."
          className="h-8 w-full rounded-md bg-transparent pl-8 pr-2 text-sm outline-none placeholder:text-gray-400 focus:bg-white focus:ring-1 focus:ring-orange-200 transition-all"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </div>

      {/* Scrollable Agent Container */}
      <div className="relative flex flex-1 items-center overflow-hidden group">
        {/* Left Arrow */}
        {showLeftArrow && (
          <button 
            onClick={() => scroll('left')}
            className="absolute left-0 z-10 flex h-full items-center justify-center bg-gradient-to-r from-white to-transparent px-1 text-gray-500 hover:text-orange-500"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
        )}

        {/* Agent List */}
        <div 
          ref={scrollContainerRef}
          onScroll={checkScroll}
          className="flex items-center space-x-2 overflow-x-auto scrollbar-hide px-1 w-full"
          style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
        >
          {filteredAgents.map(agent => (
            <button
              key={agent.id}
              onClick={() => onAgentSelect(agent)}
              className={cn(
                "flex items-center whitespace-nowrap rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
                selectedAgentId === agent.id
                  ? "bg-orange-100 text-orange-700"
                  : "text-gray-600 hover:bg-gray-200 hover:text-gray-900"
              )}
            >
              {agent.appName}
            </button>
          ))}
          {filteredAgents.length === 0 && !isLoading && (
            <span className="text-xs text-gray-400 px-2">未找到智能体</span>
          )}
        </div>

        {/* Right Arrow */}
        {showRightArrow && (
          <button 
            onClick={() => scroll('right')}
            className="absolute right-0 z-10 flex h-full items-center justify-center bg-gradient-to-l from-white to-transparent px-1 text-gray-500 hover:text-orange-500"
          >
            <ChevronRight className="h-4 w-4" />
          </button>
        )}
      </div>
    </div>
  );
}

