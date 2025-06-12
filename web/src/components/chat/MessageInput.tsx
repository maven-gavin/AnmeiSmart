'use client';

import React, { useCallback, useState } from 'react';
import { Button } from '@/components/ui/button';
import { RecordingControls } from '@/components/chat/RecordingControls';
import { MediaPreview } from '@/components/chat/MediaPreview';
import FAQSection from '@/components/chat/FAQSection';
import ConsultantTakeover from '@/components/chat/ConsultantTakeover';
import { useRecording } from '@/hooks/useRecording';
import { useMediaUpload } from '@/hooks/useMediaUpload';
import { type Message, type FileInfo, type MediaMessageContent, type TextMessageContent } from '@/types/chat';
import { v4 as uuidv4 } from 'uuid';
import { authService } from "@/service/authService";
import { AppError, ErrorType } from '@/service/errors';
import FileSelector from './FileSelector';
import { MessageUtils } from '@/utils/messageUtils';
import { FileService } from '@/service/fileService';
import { saveMessage } from '@/service/chatService';

interface MessageInputProps {
  conversationId?: string | null;
  onSendMessage: (message: Message) => Promise<void>;
  toggleSearch: () => void;
  showSearch: boolean;
  onUpdateMessages?: () => void;
  messages?: Message[]; // 传递给FAQ使用
}

/**
 * 发送文字消息
 */
function createTextMessage(content: string, conversationId: string): Message {
  const currentUser = authService.getCurrentUser();
  if (!currentUser) {
    throw new AppError(ErrorType.AUTHENTICATION, 401, '用户未登录');
  }
  
  const userRole = currentUser.currentRole || 'customer';
  const localId = `local_${uuidv4()}`;
  const now = new Date().toISOString();
  
  // 创建文本消息内容
  const textContent: TextMessageContent = {
    text: content
  };
  
  // 创建用户消息（pending状态）
  const userMessage: Message = {
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
  
  return userMessage;
}

/**
 * 发送图片消息（支持附带文字）
 */
function createImageMessage(imageUrl: string, text: string | undefined, conversationId: string): Message {
  const currentUser = authService.getCurrentUser();
  if (!currentUser) {
    throw new AppError(ErrorType.AUTHENTICATION, 401, '用户未登录');
  }
  
  const localId = `local_${uuidv4()}`;
  const now = new Date().toISOString();
  
  // 创建媒体消息内容（图片）
  const mediaContent: MediaMessageContent = {
    media_info: {
      url: imageUrl,
      name: `image_${Date.now()}.png`,
      size_bytes: 0, // 临时值，实际值需要从服务器获取
      mime_type: 'image/png',
      metadata: {
        file_type: 'image'
      }
    },
    text: text && text.trim() ? text.trim() : undefined
  };
  
  // 创建图片消息（pending状态）
  const imageMessage: Message = {
    id: localId,
    localId,
    conversationId: conversationId || '',
    content: mediaContent,
    type: 'media',
    sender: {
      id: currentUser.id,
      type: currentUser.currentRole || 'customer',
      name: currentUser.name,
      avatar: currentUser.avatar || '/avatars/user.png',
    },
    timestamp: now,
    createdAt: now,
    status: 'pending',
    canRetry: true,
    canDelete: true,
    canRecall: false,
  };
  
  return imageMessage;
}





export default function MessageInput({
  conversationId,
  onSendMessage,
  toggleSearch,
  showSearch,
  onUpdateMessages,
  messages = []
}: MessageInputProps) {

  // 内部管理的状态
  const [message, setMessage] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [sendError, setSendError] = useState<string | null>(null);

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
    const trimmedMessage = message.trim();
    
    // 检查是否有内容可发送（文字、图片、文件或语音）
    if (!trimmedMessage && !imagePreview && !filePreview && !audioPreview) {
      return;
    }

    setIsSending(true);
    setSendError(null);

    try {
      // 如果有图片预览，优先发送图片消息（可能包含文字）
      if (imagePreview) {
        const imageMessage = await createImageMessage(imagePreview, trimmedMessage || undefined, conversationId || '');
        await onSendMessage(imageMessage);
        
        // 清理状态
        setMessage('');
        cancelImagePreview();
      }
      // 如果有文件预览，发送文件消息
      else if (filePreview) {
        await sendFileMessage(filePreview, trimmedMessage || undefined);
        
        // 清理状态
        setMessage('');
        cancelFilePreview();
      }
      // 如果有语音预览，发送语音消息
      else if (audioPreview) {
        await sendAudioMessage(audioPreview, trimmedMessage || undefined);
        
        // 清理状态
        setMessage('');
        cancelAudioPreview();
      }
      // 如果只有文字，发送文字消息
      else if (trimmedMessage) {
        const textMessage = createTextMessage(trimmedMessage, conversationId || '');
        await onSendMessage(textMessage);
        
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

  // 发送文件消息
  const sendFileMessage = useCallback(async (fileInfo: FileInfo, text?: string) => {
    try {
      // 获取原始文件对象
      const originalFile = getTempFile(fileInfo.file_url);
      if (!originalFile) {
        throw new Error('文件已丢失，请重新选择');
      }

      // 上传文件到服务器
      const fileService = new FileService();
      const uploadedFileInfo = await fileService.uploadFile(originalFile, conversationId || '');
      
      // 创建媒体消息内容
      const mediaContent: MediaMessageContent = {
        media_info: {
          url: uploadedFileInfo.file_url,
          name: uploadedFileInfo.file_name,
          size_bytes: uploadedFileInfo.file_size,
          mime_type: uploadedFileInfo.mime_type,
          metadata: {
            file_type: uploadedFileInfo.file_type,
            object_name: uploadedFileInfo.object_name
          }
        },
        text: text // 可能包含文字
      };

      const currentUser = authService.getCurrentUser();
      if (!currentUser) {
        throw new AppError(ErrorType.AUTHENTICATION, 401, '用户未登录');
      }

      const localId = `local_${uuidv4()}`;
      const now = new Date().toISOString();

      // 创建文件消息
      const fileMessage: Message = {
        id: localId,
        localId,
        conversationId: conversationId || '',
        content: mediaContent,
        type: 'media',
        sender: {
          id: currentUser.id,
          type: currentUser.currentRole || 'customer',
          name: currentUser.name,
          avatar: currentUser.avatar || '/avatars/user.png',
        },
        timestamp: now,
        createdAt: now,
        status: 'pending',
        canRetry: true,
        canDelete: true,
        canRecall: false,
      };

      // 发送消息
      await onSendMessage(fileMessage);
      
    } catch (error) {
      console.error('发送文件消息失败:', error);
      throw error;
    }
  }, [getTempFile, conversationId, onSendMessage]);

  // 发送语音消息
  const sendAudioMessage = useCallback(async (audioUrl: string, text?: string) => {
    try {
      // 从 Object URL 获取 Blob 数据
      const urlToFile = async (objectUrl: string, filename: string): Promise<File> => {
        const response = await fetch(objectUrl);
        const blob = await response.blob();
        
        // 获取实际的 MIME 类型
        const mimeType = blob.type || 'audio/webm';
        
        return new File([blob], filename, { type: mimeType });
      };

      // 上传语音文件到服务器
      const timestamp = Date.now();
      const filename = `voice_${timestamp}.webm`;
      const file = await urlToFile(audioUrl, filename);
      
      console.log('准备上传语音文件:', {
        name: file.name,
        type: file.type,
        size: file.size
      });
      
      const fileService = new FileService();
      const uploadedFileInfo = await fileService.uploadFile(file, conversationId || '');
      
      // 创建媒体消息内容
      const mediaContent: MediaMessageContent = {
        media_info: {
          url: uploadedFileInfo.file_url,
          name: uploadedFileInfo.file_name,
          size_bytes: uploadedFileInfo.file_size,
          mime_type: uploadedFileInfo.mime_type,
          metadata: {
            file_type: uploadedFileInfo.file_type,
            object_name: uploadedFileInfo.object_name
          }
        },
        text: text // 可能包含文字
      };

      console.log('创建语音消息内容:', {
        textParam: text,
        textType: typeof text,
        textValue: JSON.stringify(text),
        mediaContent: mediaContent
      });

      const currentUser = authService.getCurrentUser();
      if (!currentUser) {
        throw new AppError(ErrorType.AUTHENTICATION, 401, '用户未登录');
      }

      const localId = `local_${uuidv4()}`;
      const now = new Date().toISOString();

      // 创建语音消息
      const audioMessage: Message = {
        id: localId,
        localId,
        conversationId: conversationId || '',
        content: mediaContent,
        type: 'media',
        sender: {
          id: currentUser.id,
          type: currentUser.currentRole || 'customer',
          name: currentUser.name,
          avatar: currentUser.avatar || '/avatars/user.png',
        },
        timestamp: now,
        createdAt: now,
        status: 'pending',
        canRetry: true,
        canDelete: true,
        canRecall: false,
      };

      // 发送消息
      await onSendMessage(audioMessage);
      
      // 清理 Object URL 以释放内存
      URL.revokeObjectURL(audioUrl);
      
    } catch (error) {
      console.error('发送语音消息失败:', error);
      throw error;
    }
  }, [conversationId, onSendMessage]);

  // 处理键盘事件
  const handleKeyPress = useCallback((e: React.KeyboardEvent<HTMLInputElement>) => {
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
      
      {/* 文件选择器 */}

      
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
      <div className="border-t border-gray-200 bg-white p-4">
        <div className="flex space-x-4">
          {/* FAQ按钮 */}
          {faqSection.button}
          
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
          
          {/* 顾问接管按钮 - 使用专门的组件 */}
          <ConsultantTakeover conversationId={conversationId} />
                    
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
                d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 002 2z"
              />
            </svg>
          </button>
          
          <button 
            className="flex-shrink-0 text-gray-500 hover:text-gray-700"
            title="文件"
            onClick={triggerFileUpload}
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
                d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"
              />
            </svg>
          </button>
          
          <button 
            className={`flex-shrink-0 ${isRecording ? 'text-red-500' : 'text-gray-500 hover:text-gray-700'}`}
            title="语音"
            onClick={isRecording ? handleStopRecording : handleStartRecording}
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
              disabled={isSending || isRecording}
              onKeyPress={handleKeyPress}
            />
            <Button
              onClick={handleSendMessage}
              disabled={isSending || (!message.trim() && !imagePreview && !audioPreview && !filePreview)}
              className={`bg-orange-500 hover:bg-orange-600 text-white border-0 shadow-sm transition-colors ${
                isSending ? 'opacity-70 cursor-not-allowed' : ''
              }`}
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