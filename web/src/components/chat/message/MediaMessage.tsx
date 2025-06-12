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

  // 渲染媒体内容组件
  const renderMediaComponent = () => {
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
  };

  // 高亮搜索文本的函数
  const highlightText = (text: string, searchTerm?: string) => {
    if (!searchTerm) return text;
    
    const regex = new RegExp(`(${searchTerm})`, 'gi');
    const parts = text.split(regex);
    
    return parts.map((part, index) => {
      if (part.toLowerCase() === searchTerm.toLowerCase()) {
        return (
          <span key={index} className="bg-yellow-200">
            {part}
          </span>
        );
      }
      return part;
    });
  };

  return (
    <div className="space-y-2">
      {/* 媒体内容 */}
      {renderMediaComponent()}
      
      {/* 文字内容（如果存在） */}
      {content.text && content.text.trim() && (
        <div className="text-gray-900 text-sm leading-relaxed break-words">
          {highlightText(content.text.trim(), searchTerm)}
        </div>
      )}
    </div>
  );
} 