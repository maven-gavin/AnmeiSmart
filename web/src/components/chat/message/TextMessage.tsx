'use client';

import React from 'react';
import { MessageContentProps } from './ChatMessage';

export default function TextMessage({ message, searchTerm, compact }: MessageContentProps) {
  // 高亮搜索文本
  const highlightText = (text: string, searchTerm: string) => {
    if (!searchTerm.trim() || !text) return text;
    
    const parts = text.split(new RegExp(`(${searchTerm})`, 'gi'));
    
    return (
      <>
        {parts.map((part, index) => 
          part.toLowerCase() === searchTerm.toLowerCase() 
            ? <span key={index} className="bg-yellow-200 text-gray-900">{part}</span> 
            : part
        )}
      </>
    );
  };

  return (
    <p className="break-words whitespace-pre-line">
      {searchTerm?.trim() && typeof message.content === 'string'
        ? highlightText(message.content, searchTerm)
        : message.content}
    </p>
  );
} 