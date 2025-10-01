import { User } from 'lucide-react';
import type { AgentMessage } from '@/types/agent-chat';

interface UserMessageProps {
  message: AgentMessage;
}

export function UserMessage({ message }: UserMessageProps) {
  return (
    <div className="flex items-start space-x-3">
      <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-blue-100">
        <User className="h-5 w-5 text-blue-600" />
      </div>
      <div className="flex-1">
        <div className="rounded-lg bg-blue-50 px-4 py-3">
          <p className="text-sm text-gray-900 whitespace-pre-wrap">{message.content}</p>
        </div>
        <p className="mt-1 text-xs text-gray-400">
          {new Date(message.timestamp).toLocaleTimeString()}
        </p>
      </div>
    </div>
  );
}

