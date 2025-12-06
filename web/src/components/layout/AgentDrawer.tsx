'use client';

import { useRef, useEffect } from 'react';
import { AgentChatPanel } from '@/components/agents/AgentChatPanel';
import type { AgentConfig } from '@/service/agentConfigService';
import { ChevronUp } from 'lucide-react';
import { cn } from '@/lib/utils';

interface AgentDrawerProps {
  isOpen: boolean;
  agent: AgentConfig | null;
  onClose: () => void;
  onAgentChange: (agent: AgentConfig) => void;
  allAgents: AgentConfig[];
}

export default function AgentDrawer({
  isOpen,
  agent,
  onClose,
  onAgentChange,
  allAgents
}: AgentDrawerProps) {
  const drawerRef = useRef<HTMLDivElement>(null);

  // Handle click outside to close
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (drawerRef.current && !drawerRef.current.contains(event.target as Node)) {
        // Check if the click was on the toolbar (which is in the parent). 
        // We can't easily check that here without more context, so we rely on the header to handle clicks on toggle buttons.
        // But for clicking on the rest of the page (overlay), we might want to close.
        // For now, let's rely on the user explicitly closing or clicking the toolbar toggle.
      }
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

  if (!isOpen || !agent) return null;

  return (
    <div 
      className="fixed top-16 inset-x-0 bottom-0 z-40 bg-black/20 backdrop-blur-sm"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div 
        ref={drawerRef}
        className={cn(
          "relative w-full bg-white shadow-xl transition-all duration-300 ease-in-out flex flex-col",
          "h-full animate-in slide-in-from-top-4 border-t border-gray-200"
        )}
      >
        <div className="relative flex-1 overflow-hidden">
          <AgentChatPanel 
            agents={allAgents} // Pass all agents so internal logic works if needed, though sidebar is hidden
            selectedAgent={agent}
            onSelectAgent={onAgentChange}
            hideSidebar={true}
            className="!h-full" // Force full height to fit drawer
          />
          
          {/* Collapse Button - Absolute positioned at bottom left */}
          <button
            onClick={onClose}
            className="absolute bottom-6 left-6 z-50 flex items-center justify-center h-10 w-10 rounded-full bg-white border border-gray-200 shadow-lg hover:bg-gray-100 text-gray-600 transition-all hover:scale-105 group"
            title="收起"
          >
            <ChevronUp className="h-6 w-6 group-hover:-translate-y-0.5 transition-transform" />
          </button>
        </div>
      </div>
    </div>
  );
}

