import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Send, StopCircle } from 'lucide-react';

interface MessageInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  isResponding?: boolean;
  onStop?: () => void;
  placeholder?: string;
}

export function MessageInput({ 
  onSend, 
  disabled, 
  isResponding,
  onStop,
  placeholder = '输入消息...'
}: MessageInputProps) {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    const trimmed = input.trim();
    if (!trimmed || disabled) return;
    
    onSend(trimmed);
    setInput('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // 自动调整高度
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
    }
  }, [input]);

  return (
    <div className="border-t border-gray-200 bg-white p-4">
      <div className="flex items-end space-x-4">
        <div className="flex-1">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled}
            rows={1}
            className="w-full resize-none rounded-lg border border-gray-300 px-4 py-2 focus:border-orange-500 focus:outline-none focus:ring-1 focus:ring-orange-500 disabled:bg-gray-50 disabled:text-gray-500"
            style={{ maxHeight: '150px' }}
          />
          <div className="mt-1 flex items-center justify-between text-xs text-gray-500">
            <span>按 Enter 发送，Shift+Enter 换行</span>
            <span>{input.length} 字符</span>
          </div>
        </div>
        
        {isResponding ? (
          <Button
            onClick={onStop}
            variant="outline"
            className="flex items-center space-x-2"
          >
            <StopCircle className="h-4 w-4" />
            <span>停止</span>
          </Button>
        ) : (
          <Button
            onClick={handleSend}
            disabled={disabled || !input.trim()}
            className="bg-orange-500 hover:bg-orange-600 flex items-center space-x-2"
          >
            <Send className="h-4 w-4" />
            <span>发送</span>
          </Button>
        )}
      </div>
    </div>
  );
}

