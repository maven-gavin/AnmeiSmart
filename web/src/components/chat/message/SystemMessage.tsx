'use client';

import React from 'react';
import type { MessageContentProps } from './ChatMessage';
import { SystemEventContent } from '@/types/chat';

export default function SystemMessage({ message }: MessageContentProps) {
  // 确保是系统消息
  if (message.type !== 'system') {
    return <div className="text-red-500">错误：非系统消息类型</div>;
  }

  const content = message.content as SystemEventContent;
  
  // 格式化系统事件文本
  const formatSystemEventText = (content: SystemEventContent): string => {
    const { system_event_type, status } = content;
    
    switch (system_event_type) {
      case 'user_joined':
        return `${content.user_name || '用户'} 加入了会话`;
      
      case 'user_left':
        return `${content.user_name || '用户'} 离开了会话`;
      
      case 'consultant_assigned':
        return `${content.consultant_name || '顾问'} 已分配到此会话`;
      
      case 'video_call_status':
        switch (status) {
          case 'initiated':
            return '发起了视频通话';
          case 'accepted':
            return '接受了视频通话';
          case 'declined':
            return '拒绝了视频通话';
          case 'missed':
            return '错过了视频通话';
          case 'ended':
            const duration = content.duration_seconds;
            if (duration) {
              const minutes = Math.floor(duration / 60);
              const seconds = duration % 60;
              return `通话结束，时长 ${minutes}:${seconds.toString().padStart(2, '0')}`;
            }
            return '通话结束';
          default:
            return '视频通话状态更新';
        }
      
      case 'conversation_created':
        return '会话已创建';
      
      case 'conversation_closed':
        return '会话已结束';
      
      case 'welcome':
        return content.message || '欢迎来到安美智享！我是您的AI助手，有什么可以帮助您的吗？';
      
      default:
        // 如果有message字段，优先使用
        if (content.message) {
          return content.message;
        }
        return `系统事件：${system_event_type || '未知'}`;
    }
  };

  const eventText = formatSystemEventText(content);

  // 渲染系统消息的图标
  const renderIcon = () => {
    const { system_event_type } = content;
    
    const iconClass = "w-4 h-4 mr-2";
    
    switch (system_event_type) {
      case 'user_joined':
        return (
          <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
          </svg>
        );
      
      case 'user_left':
        return (
          <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
          </svg>
        );
      
      case 'video_call_status':
        return (
          <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
        );
      
      default:
        return (
          <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
    }
  };

  return (
    <div className="flex items-center justify-center text-sm text-gray-500 my-2">
      <div className="flex items-center bg-gray-100 px-3 py-1 rounded-full">
        {renderIcon()}
        <span>{eventText}</span>
      </div>
    </div>
  );
} 