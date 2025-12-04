'use client';

import React, { useCallback, useState, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { RecordingControls } from '@/components/chat/RecordingControls';
import { MediaPreview } from '@/components/chat/MediaPreview';
import FAQSection from '@/components/chat/FAQSection';
import ConsultantTakeover from '@/components/chat/ConsultantTakeover';
import { useRecording } from '@/hooks/useRecording';
import { useMediaUpload } from '@/hooks/useMediaUpload';
import { type Message, type FileInfo, type MediaMessageContent, type TextMessageContent } from '@/types/chat';
import { v4 as uuidv4 } from 'uuid';
import { authService } from "@/service/authService";
import { ApiClientError, ErrorType } from '@/service/apiClient';
import FileSelector from './FileSelector';
import { MessageUtils } from '@/utils/messageUtils';
import { apiClient } from '@/service/apiClient';
import { useAuthContext } from '@/contexts/AuthContext';
import { saveMessage } from '@/service/chatService';
import PlanGenerationButton from './PlanGenerationButton';
import { useSearchParams } from 'next/navigation';
import { Send, Smile, Image, Paperclip, Mic } from 'lucide-react';

interface MessageInputProps {
  conversationId: string;
  onSendMessage: (message: Message) => Promise<void>;
  onUpdateMessages?: () => void;
  messages?: Message[]; // 传递给FAQ使用
  onInputFocus?: () => void; // 新增：输入框获得焦点时的回调
  onMessageAdded?: (message: Message) => void; // 新增：消息添加回调，用于更新消息状态
}

export default function MessageInput({
  conversationId,
  onSendMessage,
  onUpdateMessages,
  messages = [],
  onInputFocus,
  onMessageAdded
}: MessageInputProps) {
  const { user } = useAuthContext();
  const searchParams = useSearchParams();

  // 内部管理的状态
  const [message, setMessage] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [sendError, setSendError] = useState<string | null>(null);
  
  // 获取URL参数中的客户ID（仅在顾问界面）
  const customerId = searchParams?.get('customerId');
  
  // 检查当前用户是否为顾问
  const isConsultant = user?.currentRole === 'consultant';
  
  // 显示方案生成按钮的条件：是顾问且有会话ID和客户ID
  const showPlanGeneration = isConsultant && conversationId && customerId;

  // 录音相关状态
  const {
    isRecording,
    isPaused,
    recordingTime,
    startRecording,
    stopRecording,
    pauseRecording,
    resumeRecording,
    cancelRecording
  } = useRecording();

  // 媒体上传相关状态
  const {
    imagePreview,
    fileInputRef,
    handleImageUpload,
    cancelImagePreview,
    triggerFileSelect,
    audioPreview,
    setAudioPreview,
    cancelAudioPreview,
    // 文件相关
    filePreview,
    fileInputForFileRef,
    handleFileUpload: handleFileInputChange,
    cancelFilePreview,
    triggerFileUpload,
    getTempFile
  } = useMediaUpload();

  // 处理消息发送
  const handleSendMessage = useCallback(async () => {
    const flatMessage = message.trim();
    
    // 检查是否有内容可发送（文字、图片、文件或语音）
    if (!flatMessage && !imagePreview && !filePreview && !audioPreview) {
      return;
    }

    setIsSending(true);
    setSendError(null);

    try {
      // 如果有图片预览，发送图片消息（可能包含文字）
      if (imagePreview) {
        await sendImageMessage(imagePreview, flatMessage || undefined);
        
        // 清理状态
        setMessage('');
        cancelImagePreview();
      }
      // 如果有文件预览，发送文件消息
      else if (filePreview) {
        await sendFileMessage(filePreview, flatMessage || undefined);
        
        // 清理状态
        setMessage('');
        cancelFilePreview();
      }
      // 如果有语音预览，发送语音消息
      else if (audioPreview) {
        await sendAudioMessage(audioPreview, flatMessage || undefined);
        
        // 清理状态
        setMessage('');
        cancelAudioPreview();
      }
      // 如果只有文字，发送文字消息
      else if (flatMessage) {
        await sendTextMessage(flatMessage);

        // 清理状态
        setMessage('');
      }
    } catch (error) {
      console.error('发送消息失败:', error);
      setSendError(error instanceof Error ? error.message : '发送失败');
    } finally {
      setIsSending(false);
    }
  }, [message, imagePreview, filePreview, audioPreview, conversationId, onSendMessage, cancelImagePreview, cancelFilePreview, cancelAudioPreview]);

  
  
  /**
   * 发送文字消息
   */
  const sendTextMessage = async (content: string) => {
    try {
      const currentUser = authService.getCurrentUser();
      if (!currentUser) {
        throw new ApiClientError('用户未登录', {
          status: 401,
          type: ErrorType.AUTHENTICATION,
        })
      }
      
      const userRole = currentUser.currentRole || 'customer';
      const localId = `local_${uuidv4()}`;
      const now = new Date().toISOString();
      
      // 创建文本消息内容
      const textContent: TextMessageContent = {
        text: content
      };
      
      // 创建用户消息（pending状态）
      const textMessage: Message = {
        id: localId, // 使用临时ID，保存后会更新为服务器ID
        localId, // 本地标识
        conversationId: conversationId || '',
        content: textContent,
        type: 'text',
        sender: {
          id: currentUser.id,
          type: userRole,
          name: currentUser.name,
          avatar: currentUser.avatar || '/avatars/user.png',
        },
        timestamp: now,
        createdAt: now,
        // 消息状态相关字段
        status: 'pending',
        canRetry: true, // 失败后可重试
        canDelete: true, // 可以删除
        canRecall: false, // 初始时不可撤销，发送成功后1分钟内可撤销
      };
      
      await onSendMessage(textMessage);
    } catch (error) {
      console.error('发送文本消息失败:', error);
      throw error;
    }
  }

  // 发送图片消息
  const sendImageMessage = async (imageUrl: string, text?: string) => {
    try {
      // 从 blob URL 获取文件数据
      const urlToFile = async (objectUrl: string, filename: string): Promise<File> => {
        const response = await fetch(objectUrl);
        const blob = await response.blob();
        
        // 获取实际的 MIME 类型
        const mimeType = blob.type || 'image/png';
        
        return new File([blob], filename, { type: mimeType });
      };

      // 先创建pending消息，用户能立即看到
      const localId = `local_${Date.now()}`;
      const pendingMessage: Message = {
        id: localId,
        localId,
        conversationId: conversationId,
        content: {
          text: text,
          media_info: {
            url: imageUrl, // 临时使用blob URL，上传后会更新
            name: '上传中...',
            mime_type: 'image/png',
            size_bytes: 0,
          }
        },
        type: 'media',
        sender: {
          id: user?.id || '',
          type: 'user',
          name: user?.name || '',
          avatar: user?.avatar || '',
        },
        timestamp: new Date().toISOString(),
        status: 'pending'
      };

      // 立即添加到本地状态，用户能立即看到
      // 注意：这里添加pending消息，但handleSendMessage会尝试保存
      // 我们需要标记这个消息是媒体消息，稍后会手动保存
      if (onMessageAdded) {
        onMessageAdded(pendingMessage);
      } else {
        await onSendMessage(pendingMessage);
      }

      // 创建文件对象
      const timestamp = Date.now();
      const filename = `image_${timestamp}.png`;
      const file = await urlToFile(imageUrl, filename);
      
      // 上传文件（不创建消息）
      const formData = new FormData();
      formData.append('file', file);
      formData.append('conversation_id', conversationId);
      // 注意：不再传递text参数，因为文件上传API不再创建消息

      const { data: result } = await apiClient.upload<any>('/files/upload', formData);

      if (!result.success) {
        // 上传失败，更新消息状态为failed
        const failedMessage: Message = {
          ...pendingMessage,
          status: 'failed',
          error: result.message || '图片上传失败'
        };
        if (onMessageAdded) {
          onMessageAdded(failedMessage);
        }
        throw new Error(result.message || '图片上传失败');
      }
      
      const fileInfo = result.file_info;
      if (!fileInfo) {
        throw new Error('服务器返回的文件信息为空');
      }

      // 更新消息内容，使用上传后的文件路径
      const mediaMessage: Message = {
        ...pendingMessage,
        content: {
          text: text,
          media_info: {
            url: fileInfo.file_url,
            name: fileInfo.file_name,
            mime_type: fileInfo.mime_type,
            size_bytes: fileInfo.file_size,
          }
        },
        status: 'pending' // 保持pending状态，等待发送
      };

      // 调用媒体消息API发送消息
      const savedMessage = await saveMessage(mediaMessage);
      
      // 更新消息状态为sent，替换pending消息
      const finalMessage: Message = {
        ...savedMessage,
        localId: pendingMessage.localId,
        status: 'sent'
      };
      
      // 更新本地消息（替换pending消息）
      if (onMessageAdded) {
        onMessageAdded(finalMessage);
      }
      
      // 清理 blob URL 以释放内存
      URL.revokeObjectURL(imageUrl);
    } catch (error) {
      console.error('发送图片消息失败:', error);
      throw error;
    }
  };

  // 发送文件消息
  const sendFileMessage = async (fileInfo: FileInfo, text?: string) => {
    let previewUrl: string | null = null; // 用于存储临时创建的blob URL
    
    try {
      // 获取原始文件对象
      const originalFile = getTempFile(fileInfo.file_url);
      if (!originalFile) {
        throw new Error('文件已丢失，请重新选择');
      }

      // 对于图片文件，创建blob URL用于预览
      if (fileInfo.file_type === 'image' && fileInfo.file_url.startsWith('temp_')) {
        previewUrl = URL.createObjectURL(originalFile);
      }

      // 先创建pending消息，用户能立即看到
      const localId = `local_${Date.now()}`;
      const pendingMessage: Message = {
        id: localId,
        localId,
        conversationId: conversationId,
        content: {
          text: text,
          media_info: {
            url: previewUrl || fileInfo.file_url, // 使用blob URL（图片）或临时ID（其他文件）
            name: fileInfo.file_name || '上传中...',
            mime_type: fileInfo.mime_type || 'application/octet-stream',
            size_bytes: fileInfo.file_size || 0,
          }
        },
        type: 'media',
        sender: {
          id: user?.id || '',
          type: 'user',
          name: user?.name || '',
          avatar: user?.avatar || '',
        },
        timestamp: new Date().toISOString(),
        status: 'pending'
      };

      // 立即添加到本地状态，用户能立即看到
      if (onMessageAdded) {
        onMessageAdded(pendingMessage);
      } else {
        await onSendMessage(pendingMessage);
      }

      // 上传文件（不创建消息）
      const formData = new FormData();
      formData.append('file', originalFile);
      formData.append('conversation_id', conversationId);
      // 注意：不再传递text参数，因为文件上传API不再创建消息

      const { data: result } = await apiClient.upload<any>('/files/upload', formData);

      if (!result.success) {
        // 上传失败，更新消息状态为failed
        const failedMessage: Message = {
          ...pendingMessage,
          status: 'failed',
          error: result.message || '文件上传失败'
        };
        if (onMessageAdded) {
          onMessageAdded(failedMessage);
        }
        throw new Error(result.message || '文件上传失败');
      }

      const uploadedFileInfo = result.file_info;
      if (!uploadedFileInfo) {
        throw new Error('服务器返回的文件信息为空');
      }
      
      // 更新消息内容，使用上传后的文件路径
      const mediaMessage: Message = {
        ...pendingMessage,
        content: {
          text: text,
          media_info: {
            url: uploadedFileInfo.file_url,
            name: uploadedFileInfo.file_name,
            mime_type: uploadedFileInfo.mime_type,
            size_bytes: uploadedFileInfo.file_size,
          }
        },
        status: 'pending' // 保持pending状态，等待发送
      };

      // 调用媒体消息API发送消息
      const savedMessage = await saveMessage(mediaMessage);
      
      // 更新消息状态为sent，替换pending消息
      const finalMessage: Message = {
        ...savedMessage,
        localId: pendingMessage.localId,
        status: 'sent'
      };
      
      // 更新本地消息（替换pending消息）
      if (onMessageAdded) {
        onMessageAdded(finalMessage);
      }

      // 清理之前创建的blob URL（如果是图片文件）
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    } catch (error) {
      console.error('发送文件消息失败:', error);
      // 出错时也要清理blob URL
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
      throw error;
    }
  };

  // 发送语音消息
  const sendAudioMessage = async (audioUrl: string, text?: string) => {
    try {
      // 先创建pending消息，用户能立即看到
      const localId = `local_${Date.now()}`;
      const pendingMessage: Message = {
        id: localId,
        localId,
        conversationId: conversationId,
        content: {
          text: text,
          media_info: {
            url: audioUrl, // 临时使用blob URL
            name: '上传中...',
            mime_type: 'audio/webm',
            size_bytes: 0,
          }
        },
        type: 'media',
        sender: {
          id: user?.id || '',
          type: 'user',
          name: user?.name || '',
          avatar: user?.avatar || '',
        },
        timestamp: new Date().toISOString(),
        status: 'pending'
      };

      // 立即添加到本地状态，用户能立即看到
      if (onMessageAdded) {
        onMessageAdded(pendingMessage);
      } else {
        await onSendMessage(pendingMessage);
      }

      // 从 Object URL 获取 Blob 数据
      const urlToFile = async (objectUrl: string, filename: string): Promise<File> => {
        const response = await fetch(objectUrl);
        const blob = await response.blob();
        
        // 获取实际的 MIME 类型
        const mimeType = blob.type || 'audio/webm';
        
        return new File([blob], filename, { type: mimeType });
      };

      // 创建文件对象
      const timestamp = Date.now();
      const filename = `voice_${timestamp}.webm`;
      const file = await urlToFile(audioUrl, filename);
      
      // 上传文件（不创建消息）
      const formData = new FormData();
      formData.append('file', file);
      formData.append('conversation_id', conversationId);
      // 注意：不再传递text参数，因为文件上传API不再创建消息

      const { data: result } = await apiClient.upload<any>('/files/upload', formData);

      if (!result.success) {
        // 上传失败，更新消息状态为failed
        const failedMessage: Message = {
          ...pendingMessage,
          status: 'failed',
          error: result.message || '语音上传失败'
        };
        if (onMessageAdded) {
          onMessageAdded(failedMessage);
        }
        throw new Error(result.message || '语音上传失败');
      }

      const fileInfo = result.file_info;
      if (!fileInfo) {
        throw new Error('服务器返回的文件信息为空');
      }
      
      // 更新消息内容，使用上传后的文件路径
      const mediaMessage: Message = {
        ...pendingMessage,
        content: {
          text: text,
          media_info: {
            url: fileInfo.file_url,
            name: fileInfo.file_name,
            mime_type: fileInfo.mime_type,
            size_bytes: fileInfo.file_size,
          }
        },
        status: 'pending' // 保持pending状态，等待发送
      };

      // 调用媒体消息API发送消息
      const savedMessage = await saveMessage(mediaMessage);
      
      // 更新消息状态为sent，替换pending消息
      const finalMessage: Message = {
        ...savedMessage,
        localId: pendingMessage.localId,
        status: 'sent'
      };
      
      // 更新本地消息（替换pending消息）
      if (onMessageAdded) {
        onMessageAdded(finalMessage);
      }
      
      // 清理 Object URL 以释放内存
      URL.revokeObjectURL(audioUrl);
    } catch (error) {
      console.error('发送语音消息失败:', error);
      throw error;
    }
  };

  // 处理键盘事件
  const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!isSending && (message.trim() || imagePreview || filePreview || audioPreview)) {
        handleSendMessage();
      }
    }
  }, [handleSendMessage, isSending, message, imagePreview, filePreview, audioPreview]);

  // 处理开始录音
  const handleStartRecording = useCallback(async () => {
    try {
      cancelAudioPreview(); // 清除之前的音频预览
      await startRecording();
    } catch (error) {
      console.error('开始录音失败:', error);
    }
  }, [startRecording, cancelAudioPreview]);

  // 处理停止录音
  const handleStopRecording = useCallback(async () => {
    try {
      const audioUrl = await stopRecording();
      if (audioUrl) {
        setAudioPreview(audioUrl);
      }
    } catch (error) {
      console.error('停止录音失败:', error);
    }
  }, [stopRecording, setAudioPreview]);

  // FAQ选择处理 - 填入输入框而不是直接发送
  const handleFAQSelect = useCallback((faqMessage: string) => {
    setMessage(faqMessage);
    // 聚焦到输入框
    setTimeout(() => {
      const input = document.querySelector('input[placeholder="输入消息..."]') as HTMLInputElement;
      if (input) {
        input.focus();
      }
    }, 100);
  }, []);

  // 获取FAQ组件的按钮和面板
  const faqSection = FAQSection({
    onSelectFAQ: handleFAQSelect,
    messages: messages.map(msg => ({
      content: MessageUtils.getTextContent(msg) || ''
    }))
  });

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

      {/* 录音状态显示 */}
      <RecordingControls
        isRecording={isRecording}
        isPaused={isPaused}
        recordingTime={recordingTime}
        onStopRecording={handleStopRecording}
        onCancelRecording={cancelRecording}
        onPauseRecording={pauseRecording}
        onResumeRecording={resumeRecording}
        maxDuration={300}
      />
      
      {/* 媒体预览 */}
      <MediaPreview
        conversationId={conversationId}
        imagePreview={imagePreview}
        audioPreview={audioPreview}
        filePreview={filePreview}
        onCancelImage={cancelImagePreview}
        onCancelAudio={cancelAudioPreview}
        onCancelFile={cancelFilePreview}
      />
      
      {/* FAQ面板 - 在输入区域上方显示 */}
      {faqSection.panel}
      
      {/* 隐藏的文件输入 */}
      <input
        type="file"
        ref={fileInputRef}
        className="hidden"
        accept="image/*"
        onChange={handleImageUpload}
      />
      
      {/* 隐藏的文件输入（用于普通文件） */}
      <input
        type="file"
        ref={fileInputForFileRef}
        className="hidden"
        accept="*/*"
        onChange={handleFileInputChange}
      />
      
      {/* 输入区域 */}
      <div className="border-t border-gray-200 bg-white">
        {/* 功能按钮区域 */}
        <div className="flex items-center justify-between px-4 py-2 border-b border-gray-100">
          <div className="flex items-center space-x-3">
            {/* FAQ按钮 */}
            {faqSection.button}
            
            {/* 顾问接管按钮 */}
            <ConsultantTakeover conversationId={conversationId} className="p-1.5 rounded-md transition-colors" />

            <button 
                className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-md transition-colors"
                title="表情"
            >
              <Smile className="h-5 w-5" />
            </button>
            
            <button 
              className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-md transition-colors"
              title="图片"
              onClick={triggerFileSelect}
            >
              <Image className="h-5 w-5" />
            </button>
            
            <button 
              className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-md transition-colors"
              title="文件"
              onClick={triggerFileUpload}
            >
              <Paperclip className="h-5 w-5" />
            </button>
            
            <button 
              className={`p-2 rounded-md transition-colors ${
                isRecording 
                  ? 'text-red-500 bg-red-50' 
                  : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
              }`}
              title="语音"
              onClick={isRecording ? handleStopRecording : handleStartRecording}
            >
              <Mic className="h-5 w-5" />
            </button>
            
            {/* AI方案生成按钮 - 仅对顾问显示 */}
            {showPlanGeneration && (
              <PlanGenerationButton
                conversationId={conversationId}
                customerId={customerId}
                consultantId={user?.id || ''}
                onPlanGenerated={(plan) => {
                  console.log('方案生成完成:', plan);
                  if (onUpdateMessages) {
                    onUpdateMessages();
                  }
                }}
              />
            )}
          </div>
        </div>

        {/* 输入框区域 */}
        <div className="p-4">
          {/* 输入框 */}
          <div className="flex-1 relative">
              <Textarea
                value={message}
                onChange={e => setMessage(e.target.value)}
                onKeyDown={handleKeyDown}
                onFocus={onInputFocus} // 添加聚焦事件处理
                placeholder="输入消息... (Shift + Enter 换行)"
                className="min-h-[40px] max-h-[120px] pr-12 border-gray-200 focus:border-orange-500 focus:ring-orange-500/20"
                autoResize
                maxRows={5}
                minRows={1}
                disabled={isSending || isRecording}
              />
              
              {/* 发送按钮 */}
              <Button
                onClick={handleSendMessage}
                disabled={isSending || (!message.trim() && !imagePreview && !audioPreview && !filePreview)}
                size="sm"
                className={`absolute right-2 bottom-2 h-8 w-8 p-0 bg-orange-500 hover:bg-orange-600 text-white border-0 shadow-sm transition-all ${
                  isSending || (!message.trim() && !imagePreview && !audioPreview && !filePreview)
                    ? 'opacity-50 cursor-not-allowed' 
                    : 'hover:scale-105'
                }`}
              >
                {isSending ? (
                  <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                ) : (
                  <Send className="h-4 w-4" />
                )}
              </Button>
            </div>
        </div>
      </div>
    </>
  );
} 