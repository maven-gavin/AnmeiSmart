'use client';

import React, { useState } from 'react';
import { formatDistanceToNow } from 'date-fns';
import { zhCN } from 'date-fns/locale';
import { Message } from '@/types/chat';
import { useAuthContext } from '@/contexts/AuthContext';
import TextMessage from './TextMessage';
import MediaMessage from './MediaMessage';
import SystemMessage from './SystemMessage';
import StructuredMessage from './StructuredMessage';

export interface MessageContentProps {
  message: Message;
  searchTerm?: string;
  compact?: boolean;
  onRetry?: (message: Message) => void;
}

interface ChatMessageProps {
  message: Message;
  isSelected?: boolean;
  searchTerm?: string;
  showAvatar?: boolean;
  showTimestamp?: boolean;
  onReaction?: (messageId: string, emoji: string) => void;
  onReply?: (message: Message) => void;
  onCardAction?: (action: string, data: any) => void;
  onToggleImportant?: (messageId: string) => void;
  onDelete?: (messageId: string) => void;
  onRetry?: (message: Message) => void;
}

const ChatMessage: React.FC<ChatMessageProps> = ({
  message,
  isSelected = false,
  searchTerm = '',
  showAvatar = true,
  showTimestamp = true,
  onReaction,
  onReply,
  onCardAction,
  onToggleImportant,
  onDelete,
  onRetry
}) => {
  const { user } = useAuthContext();
  const [showToolbar, setShowToolbar] = useState(false);
  
  // 计算是否为当前用户发送的消息
  const isOwn = user?.id === message.sender.id;

  const renderMessageContent = () => {
    switch (message.type) {
      case 'text':
        return <TextMessage message={message} searchTerm={searchTerm} />;
      
      case 'media':
        return <MediaMessage message={message} searchTerm={searchTerm} onRetry={onRetry} />;
      
      case 'system':
        return <SystemMessage message={message} />;
      
      case 'structured':
        return (
          <StructuredMessage 
            message={message} 
            onAction={onCardAction}
          />
        );
      
      default:
        return <div className="text-gray-500">不支持的消息类型</div>;
    }
  };

  const renderReactions = () => {
    if (!message.reactions || Object.keys(message.reactions).length === 0) {
      return null;
    }

    return (
      <div className="flex flex-wrap gap-1 mt-2">
        {Object.entries(message.reactions).map(([emoji, userIds]) => (
          <button
            key={emoji}
            className="flex items-center gap-1 px-2 py-1 bg-blue-50 hover:bg-blue-100 
                     rounded-full text-sm border border-blue-200 transition-colors"
            onClick={() => onReaction?.(message.id, emoji)}
          >
            <span>{emoji}</span>
            <span className="text-blue-600">{userIds.length}</span>
          </button>
        ))}
      </div>
    );
  };

  const renderToolbar = () => {
    if (!showToolbar) return null;

    return (
      <div className="absolute top-0 right-0 transform -translate-y-full bg-white border border-gray-200 rounded-lg shadow-lg p-1 flex items-center gap-1 z-10">
        {/* 标记重点 */}
        <button
          className={`p-1 rounded hover:bg-gray-100 ${message.is_important ? 'text-yellow-500' : 'text-gray-400'}`}
          onClick={() => onToggleImportant?.(message.id)}
          title={message.is_important ? '取消重点标记' : '标记为重点'}
        >
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M3.172 5.172a4 4 0 015.656 0L10 6.343l1.172-1.171a4 4 0 115.656 5.656L10 17.657l-6.828-6.829a4 4 0 010-5.656z" clipRule="evenodd" />
          </svg>
        </button>

        {/* 回复 */}
        <button
          className="p-1 rounded hover:bg-gray-100 text-gray-400"
          onClick={() => onReply?.(message)}
          title="回复"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
          </svg>
        </button>

        {/* 表情反应 */}
        <button
          className="p-1 rounded hover:bg-gray-100 text-gray-400"
          onClick={() => onReaction?.(message.id, '👍')}
          title="添加表情"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </button>

        {/* 删除（仅自己的消息或管理员） */}
        {(isOwn || user?.roles?.includes('admin') || user?.currentRole === 'admin') && (
          <button
            className="p-1 rounded hover:bg-gray-100 text-red-400"
            onClick={() => onDelete?.(message.id)}
            title="删除"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        )}
      </div>
    );
  };

  // 系统消息使用特殊样式
  if (message.type === 'system') {
    return (
      <div className="flex justify-center my-4">
        <div className="bg-gray-100 text-gray-600 px-3 py-1 rounded-full text-sm">
          {renderMessageContent()}
        </div>
      </div>
    );
  }

  // 结构化消息（卡片）使用特殊布局
  if (message.type === 'structured') {
    return (
      <div className="mb-4">
        <div className="max-w-md">
          {/* 发送者信息 */}
          {showAvatar && (
            <div className="flex items-center mb-2">
              <img
                src={message.sender.avatar || '/avatars/default.png'}
                alt={message.sender.name}
                className="w-6 h-6 rounded-full mr-2"
              />
              <span className="text-sm text-gray-600">{message.sender.name}</span>
            </div>
          )}
          
          {/* 卡片内容 */}
          <div className="bg-white border border-gray-200 rounded-lg shadow-sm">
            {renderMessageContent()}
          </div>
          
          {/* 时间戳和反应 */}
          <div className="mt-2">
            {showTimestamp && (
              <span className="text-xs text-gray-500">
                {formatDistanceToNow(new Date(message.timestamp), { 
                  addSuffix: true, 
                  locale: zhCN 
                })}
              </span>
            )}
            {renderReactions()}
          </div>
        </div>
      </div>
    );
  }

  // 普通消息布局 - 统一垂直列表布局
  return (
    <div 
      className={`mb-4 relative group ${
        isSelected ? 'bg-yellow-50 rounded-lg p-2' : ''
      }`}
      onMouseEnter={() => setShowToolbar(true)}
      onMouseLeave={() => setShowToolbar(false)}
    >
      <div className="flex items-start space-x-3">
        {/* 头像 */}
        {showAvatar && (
          <img
            src={message.sender.avatar || '/avatars/default.png'}
            alt={message.sender.name}
            className="w-8 h-8 rounded-full flex-shrink-0"
          />
        )}
        
        <div className="flex-1 min-w-0 relative">
          {/* 工具栏 */}
          {renderToolbar()}
          
          {/* 发送者名称和时间戳 */}
          <div className="flex items-center space-x-2 mb-1">
            <span className="text-sm font-medium text-gray-900">
              {message.sender.name}
            </span>
            {showTimestamp && (
              <span className="text-xs text-gray-500">
                {formatDistanceToNow(new Date(message.timestamp), { 
                  addSuffix: true, 
                  locale: zhCN 
                })}
              </span>
            )}
            {message.status && (
              <span className="text-xs text-gray-500">
                {message.status === 'pending' && '发送中...'}
                {message.status === 'failed' && '发送失败'}
              </span>
            )}
          </div>
          
          {/* 消息内容 */}
          <div
            className={`
              ${message.type === 'media' 
                ? 'max-w-full' // 媒体消息不需要气泡样式
                : `inline-block px-3 py-2 rounded-lg max-w-full break-words relative
                   ${isOwn 
                     ? 'bg-blue-500 text-white' 
                     : 'bg-gray-100 text-gray-900'
                   }`
              }
              ${message.is_important && message.type !== 'media' ? 'ring-2 ring-yellow-400' : ''}
              ${message.status === 'failed' ? 'border-red-300 bg-red-50' : ''}
            `}
          >
            {renderMessageContent()}
            
            {/* 发送状态 - 仅对非媒体消息显示 */}
            {message.type !== 'media' && message.status === 'pending' && (
              <div className="absolute -bottom-1 -right-1">
                <div className="w-4 h-4 bg-gray-300 rounded-full animate-pulse"></div>
              </div>
            )}
            
            {message.type !== 'media' && message.status === 'failed' && (
              <button
                onClick={() => onRetry?.(message)}
                className="absolute -bottom-1 -right-1 w-4 h-4 bg-red-500 text-white rounded-full flex items-center justify-center text-xs hover:bg-red-600"
                title="重新发送"
              >
                !
              </button>
            )}
          </div>
          
          {/* 回复引用 */}
          {message.reply_to_message_id && (
            <div className="text-xs text-gray-500 mt-1">
              回复了一条消息
            </div>
          )}
          
          {/* 反应 */}
          {renderReactions()}
        </div>
      </div>
    </div>
  );
};

export default ChatMessage; 