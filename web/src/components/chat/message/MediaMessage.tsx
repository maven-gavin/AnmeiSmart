'use client';

import React from 'react';
import type { MessageContentProps } from './ChatMessage';
import { MediaMessageContent } from '@/types/chat';
import ImageMessage from './ImageMessage';
import FileMessage from './FileMessage';
import VideoMessage from './VideoMessage';
import VoiceMessage from './VoiceMessage';

export default function MediaMessage({ message, searchTerm, compact, onRetry }: MessageContentProps) {
  // 确保是媒体消息
  if (message.type !== 'media') {
    return <div className="text-red-500">错误：非媒体消息类型</div>;
  }

  const content = message.content as MediaMessageContent;
  
  // 如果没有媒体信息，显示错误
  if (!content.media_info) {
    return <div className="text-gray-500">媒体信息缺失</div>;
  }

  const { mime_type } = content.media_info;

  // 根据MIME类型选择合适的组件
  if (mime_type.startsWith('image/')) {
    return <ImageMessage message={message} searchTerm={searchTerm} compact={compact} onRetry={onRetry} />;
  }
  
  if (mime_type.startsWith('video/')) {
    return <VideoMessage message={message} searchTerm={searchTerm} compact={compact} onRetry={onRetry} />;
  }
  
  if (mime_type.startsWith('audio/')) {
    return <VoiceMessage message={message} searchTerm={searchTerm} compact={compact} onRetry={onRetry} />;
  }

  // 其他文件类型使用通用文件组件
  return <FileMessage message={message} searchTerm={searchTerm} compact={compact} onRetry={onRetry} />;
} 