'use client';

import { type Message } from '@/types/chat';
import { useState } from 'react';

export interface ChatMessageProps {
  message: Message;
  isSelected?: boolean;
  searchTerm?: string;
  onToggleImportant?: (messageId: string, currentStatus: boolean) => void;
  showSender?: boolean;
  compact?: boolean;
}

export default function ChatMessage({
  message,
  isSelected = false,
  searchTerm = '',
  onToggleImportant,
  showSender = true,
  compact = false
}: ChatMessageProps) {
  const [imageExpanded, setImageExpanded] = useState(false);
  
  // 消息发送者信息
  const avatar = message.sender?.avatar || '/avatars/default.png';
  const name = message.sender?.name || '未知用户';
  const isCustomerMessage = message.sender.type === 'customer' || message.sender.type === 'user';
  
  // 系统消息单独处理
  if (message.isSystemMessage) {
    return (
      <div className="flex justify-center my-3">
        <div className="text-center py-1 px-3 bg-gray-100 rounded-full text-xs text-gray-500 max-w-[80%]">
          {message.content}
        </div>
      </div>
    );
  }
  
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
  
  // 渲染消息内容
  const renderMessageContent = () => {
    // 图片消息展示
    if (message.type === 'image' && typeof message.content === 'string') {
      return (
        <div className={`${imageExpanded ? 'max-w-full' : 'max-w-[300px]'}`}>
          <img 
            src={message.content} 
            alt="聊天图片" 
            className={`max-h-60 rounded-md cursor-pointer ${imageExpanded ? 'w-full' : 'max-w-full'}`}
            onClick={() => setImageExpanded(!imageExpanded)}
          />
          <div className="mt-1 text-xs text-gray-500 text-center">
            {imageExpanded ? '点击缩小' : '点击放大'}
          </div>
        </div>
      );
    // 语音消息展示  
    } else if (message.type === 'voice' && typeof message.content === 'string') {
      return (
        <div className="flex items-center space-x-2">
          <audio src={message.content} controls className="max-w-full" controlsList="nodownload" />
          <span className="text-xs opacity-70">语音消息</span>
        </div>
      );
    }
    
    // 文本消息处理，支持高亮搜索词
    return (
      <p className="break-words whitespace-pre-line">
        {searchTerm.trim() && typeof message.content === 'string'
          ? highlightText(message.content, searchTerm)
          : message.content}
      </p>
    );
  };
  
  return (
    <div
      id={`message-${message.id}`}
      className={`my-4 mx-2 ${
        isSelected ? 'bg-yellow-50 -mx-2 px-2 py-2 rounded-lg' : ''
      }`}
    >
      <div className="flex items-start">
        {/* 头像 */}
        {showSender && (
          <div className="flex-shrink-0 mr-3">
            <img 
              src={avatar} 
              alt={name} 
              className={`rounded-full border-2 border-gray-200 ${compact ? 'h-8 w-8' : 'h-10 w-10'}`}
              onError={(e) => {
                const target = e.target as HTMLImageElement;
                target.onerror = null;
                const nameInitial = name.charAt(0);
                const parentElement = target.parentElement;
                if (parentElement) {
                  setTimeout(() => {
                    parentElement.innerHTML = `<div class="${compact ? 'h-8 w-8' : 'h-10 w-10'} rounded-full flex items-center justify-center text-white text-sm font-bold border-2 border-gray-200" style="background-color: #FF9800">${nameInitial}</div>`;
                  }, 0);
                }
              }}
            />
          </div>
        )}
        
        <div className="flex-1 flex flex-col">
          {/* 发送者名称和时间 */}
          {showSender && (
            <div className="flex items-center mb-1">
              <span className="text-xs font-medium text-gray-700 mr-2">{name}</span>
              <span className="text-xs text-gray-500">
                {new Date(message.timestamp).toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'})}
              </span>
            </div>
          )}
          
          {/* 消息内容卡片 */}
          <div 
            className={`relative rounded-lg p-4 shadow-sm ${
              message.sender.type === 'customer' || message.sender.type === 'user'
                ? 'bg-white border border-gray-200 text-gray-800'
                : message.sender.type === 'ai'
                  ? 'bg-blue-50 border border-blue-100 text-gray-800'
                  : message.sender.type === 'consultant'
                    ? 'bg-orange-50 border border-orange-200 text-gray-800'
                    : 'bg-gray-50 border border-gray-200 text-gray-800'
            } ${compact ? 'p-3' : 'p-4'}`}
          >
            {renderMessageContent()}
            
            {/* 重点标记按钮，仅在有回调函数时显示 */}
            {onToggleImportant && (
              <button
                onClick={() => onToggleImportant(message.id, !!message.isImportant)}
                className={`absolute -right-1.5 -top-1.5 rounded-full p-1 shadow-sm ${
                  message.isImportant ? 'bg-yellow-400 text-white' : 'bg-gray-200 text-gray-500'
                }`}
              >
                <svg className="h-3.5 w-3.5" fill="currentColor" viewBox="0 0 20 20">
                  <path 
                    fillRule="evenodd" 
                    d="M3.172 5.172a4 4 0 015.656 0L10 6.343l1.172-1.171a4 4 0 115.656 5.656L10 17.657l-6.828-6.829a4 4 0 010-5.656z" 
                    clipRule="evenodd" 
                  />
                </svg>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
} 