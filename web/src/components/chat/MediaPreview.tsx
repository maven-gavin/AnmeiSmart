'use client';

import { useCallback, useState } from 'react';
import { FileService } from '@/service/fileService';
import toast from 'react-hot-toast';

interface MediaPreviewProps {
  conversationId?: string | null;
  imagePreview?: string | null;
  audioPreview?: string | null;
  onCancelImage?: () => void;
  onCancelAudio?: () => void;
  onSendSuccess?: () => void;
  onUpdateMessages?: () => void;
  onSendImage?: (imageUrl: string) => void;
  onSendAudio?: (audioUrl: string) => void;
}

export function MediaPreview({ 
  conversationId,
  imagePreview, 
  audioPreview, 
  onCancelImage, 
  onCancelAudio,
  onSendSuccess,
  onUpdateMessages,
  onSendImage,
  onSendAudio
}: MediaPreviewProps) {
  const [sendError, setSendError] = useState<string | null>(null);
  const [isSending, setIsSending] = useState(false);

  // 将 base64 数据转换为 File 对象
  const dataURLToFile = useCallback((dataURL: string, filename: string): File => {
    const arr = dataURL.split(',');
    const mime = arr[0].match(/:(.*?);/)?.[1] || 'application/octet-stream';
    const bstr = atob(arr[1]);
    let n = bstr.length;
    const u8arr = new Uint8Array(n);
    
    while (n--) {
      u8arr[n] = bstr.charCodeAt(n);
    }
    
    return new File([u8arr], filename, { type: mime });
  }, []);

  // 上传媒体文件的通用方法
  const uploadMediaFile = useCallback(async (
    dataURL: string, 
    filename: string, 
    mediaType: 'image' | 'audio'
  ): Promise<string> => {
    if (!conversationId) {
      throw new Error('会话ID不能为空');
    }

    // 1. 将预览数据转换为文件
    const file = dataURLToFile(dataURL, filename);
    
    // 2. 上传文件到服务器
    const fileService = new FileService();
    const fileInfo = await fileService.uploadFile(file, conversationId);
    
    // 3. 返回文件URL供父组件使用
    return fileInfo.file_url;
  }, [conversationId, dataURLToFile]);

  // 发送图片
  const handleSendImage = useCallback(async () => {
    if (!imagePreview) {
      setSendError('没有图片可发送');
      return;
    }

    if (!onSendImage) {
      setSendError('发送功能未配置');
      return;
    }

    setIsSending(true);
    setSendError(null);

    try {
      const timestamp = Date.now();
      const filename = `image_${timestamp}.png`;
      
      // 上传文件并获取URL
      const imageUrl = await uploadMediaFile(imagePreview, filename, 'image');
      
      // 通过回调将URL传递给父组件，由父组件负责创建和发送消息
      onSendImage(imageUrl);
      
      // 成功后清理和回调
      toast.success('图片上传成功');
      
      if (onSendSuccess) {
        onSendSuccess();
      }
      
      if (onUpdateMessages) {
        onUpdateMessages();
      }

      // 发送成功后清除预览
      if (onCancelImage) {
        onCancelImage();
      }
      
    } catch (error) {
      console.error('图片上传失败:', error);
      const errorMessage = error instanceof Error ? error.message : '图片上传失败';
      setSendError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setIsSending(false);
    }
  }, [imagePreview, uploadMediaFile, onSendImage, onSendSuccess, onUpdateMessages, onCancelImage]);

  // 发送语音
  const handleSendAudio = useCallback(async () => {
    if (!audioPreview) {
      setSendError('没有语音可发送');
      return;
    }

    if (!onSendAudio) {
      setSendError('发送功能未配置');
      return;
    }

    setIsSending(true);
    setSendError(null);

    try {
      const timestamp = Date.now();
      const filename = `voice_${timestamp}.webm`;
      
      // 上传文件并获取URL
      const audioUrl = await uploadMediaFile(audioPreview, filename, 'audio');
      
      // 通过回调将URL传递给父组件，由父组件负责创建和发送消息
      onSendAudio(audioUrl);
      
      // 成功后清理和回调
      toast.success('语音上传成功');
      
      if (onSendSuccess) {
        onSendSuccess();
      }
      
      if (onUpdateMessages) {
        onUpdateMessages();
      }

      // 发送成功后清除预览
      if (onCancelAudio) {
        onCancelAudio();
      }
      
    } catch (error) {
      console.error('语音上传失败:', error);
      const errorMessage = error instanceof Error ? error.message : '语音上传失败';
      setSendError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setIsSending(false);
    }
  }, [audioPreview, uploadMediaFile, onSendAudio, onSendSuccess, onUpdateMessages, onCancelAudio]);

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
              className="text-red-500 hover:text-red-700 transition-colors"
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
              {conversationId && onSendImage && (
                <button
                  onClick={handleSendImage}
                  disabled={isSending}
                  className="px-3 py-1 text-sm bg-orange-500 text-white rounded hover:bg-orange-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {isSending ? (
                    <span className="flex items-center">
                      <svg className="animate-spin -ml-1 mr-2 h-3 w-3 text-white" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      上传中...
                    </span>
                  ) : (
                    '发送'
                  )}
                </button>
              )}
              <button 
                onClick={onCancelImage}
                disabled={isSending}
                className="text-gray-500 hover:text-gray-700 disabled:opacity-50 transition-colors"
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
              className="max-h-40 max-w-full rounded-lg object-contain shadow-sm"
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
              {conversationId && onSendAudio && (
                <button
                  onClick={handleSendAudio}
                  disabled={isSending}
                  className="px-3 py-1 text-sm bg-orange-500 text-white rounded hover:bg-orange-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {isSending ? (
                    <span className="flex items-center">
                      <svg className="animate-spin -ml-1 mr-2 h-3 w-3 text-white" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      上传中...
                    </span>
                  ) : (
                    '发送'
                  )}
                </button>
              )}
              <button 
                onClick={onCancelAudio}
                disabled={isSending}
                className="text-gray-500 hover:text-gray-700 disabled:opacity-50 transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
          <audio 
            src={audioPreview} 
            controls 
            className="w-full"
            style={{ height: '40px' }}
          />
        </div>
      )}
    </>
  )
} 