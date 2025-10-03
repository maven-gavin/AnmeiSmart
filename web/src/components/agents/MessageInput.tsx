import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Send, StopCircle, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

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
  const [isSending, setIsSending] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = async () => {
    const trimmed = input.trim();
    if (!trimmed || disabled || isResponding) return;
    
    setIsSending(true);
    try {
      onSend(trimmed);
      setInput('');
    } finally {
      // 短暂延迟后重置发送状态
      setTimeout(() => setIsSending(false), 500);
    }
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

  // 清空输入时重置高度
  useEffect(() => {
    if (!input && textareaRef.current) {
      textareaRef.current.style.height = 'auto';
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
            className={cn(
              "flex items-center space-x-2 border-red-300 text-red-600",
              "hover:bg-red-50 hover:border-red-400",
              "transition-all duration-200"
            )}
          >
            <StopCircle className="h-4 w-4 animate-pulse" />
            <span>停止</span>
          </Button>
        ) : (
          <Button
            onClick={handleSend}
            disabled={disabled || !input.trim() || isSending}
            className={cn(
              "flex items-center space-x-2 bg-orange-500 hover:bg-orange-600",
              "disabled:bg-gray-300 disabled:cursor-not-allowed",
              "transition-all duration-200"
            )}
          >
            {isSending ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>发送中</span>
              </>
            ) : (
              <>
                <Send className="h-4 w-4" />
                <span>发送</span>
              </>
            )}
          </Button>
        )}
      </div>
    </div>
  );
}

