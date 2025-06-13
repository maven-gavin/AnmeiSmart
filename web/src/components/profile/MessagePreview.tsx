'use client';

import { Message } from '@/types/chat';
import ChatMessage from '@/components/chat/message/ChatMessage';

interface MessagePreviewProps {
  show: boolean;
  messages: Message[];
  loading: boolean;
  onToggle: () => void;
}

export function MessagePreview({ show, messages, loading, onToggle }: MessagePreviewProps) {
  if (!show) {
    return null;
  }

  return (
    <div className="mt-4">
      <div className="flex items-center justify-between mb-3">
        <div className="text-sm font-medium text-gray-700">历史消息记录</div>
        <button 
          onClick={onToggle}
          className="text-xs text-gray-500 hover:text-gray-700"
        >
          收起
        </button>
      </div>
      
      <div className="bg-gray-50 rounded-lg p-3 max-h-[300px] overflow-y-auto border border-gray-200">
        {messages.length > 0 ? (
          <div className="space-y-2">
            {messages.map((message, index) => (
              <div key={index} className="text-sm">
                <ChatMessage 
                  message={message}
                  showAvatar={false}
                  showTimestamp={false}
                />
              </div>
            ))}
          </div>
        ) : loading ? (
          <div className="flex justify-center py-8">
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-orange-500 border-t-transparent"></div>
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            暂无消息记录
          </div>
        )}
      </div>
    </div>
  );
} 