'use client';

import React from 'react';
import type { MessageContentProps } from './ChatMessage';
import { MediaMessageContent } from '@/types/chat';
import ImageMessage from './ImageMessage';
import FileMessage from './FileMessage';
import VideoMessage from './VideoMessage';
import VoiceMessage from './VoiceMessage';
import { escapeRegExp } from '@/utils/regex';

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

  const { mime_type, name } = content.media_info;

  // 从文件名中提取文件扩展名
  const getFileExtension = (urlOrName: string): string => {
    const match = urlOrName.match(/\.([a-zA-Z0-9]+)(?:\?|$)/);
    return match ? match[1].toLowerCase() : '';
  };

  // 判断是否为PDF文件
  const isPdfFile = (): boolean => {
    const extension = getFileExtension(name || '');
    return extension === 'pdf' || mime_type === 'application/pdf';
  };

  // 判断是否为图片文件（排除PDF）
  const isImageFile = (): boolean => {
    if (isPdfFile()) return false;
    return mime_type.startsWith('image/') || 
           ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'bmp'].includes(getFileExtension(name || ''));
  };

  // 判断是否为视频文件（排除音频）
  const isVideoFile = (): boolean => {
    // 优先检查mime_type，如果明确是audio/开头，不是视频
    if (mime_type.startsWith('audio/')) return false;
    return mime_type.startsWith('video/') || 
           ['mp4', 'avi', 'mov', 'mkv'].includes(getFileExtension(name || ''));
  };

  // 判断是否为音频文件
  const isAudioFile = (): boolean => {
    return mime_type.startsWith('audio/') || 
           ['mp3', 'wav', 'ogg', 'aac', 'webm'].includes(getFileExtension(name || ''));
  };

  // 渲染媒体内容组件
  const renderMediaComponent = () => {
    if (isImageFile()) {
      return <ImageMessage message={message} searchTerm={searchTerm} compact={compact} onRetry={onRetry} />;
    }
    
    // 先检查音频，避免audio/webm被误识别为视频
    if (isAudioFile()) {
      return <VoiceMessage message={message} searchTerm={searchTerm} compact={compact} onRetry={onRetry} />;
    }
    
    if (isVideoFile()) {
      return <VideoMessage message={message} searchTerm={searchTerm} compact={compact} onRetry={onRetry} />;
    }

    // PDF和其他文件类型使用通用文件组件
    return <FileMessage message={message} searchTerm={searchTerm} compact={compact} onRetry={onRetry} />;
  };

  // 高亮搜索文本的函数
  const highlightText = (text: string, searchTerm?: string) => {
    if (!searchTerm) return text;
    
    const escaped = escapeRegExp(searchTerm);
    const regex = new RegExp(`(${escaped})`, 'gi');
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
    </div>
  );
} 