'use client';

import { useCallback, useState } from 'react';
import { sendImageMessage, sendVoiceMessage } from '@/service/chatService';

interface MediaPreviewProps {
  conversationId?: string | null;
  imagePreview?: string | null;
  audioPreview?: string | null;
  onCancelImage?: () => void;
  onCancelAudio?: () => void;
  onSendSuccess?: () => void;
  onUpdateMessages?: () => void;
}

export function MediaPreview({ 
  conversationId,
  imagePreview, 
  audioPreview, 
  onCancelImage, 
  onCancelAudio,
  onSendSuccess,
  onUpdateMessages
}: MediaPreviewProps) {
  const [sendError, setSendError] = useState<string | null>(null);
  const [isSending, setIsSending] = useState(false);

  // 发送图片消息
  const handleSendImage = useCallback(async () => {
    if (!imagePreview || !conversationId || isSending) return;
    
    try {
      setIsSending(true);
      setSendError(null);
      
      await sendImageMessage(conversationId, imagePreview);
      
      // 清除预览
      onCancelImage?.();
      
      // 通知父组件更新消息
      onUpdateMessages?.();
      onSendSuccess?.();
      
    } catch (error) {
      console.error('发送图片失败:', error);
      setSendError('发送图片失败，请稍后重试');
    } finally {
      setIsSending(false);
    }
  }, [imagePreview, conversationId, isSending, onCancelImage, onUpdateMessages, onSendSuccess]);

  // 发送语音消息
  const handleSendAudio = useCallback(async () => {
    if (!audioPreview || !conversationId || isSending) return;
    
    try {
      setIsSending(true);
      setSendError(null);
      
      await sendVoiceMessage(conversationId, audioPreview);
      
      // 清除预览
      onCancelAudio?.();
      
      // 通知父组件更新消息
      onUpdateMessages?.();
      onSendSuccess?.();
      
    } catch (error) {
      console.error('发送语音失败:', error);
      setSendError('发送语音失败，请稍后重试');
    } finally {
      setIsSending(false);
    }
  }, [audioPreview, conversationId, isSending, onCancelAudio, onUpdateMessages, onSendSuccess]);

  if (!imagePreview && !audioPreview) {
    return null;
  }

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
            <button 
              onClick={() => setSendError(null)}
              className="text-red-500 hover:text-red-700"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      )}

      {/* 图片预览 */}
      {imagePreview && (
        <div className="border-t border-gray-200 bg-gray-50 p-3">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-gray-700">图片预览</span>
            <div className="flex items-center space-x-2">
              {conversationId && (
                <button
                  onClick={handleSendImage}
                  disabled={isSending}
                  className="px-3 py-1 text-sm bg-orange-500 text-white rounded hover:bg-orange-600 disabled:opacity-50"
                >
                  {isSending ? '发送中...' : '发送'}
                </button>
              )}
              <button 
                onClick={onCancelImage}
                className="text-gray-500 hover:text-gray-700"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
          <div className="relative">
            <img 
              src={imagePreview} 
              alt="预览图片" 
              className="max-h-40 max-w-full rounded-lg object-contain"
            />
          </div>
        </div>
      )}

      {/* 音频预览 */}
      {audioPreview && (
        <div className="border-t border-gray-200 bg-gray-50 p-3">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-gray-700">语音预览</span>
            <div className="flex items-center space-x-2">
              {conversationId && (
                <button
                  onClick={handleSendAudio}
                  disabled={isSending}
                  className="px-3 py-1 text-sm bg-orange-500 text-white rounded hover:bg-orange-600 disabled:opacity-50"
                >
                  {isSending ? '发送中...' : '发送'}
                </button>
              )}
              <button 
                onClick={onCancelAudio}
                className="text-gray-500 hover:text-gray-700"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
          <audio src={audioPreview} controls className="w-full" />
        </div>
      )}
    </>
  )
} 