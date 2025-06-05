'use client';

import React, { useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { RecordingControls } from '@/components/chat/RecordingControls';
import { MediaPreview } from '@/components/chat/MediaPreview';

interface MessageInputProps {
  message: string;
  setMessage: (message: string) => void;
  imagePreview: string | null;
  audioPreview: string | null;
  isRecording: boolean;
  recordingTime: number;
  isSending: boolean;
  handleSendMessage: () => Promise<void>;
  startRecording: () => Promise<void>;
  stopRecording: () => void;
  cancelRecording: () => void;
  cancelImagePreview: () => void;
  cancelAudioPreview: () => void;
  triggerFileSelect: () => void;
  toggleFAQ: () => void;
  toggleSearch: () => void;
  isConsultant: boolean;
  isConsultantTakeover: boolean;
  toggleConsultantMode: () => void;
  showFAQ: boolean;
  showSearch: boolean;
  sendError?: string | null;
  setSendError?: (error: string | null) => void;
}

export default function MessageInput({
  message,
  setMessage,
  imagePreview,
  audioPreview,
  isRecording,
  recordingTime,
  isSending,
  handleSendMessage,
  startRecording,
  stopRecording,
  cancelRecording,
  cancelImagePreview,
  cancelAudioPreview,
  triggerFileSelect,
  toggleFAQ,
  toggleSearch,
  isConsultant,
  isConsultantTakeover,
  toggleConsultantMode,
  showFAQ,
  showSearch,
  sendError,
  setSendError
}: MessageInputProps) {
  
  // 格式化录音时间
  const formatRecordingTime = useCallback((seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
  }, []);
  
  return (
    <>
      {/* 错误提示 */}
      {sendError && (
        <div className="border-t border-gray-200 bg-red-50 p-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center text-red-700">
              <svg className="h-4 w-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              <span className="text-sm">{sendError}</span>
            </div>
            {setSendError && (
              <button 
                onClick={() => setSendError(null)}
                className="text-red-500 hover:text-red-700"
              >
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>
        </div>
      )}

      {/* 使用 RecordingControls 组件 */}
      <RecordingControls
        isRecording={isRecording}
        recordingTime={recordingTime}
        formatRecordingTime={formatRecordingTime}
        onCancel={cancelRecording}
        onStop={stopRecording}
      />
      
      {/* 使用 MediaPreview 组件 */}
      <MediaPreview
        imagePreview={imagePreview}
        audioPreview={audioPreview && !isRecording ? audioPreview : null}
        onCancelImage={cancelImagePreview}
        onCancelAudio={cancelAudioPreview}
      />
      
      {/* 输入区域 */}
      <div className="border-t border-gray-200 bg-white p-4">
        <div className="flex space-x-4">
          <button 
            className={`flex-shrink-0 ${showFAQ ? 'text-orange-500' : 'text-gray-500 hover:text-gray-700'}`}
            onClick={toggleFAQ}
            title="常见问题"
          >
            <svg
              className="h-6 w-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </button>
          
          <button 
            className={`flex-shrink-0 ${showSearch ? 'text-orange-500' : 'text-gray-500 hover:text-gray-700'}`}
            onClick={toggleSearch}
            title="搜索聊天记录"
          >
            <svg
              className="h-6 w-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          </button>
          
          {/* 顾问接管按钮 - 只对顾问角色显示 */}
          {isConsultant && (
            <button 
              className={`flex-shrink-0 ${isConsultantTakeover ? 'text-green-500' : 'text-gray-500 hover:text-gray-700'}`}
              onClick={toggleConsultantMode}
              title={isConsultantTakeover ? "切换回AI助手" : "顾问接管"}
            >
              <svg
                className="h-6 w-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d={isConsultantTakeover 
                    ? "M13 10V3L4 14h7v7l9-11h-7z" // 闪电图标，表示切换回AI
                    : "M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" // 用户图标，表示顾问接管
                  }
                />
              </svg>
            </button>
          )}
                    
          <button className="flex-shrink-0 text-gray-500 hover:text-gray-700" title="表情">
            <svg
              className="h-6 w-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </button>
          
          <button 
            className="flex-shrink-0 text-gray-500 hover:text-gray-700"
            title="图片"
            onClick={triggerFileSelect}
          >
            <svg
              className="h-6 w-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
          </button>
          
          <button 
            className={`flex-shrink-0 ${isRecording ? 'text-red-500' : 'text-gray-500 hover:text-gray-700'}`}
            title="语音"
            onClick={isRecording ? stopRecording : startRecording}
          >
            <svg
              className="h-6 w-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
              />
            </svg>
          </button>
          
          <div className="flex flex-1 items-center space-x-2">
            <input
              type="text"
              value={message}
              onChange={e => setMessage(e.target.value)}
              placeholder="输入消息..."
              className="flex-1 rounded-lg border border-gray-200 px-4 py-2 focus:border-orange-500 focus:outline-none"
              disabled={isRecording || isSending}
              onKeyPress={e => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
            />
            <Button
              onClick={handleSendMessage}
              disabled={isRecording || isSending || (!message.trim() && !imagePreview && !audioPreview)}
              className={isSending ? 'opacity-70 cursor-not-allowed' : ''}
            >
              {isSending ? (
                <span className="flex items-center">
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  发送中
                </span>
              ) : '发送'}
            </Button>
          </div>
        </div>
      </div>
    </>
  );
} 