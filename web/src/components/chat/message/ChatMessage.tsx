'use client';

import React from 'react';
import { formatDistanceToNow } from 'date-fns';
import { zhCN } from 'date-fns/locale';
import { Message } from '@/types/chat';
import { MessageUtils } from '@/utils/messageUtils';

export interface MessageContentProps {
  message: Message;
  searchTerm?: string;
  compact?: boolean;
}
import TextMessage from './TextMessage';
import MediaMessage from './MediaMessage';
import SystemMessage from './SystemMessage';
import StructuredMessage from './StructuredMessage';

interface ChatMessageProps {
  message: Message;
  isOwn: boolean;
  showAvatar?: boolean;
  showTimestamp?: boolean;
  onReaction?: (messageId: string, emoji: string) => void;
  onReply?: (message: Message) => void;
  onCardAction?: (action: string, data: any) => void;
}

const ChatMessage: React.FC<ChatMessageProps> = ({
  message,
  isOwn,
  showAvatar = true,
  showTimestamp = true,
  onReaction,
  onReply,
  onCardAction
}) => {
  const renderMessageContent = () => {
    switch (message.type) {
      case 'text':
        return <TextMessage message={message} />;
      
      case 'media':
        return <MediaMessage message={message} />;
      
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
      <div className={`flex ${isOwn ? 'justify-end' : 'justify-start'} mb-4`}>
        <div className={`max-w-md ${isOwn ? 'order-1' : 'order-2'}`}>
          {/* 发送者信息 */}
          {!isOwn && showAvatar && (
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

  // 普通消息布局
  return (
    <div className={`flex ${isOwn ? 'justify-end' : 'justify-start'} mb-4`}>
      {/* 头像 */}
      {!isOwn && showAvatar && (
        <img
          src={message.sender.avatar || '/avatars/default.png'}
          alt={message.sender.name}
          className="w-8 h-8 rounded-full mr-3 mt-1"
        />
      )}
      
      <div className={`max-w-xs lg:max-w-md ${isOwn ? 'order-1' : 'order-2'}`}>
        {/* 发送者名称 */}
        {!isOwn && showAvatar && (
          <div className="text-sm text-gray-600 mb-1">
            {message.sender.name}
          </div>
        )}
        
        {/* 消息气泡 */}
        <div
          className={`
            px-4 py-2 rounded-lg max-w-full break-words
            ${isOwn 
              ? 'bg-blue-500 text-white' 
              : 'bg-gray-100 text-gray-900'
            }
            ${message.is_important ? 'ring-2 ring-yellow-400' : ''}
          `}
        >
          {renderMessageContent()}
        </div>
        
        {/* 回复引用 */}
        {message.reply_to_message_id && (
          <div className="text-xs text-gray-500 mt-1">
            回复了一条消息
          </div>
        )}
        
        {/* 时间戳 */}
        {showTimestamp && (
          <div className={`text-xs text-gray-500 mt-1 ${isOwn ? 'text-right' : 'text-left'}`}>
            {formatDistanceToNow(new Date(message.timestamp), { 
              addSuffix: true, 
              locale: zhCN 
            })}
            {message.status && (
              <span className="ml-2">
                {message.status === 'pending' && '发送中...'}
                {message.status === 'failed' && '发送失败'}
              </span>
            )}
          </div>
        )}
        
        {/* 反应 */}
        {renderReactions()}
      </div>
      
      {isOwn && showAvatar && (
        <img
          src={message.sender.avatar || '/avatars/default.png'}
          alt={message.sender.name}
          className="w-8 h-8 rounded-full ml-3 mt-1"
        />
      )}
    </div>
  );
};

export default ChatMessage; 