'use client';

import React from 'react';
import { Message, TextMessageContent } from '@/types/chat';
import { MessageUtils } from '@/utils/messageUtils';

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
    
    const regex = new RegExp(`(${searchTerm})`, 'gi');
    const parts = text.split(regex);
    
    return parts.map((part, index) => 
      regex.test(part) ? (
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