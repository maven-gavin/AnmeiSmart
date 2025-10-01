import { ChevronDown, ChevronRight } from 'lucide-react';
import { useState } from 'react';
import type { AgentThought } from '@/types/agent-chat';

interface AgentThinkingProps {
  thoughts: AgentThought[];
}

export function AgentThinking({ thoughts }: AgentThinkingProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!thoughts || thoughts.length === 0) return null;

  return (
    <div className="mb-3 rounded-lg border border-purple-200 bg-purple-50">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex w-full items-center justify-between px-4 py-2 text-sm font-medium text-purple-900 hover:bg-purple-100"
      >
        <span>🧠 Agent 思考过程 ({thoughts.length} 步)</span>
        {isExpanded ? (
          <ChevronDown className="h-4 w-4" />
        ) : (
          <ChevronRight className="h-4 w-4" />
        )}
      </button>
      
      {isExpanded && (
        <div className="border-t border-purple-200 px-4 py-3 space-y-3">
          {thoughts.map((thought, index) => (
            <div key={thought.id} className="text-sm">
              <div className="flex items-start space-x-2">
                <span className="flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-purple-200 text-xs font-medium text-purple-900">
                  {index + 1}
                </span>
                <div className="flex-1">
                  {thought.tool && (
                    <p className="font-medium text-purple-900">
                      🔧 使用工具: {thought.tool}
                    </p>
                  )}
                  {thought.thought && (
                    <p className="mt-1 text-gray-700">{thought.thought}</p>
                  )}
                  {thought.observation && (
                    <p className="mt-1 text-gray-600">💡 {thought.observation}</p>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

