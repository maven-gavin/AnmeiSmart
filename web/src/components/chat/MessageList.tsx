'use client';

import React, { useCallback, useMemo } from 'react';
import { Message } from '@/types/chat';

interface MessageListProps {
  messages: Message[];
  importantMessages: Message[];
  showImportantOnly: boolean;
  selectedMessageId: string | null;
  searchTerm: string;
  toggleMessageImportant: (messageId: string, currentStatus: boolean) => void;
  toggleShowImportantOnly: () => void;
  highlightText: (text: string, searchTerm: string) => React.ReactNode;
  showSearch: boolean;
  formatMessageDate: (timestamp: string) => string;
}

export default function MessageList({
  messages,
  importantMessages,
  showImportantOnly,
  selectedMessageId,
  searchTerm,
  toggleMessageImportant,
  toggleShowImportantOnly,
  highlightText,
  showSearch,
  formatMessageDate
}: MessageListProps) {
  // 获取发送者名称和头像
  const getSenderInfo = useCallback((msg: Message) => {
    // 根据消息类型设置默认值
    let name = msg.sender.name || '未知用户';
    let avatar = msg.sender.avatar || '/avatars/default.png';
    let isSelf = false;
    
    // 检查是否是系统消息
    if (msg.sender.type === 'system') {
      name = '系统';
      avatar = '/avatars/system.png';
      return { name, avatar, isSelf };
    }
    
    // 检查是否是AI消息
    if (msg.sender.type === 'ai') {
      name = 'AI助手';
      avatar = '/avatars/ai.png';
      return { name, avatar, isSelf };
    }
    
    // 根据本地用户信息判断是否是自己发送的消息
    // 注意: 实际应用中应从上下文或props获取当前用户信息
    const currentUser = localStorage.getItem('currentUser');
    if (currentUser) {
      const user = JSON.parse(currentUser);
      if (user.id === msg.sender.id) {
        name = '我';
        isSelf = true;
        avatar = user.avatar || '/avatars/user.png';
      }
    }
    
    return { name, avatar, isSelf };
  }, []);

  // 渲染消息内容
  const renderMessageContent = useCallback((msg: Message) => {
    // 系统消息展示
    if (msg.isSystemMessage) {
      return (
        <div className="text-center py-1 px-2 bg-gray-100 rounded-full text-xs text-gray-500">
          {msg.content}
        </div>
      );
    }
    
    // 图片消息展示
    if (msg.type === 'image' && typeof msg.content === 'string') {
      return (
        <img 
          src={msg.content} 
          alt="聊天图片" 
          className="max-w-full max-h-60 rounded-md"
          onClick={() => window.open(msg.content, '_blank')}
        />
      );
    // 语音消息展示  
    } else if (msg.type === 'voice' && typeof msg.content === 'string') {
      return (
        <div className="flex items-center space-x-2">
          <audio src={msg.content} controls className="max-w-full" controlsList="nodownload" />
          <span className="text-xs opacity-70">语音消息</span>
        </div>
      );
    }
    
    // 文本消息处理，支持高亮搜索词
    return (
      <p className="break-words whitespace-pre-line">
        {showSearch && searchTerm.trim() && typeof msg.content === 'string'
          ? highlightText(msg.content, searchTerm)
          : msg.content}
      </p>
    );
  }, [highlightText, showSearch, searchTerm]);

  // 分组消息
  const messageGroups = useMemo(() => {
    const messagesToGroup = showImportantOnly ? importantMessages : messages;
    const groups: { date: string; messages: Message[] }[] = [];
    
    // 按日期分组，但不做去重处理
    messagesToGroup.forEach((msg: Message) => {
      const dateStr = formatMessageDate(msg.timestamp);
      
      // 查找或创建日期组
      let group = groups.find(g => g.date === dateStr);
      if (!group) {
        group = { date: dateStr, messages: [] };
        groups.push(group);
      }
      
      group.messages.push(msg);
    });
    
    return groups;
  }, [showImportantOnly, importantMessages, messages, formatMessageDate]);

  return (
    <>
      {/* 仅显示重点标记按钮 */}
      {importantMessages.length > 0 && (
        <div className="sticky top-0 z-10 mb-2 flex justify-end">
          <button
            className={`rounded-full px-3 py-1 text-xs font-medium flex items-center space-x-1 ${
              showImportantOnly 
              ? 'bg-orange-100 text-orange-700 border border-orange-300' 
              : 'bg-gray-100 text-gray-600 border border-gray-200 hover:bg-gray-200'
            }`}
            onClick={toggleShowImportantOnly}
          >
            <svg 
              className={`h-4 w-4 ${showImportantOnly ? 'text-orange-500' : 'text-gray-500'}`} 
              fill="currentColor" 
              viewBox="0 0 20 20"
            >
              <path 
                fillRule="evenodd" 
                d="M3.172 5.172a4 4 0 015.656 0L10 6.343l1.172-1.171a4 4 0 115.656 5.656L10 17.657l-6.828-6.829a4 4 0 010-5.656z" 
                clipRule="evenodd" 
              />
            </svg>
            <span>{showImportantOnly ? '查看全部消息' : '仅显示重点标记'}</span>
          </button>
        </div>
      )}

      {/* 显示分组后的消息列表 */}
      {messageGroups.map((group, groupIndex) => (
        <div key={group.date} className="space-y-4">
          {/* 日期分隔符 */}
          <div className="flex items-center justify-center my-4">
            <div className="h-px flex-grow bg-gray-200"></div>
            <div className="mx-4 text-xs text-gray-500">{group.date}</div>
            <div className="h-px flex-grow bg-gray-200"></div>
          </div>
          
          {/* 当前日期组的消息 */}
          {group.messages.map(msg => {
            const { name, avatar, isSelf } = getSenderInfo(msg);
            
            return (
              <div
                key={msg.id}
                id={`message-${msg.id}`}
                className={`flex ${isSelf ? 'justify-end' : 'justify-start'} items-end space-x-2 ${
                  selectedMessageId === msg.id ? 'bg-yellow-50 -mx-2 px-2 py-1 rounded-lg' : ''
                }`}
              >
                {/* 非自己发送的消息显示头像 */}
                {!isSelf && (
                  <img 
                    src={avatar} 
                    alt={name} 
                    className="h-8 w-8 rounded-full"
                    onError={(e) => {
                      const target = e.target as HTMLImageElement;
                      target.onerror = null;
                      target.src = '/avatars/default.png';
                    }}
                  />
                )}
                
                <div className={`flex max-w-[75%] flex-col ${isSelf ? 'items-end' : 'items-start'}`}>
                  {/* 发送者名称 */}
                  <span className="mb-1 text-xs text-gray-500">{name}</span>
                  
                  {/* 消息内容气泡 */}
                  <div 
                    className={`relative rounded-lg p-3 ${
                      isSelf
                        ? 'bg-orange-500 text-white'
                        : msg.sender.type === 'ai'
                          ? 'bg-gray-100 text-gray-800'
                          : 'bg-white border border-gray-200 text-gray-800'
                    }`}
                  >
                    {renderMessageContent(msg)}
                    
                    {/* 重点标记 */}
                    <button
                      onClick={() => toggleMessageImportant(msg.id, msg.isImportant || false)}
                      className={`absolute -right-1.5 -top-1.5 rounded-full p-0.5 ${
                        msg.isImportant ? 'bg-yellow-400 text-white' : 'bg-gray-200 text-gray-500'
                      }`}
                    >
                        <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                          <path 
                            fillRule="evenodd" 
                            d="M3.172 5.172a4 4 0 015.656 0L10 6.343l1.172-1.171a4 4 0 115.656 5.656L10 17.657l-6.828-6.829a4 4 0 010-5.656z" 
                            clipRule="evenodd" 
                          />
                      </svg>
                    </button>
                    
                    {/* 消息时间 */}
                    <div className={`mt-1 text-right text-xs ${isSelf ? 'text-white text-opacity-75' : 'text-gray-500'}`}>
                      {new Date(msg.timestamp).toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'})}
                    </div>
                  </div>
                </div>
                
                {/* 自己发送的消息显示头像 */}
                {isSelf && (
                  <img 
                    src={avatar} 
                    alt={name} 
                    className="h-8 w-8 rounded-full"
                    onError={(e) => {
                      const target = e.target as HTMLImageElement;
                      target.onerror = null;
                      target.src = '/avatars/default.png';
                    }}
                  />
                )}
              </div>
            );
          })}
        </div>
      ))}
      
      {showImportantOnly && importantMessages.length === 0 && (
        <div className="flex flex-col items-center justify-center h-32 text-gray-500">
          <svg className="h-12 w-12 mb-2 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
          </svg>
          <p className="text-sm">暂无标记的重点消息</p>
          <button 
            className="mt-2 text-sm text-orange-500 hover:underline"
            onClick={toggleShowImportantOnly}
          >
            返回全部消息
          </button>
        </div>
      )}
    </>
  );
} 