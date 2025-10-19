import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Send, StopCircle, Loader2, Mic, Image as ImageIcon, Paperclip, X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useRecording } from '@/hooks/useRecording';
import { useMediaUpload } from '@/hooks/useMediaUpload';
import type { ApplicationParameters } from '@/types/agent-chat';

interface MessageInputProps {
  onSend: (message: string, files?: File[]) => void;
  disabled?: boolean;
  isResponding?: boolean;
  onStop?: () => void;
  placeholder?: string;
  config?: ApplicationParameters | null;  // 应用配置
}

export function MessageInput({ 
  onSend, 
  disabled, 
  isResponding,
  onStop,
  placeholder = '输入消息...',
  config
}: MessageInputProps) {
  const [input, setInput] = useState('');
  const [isSending, setIsSending] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // 音频预览
  const [audioPreview, setAudioPreview] = useState<string | null>(null);

  // 处理录音完成
  const handleRecordingComplete = async (audioBlob: Blob) => {
    const audioUrl = URL.createObjectURL(audioBlob);
    setAudioPreview(audioUrl);
  };

  // 语音录制
  const {
    isRecording,
    startRecording,
    stopRecording,
    cancelRecording
  } = useRecording({
    onRecordingComplete: handleRecordingComplete
  });

  // 文件上传
  const {
    imagePreview,
    filePreview,
    fileInputRef,
    fileInputForFileRef,
    handleImageUpload,
    handleFileUpload,
    cancelImagePreview,
    cancelFilePreview,
    getTempFile
  } = useMediaUpload();

  // 判断是否启用各项功能
  const enableVoice = config?.speech_to_text?.enabled ?? false;
  const enableFileUpload = config?.file_upload?.enabled ?? false;
  const allowedFileTypes = config?.file_upload?.allowed_file_types ?? [];

  const handleSend = async () => {
    const trimmed = input.trim();
    const hasContent = trimmed || imagePreview || filePreview || audioPreview;
    
    if (!hasContent || disabled || isResponding) return;
    
    setIsSending(true);
    try {
      // 收集文件
      const files: File[] = [];
      if (imagePreview) {
        const file = getTempFile();
        if (file) files.push(file);
      }
      if (filePreview) {
        const file = getTempFile();
        if (file) files.push(file);
      }
      
      onSend(trimmed, files.length > 0 ? files : undefined);
      
      // 清空状态
      setInput('');
      cancelImagePreview();
      cancelFilePreview();
      setAudioPreview(null);
    } finally {
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

  // 取消音频预览
  const cancelAudioPreview = () => {
    if (audioPreview) {
      URL.revokeObjectURL(audioPreview);
      setAudioPreview(null);
    }
  };

  // 判断是否可以发送
  const canSend = input.trim() || imagePreview || filePreview || audioPreview;

  return (
    <div className="border-t border-gray-200 bg-white p-4">
      {/* 媒体预览区 */}
      {(imagePreview || filePreview || audioPreview) && (
        <div className="mb-3 flex flex-wrap gap-2">
          {imagePreview && (
            <div className="relative">
              <img
                src={imagePreview}
                alt="预览"
                className="h-20 w-20 rounded-lg object-cover"
              />
              <button
                onClick={cancelImagePreview}
                className="absolute -right-2 -top-2 rounded-full bg-red-500 p-1 text-white hover:bg-red-600"
              >
                <X className="h-3 w-3" />
              </button>
            </div>
          )}
          {filePreview && (
            <div className="relative flex h-20 w-32 items-center justify-center rounded-lg border border-gray-300 bg-gray-50 p-2">
              <div className="text-center">
                <Paperclip className="mx-auto h-6 w-6 text-gray-400" />
                <p className="mt-1 truncate text-xs text-gray-600">
                  {filePreview.name}
                </p>
              </div>
              <button
                onClick={cancelFilePreview}
                className="absolute -right-2 -top-2 rounded-full bg-red-500 p-1 text-white hover:bg-red-600"
              >
                <X className="h-3 w-3" />
              </button>
            </div>
          )}
          {audioPreview && (
            <div className="relative flex h-20 w-32 items-center justify-center rounded-lg border border-gray-300 bg-gray-50 p-2">
              <div className="text-center">
                <Mic className="mx-auto h-6 w-6 text-orange-500" />
                <p className="mt-1 text-xs text-gray-600">语音消息</p>
              </div>
              <button
                onClick={cancelAudioPreview}
                className="absolute -right-2 -top-2 rounded-full bg-red-500 p-1 text-white hover:bg-red-600"
              >
                <X className="h-3 w-3" />
              </button>
            </div>
          )}
        </div>
      )}

      <div className="flex items-end space-x-2">
        {/* 工具栏 */}
        <div className="flex items-center space-x-1">
          {/* 语音输入 */}
          {enableVoice && (
            <Button
              variant="ghost"
              size="sm"
              onClick={isRecording ? stopRecording : startRecording}
              disabled={disabled || isResponding}
              title={isRecording ? '停止录音' : '语音输入'}
              className={cn(
                "h-9 w-9 p-0",
                isRecording && "text-red-500 animate-pulse"
              )}
            >
              <Mic className="h-5 w-5" />
            </Button>
          )}

          {/* 图片上传 */}
          {enableFileUpload && allowedFileTypes.includes('image') && (
            <>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleImageUpload}
                className="hidden"
              />
              <Button
                variant="ghost"
                size="sm"
                onClick={() => fileInputRef.current?.click()}
                disabled={disabled || isResponding}
                title="上传图片"
                className="h-9 w-9 p-0"
              >
                <ImageIcon className="h-5 w-5" />
              </Button>
            </>
          )}

          {/* 文件上传 */}
          {enableFileUpload && (
            <>
              <input
                ref={fileInputForFileRef}
                type="file"
                onChange={handleFileUpload}
                className="hidden"
              />
              <Button
                variant="ghost"
                size="sm"
                onClick={() => fileInputForFileRef.current?.click()}
                disabled={disabled || isResponding}
                title="上传文件"
                className="h-9 w-9 p-0"
              >
                <Paperclip className="h-5 w-5" />
              </Button>
            </>
          )}
        </div>

        {/* 输入框 */}
        <div className="flex-1">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled || isRecording}
            rows={1}
            className="w-full resize-none rounded-lg border border-gray-300 px-4 py-2 focus:border-orange-500 focus:outline-none focus:ring-1 focus:ring-orange-500 disabled:bg-gray-50 disabled:text-gray-500"
            style={{ maxHeight: '150px' }}
          />
          <div className="mt-1 flex items-center justify-between text-xs text-gray-500">
            <span>按 Enter 发送，Shift+Enter 换行</span>
            <span>{input.length} 字符</span>
          </div>
        </div>
        
        {/* 发送/停止按钮 */}
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
            disabled={disabled || !canSend || isSending}
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

