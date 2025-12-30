'use client';

import React from 'react';
import { Message, TextMessageContent } from '@/types/chat';
import { escapeRegExp } from '@/utils/regex';

interface TextMessageProps {
  message: Message;
  searchTerm?: string;
}

const TextMessage: React.FC<TextMessageProps> = ({ message, searchTerm }) => {
  const content = message.content as TextMessageContent;
  const text = content.text || '';

  // 高亮搜索关键词
  const highlightText = (text: string, searchTerm?: string) => {
    if (!searchTerm || !text) return text;
    
    const escaped = escapeRegExp(searchTerm);
    const regex = new RegExp(`(${escaped})`, 'gi');
    const parts = text.split(regex);
    
    return parts.map((part, index) => 
      part.toLowerCase() === searchTerm.toLowerCase() ? (
        <mark key={index} className="bg-yellow-200 px-1 rounded">
          {part}
        </mark>
      ) : part
    );
  };

  return (
    <div className="text-message">
      <div className="whitespace-pre-wrap break-words">
        {highlightText(text, searchTerm)}
      </div>
    </div>
  );
};

export default TextMessage; 