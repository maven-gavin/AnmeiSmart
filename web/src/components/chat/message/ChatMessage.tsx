'use client';

import { type Message } from '@/types/chat';
import { useState, useEffect } from 'react';
import { 
  markMessageAsImportant,
  saveMessage
} from '@/service/chatService';
import toast from 'react-hot-toast';
import FileMessage from './FileMessage';
import TextMessage from './TextMessage';
import VoiceMessage from './VoiceMessage';
import VideoMessage from './VideoMessage';
import ImageMessage from './ImageMessage';

/** 聊天消息组件的属性接口 */
export interface ChatMessageProps {
  /** 要显示的消息对象，包含消息内容、发送者信息、时间戳等 */
  message: Message;
  /** 是否选中该消息，选中时会高亮显示背景色 */
  isSelected?: boolean;
  /** 搜索关键词，用于在消息内容中高亮显示匹配的文本 */
  searchTerm?: string;
  /** 是否显示发送者信息（头像、名称、时间），默认为true */
  showSender?: boolean;
  /** 是否使用紧凑模式显示，紧凑模式下头像和内边距会更小 */
  compact?: boolean;
}

/** 消息内容组件的属性接口，用于各种类型的消息内容组件 */
export interface MessageContentProps {
  /** 要显示的消息对象，包含消息内容、类型、附件信息等 */
  message: Message;
  /** 搜索关键词，用于在消息内容中高亮显示匹配的文本 */
  searchTerm?: string;
  /** 是否使用紧凑模式显示，影响内容的间距和大小 */
  compact?: boolean;
}

export default function ChatMessage({
  message,
  isSelected = false,
  searchTerm = '',
  showSender = true,
  compact = false
}: ChatMessageProps) {
  const [showActions, setShowActions] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  
  // 消息发送者信息
  const avatar = message.sender?.avatar || '/avatars/default.png';
  const name = message.sender?.name || '未知用户';

  // 组件挂载时检查消息状态，如果是pending则自动保存
  useEffect(() => {
    const handlePendingMessage = async () => {
      if (message.status === 'pending' && message.localId && !isProcessing) {
        try {
          setIsProcessing(true);
          const savedMessage = await saveMessage(message);
          
          if (savedMessage) {
            message.status = 'sent';
            message.id = savedMessage.id;
            message.timestamp = savedMessage.timestamp;
            delete message.localId;
            message.canRecall = true;
            message.canRetry = false;
            message.canDelete = false;
            
            setTimeout(() => {
              message.canRecall = false;
            }, 60000);
          }
        } catch (error) {
          console.error('自动发送消息失败:', error);
          message.status = 'failed';
          message.error = error instanceof Error ? error.message : '发送失败';
          message.canRetry = true;
          message.canDelete = true;
        } finally {
          setIsProcessing(false);
        }
      }
    };

    handlePendingMessage();
  }, [message.status, message.localId, isProcessing]);

  // 处理重试发送
  const handleRetryMessage = async () => {
    if (isProcessing || !message.canRetry) return;
    
    try {
      setIsProcessing(true);
      if (message.status === 'failed') {
        const savedMessage = await saveMessage(message);
        if (savedMessage) {
          message.status = 'sent';
          message.id = savedMessage.id;
          message.timestamp = savedMessage.timestamp;
          delete message.error;
          message.canRetry = false;
          message.canDelete = false;
          message.canRecall = true;
          
          setTimeout(() => {
            message.canRecall = false;
          }, 60000);
        }
      }
      toast.success('消息重新发送成功');
    } catch (error) {
      console.error('重试发送失败:', error);
      toast.error('重试发送失败，请稍后再试');
    } finally {
      setIsProcessing(false);
    }
  };

  // 处理删除消息
  const handleDeleteMessage = async () => {
    if (isProcessing || !message.canDelete) return;
    
    try {
      setIsProcessing(true);
      toast.success('消息已删除');
    } catch (error) {
      console.error('删除消息失败:', error);
      toast.error('删除消息失败');
    } finally {
      setIsProcessing(false);
    }
  };

  // 处理撤销消息
  const handleRecallMessage = async () => {
    if (isProcessing || !message.canRecall) return;
    
    try {
      setIsProcessing(true);
      toast.success('消息已撤销');
    } catch (error) {
      console.error('撤销消息失败:', error);
      toast.error('撤销消息失败');
    } finally {
      setIsProcessing(false);
    }
  };

  // 处理重点标记切换
  const handleToggleImportant = async () => {
    if (isProcessing) return;
    
    try {
      setIsProcessing(true);
      const newImportantState = !message.isImportant;
      const result = await markMessageAsImportant(
        message.conversationId, 
        message.id, 
        newImportantState
      );
      
      if (result) {
        message.isImportant = newImportantState;
        toast.success(newImportantState ? '消息已标记为重点' : '已取消重点标记');
      } else {
        toast.error('操作失败，请重试');
      }
    } catch (error) {
      console.error('标记重点消息失败:', error);
      toast.error('标记重点消息失败，请检查网络连接');
    } finally {
      setIsProcessing(false);
    }
  };

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

  // 渲染状态指示器
  const renderStatusIndicator = () => {
    if (!message.status || message.status === 'sent') return null;

    return (
      <div className="flex items-center mt-1 text-xs">
        {message.status === 'pending' && (
          <div className="flex items-center text-gray-500">
            <svg className="animate-spin h-3 w-3 mr-1" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span>发送中...</span>
          </div>
        )}
        
        {message.status === 'failed' && (
          <div className="flex items-center text-red-500">
            <svg className="h-3 w-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            <span>发送失败</span>
            {message.error && (
              <span className="ml-1 text-gray-400">({message.error})</span>
            )}
          </div>
        )}
      </div>
    );
  };

  // 渲染操作按钮栏
  const renderActionButtons = () => {
    const actions = [];
    
    // 重点标记按钮
    actions.push(
      <button
        key="important"
        onClick={handleToggleImportant}
        disabled={isProcessing}
        className={`p-1.5 rounded-md transition-colors disabled:opacity-50 ${
          message.isImportant 
            ? 'text-yellow-600 hover:bg-yellow-50' 
            : 'text-gray-400 hover:text-gray-600 hover:bg-gray-50'
        }`}
        title={message.isImportant ? '取消重点标记' : '标记为重点'}
      >
        <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M3.172 5.172a4 4 0 015.656 0L10 6.343l1.172-1.171a4 4 0 115.656 5.656L10 17.657l-6.828-6.829a4 4 0 010-5.656z" clipRule="evenodd" />
        </svg>
      </button>
    );

    // 重试按钮
    if (message.canRetry) {
      actions.push(
        <button
          key="retry"
          onClick={handleRetryMessage}
          disabled={isProcessing}
          className="p-1.5 rounded-md text-orange-500 hover:text-orange-600 hover:bg-orange-50 transition-colors disabled:opacity-50"
          title="重新发送"
        >
          <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>
      );
    }

    // 撤销按钮
    if (message.canRecall) {
      actions.push(
        <button
          key="recall"
          onClick={handleRecallMessage}
          disabled={isProcessing}
          className="p-1.5 rounded-md text-blue-500 hover:text-blue-600 hover:bg-blue-50 transition-colors disabled:opacity-50"
          title="撤销消息"
        >
          <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
          </svg>
        </button>
      );
    }

    // 删除按钮
    if (message.canDelete) {
      actions.push(
        <button
          key="delete"
          onClick={handleDeleteMessage}
          disabled={isProcessing}
          className="p-1.5 rounded-md text-red-500 hover:text-red-600 hover:bg-red-50 transition-colors disabled:opacity-50"
          title="删除消息"
        >
          <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
        </button>
      );
    }

    if (actions.length === 0) return null;

    return (
      <div className={`absolute top-0 right-0 -mt-2 -mr-2 flex items-center bg-white border border-gray-200 rounded-lg shadow-sm transition-opacity duration-200 z-10 ${
        showActions ? 'opacity-100' : 'opacity-0 pointer-events-none'
      }`}>
        {actions}
      </div>
    );
  };

  // 根据消息类型渲染对应的内容组件
  const renderMessageContent = () => {
    const contentProps: MessageContentProps = {
      message,
      searchTerm,
      compact
    };

    // 文件消息展示 - 优先处理file类型且有file_info的消息
    if (message.type === 'file' && message.file_info) {
      return <FileMessage {...contentProps}  fileInfo={message.file_info} />;
    }
    
    // 图片消息展示
    if (message.type === 'image' || (message.type === 'file' && message.file_info?.file_type === 'image')) {
      return <ImageMessage {...contentProps} />;
    }
    
    // 语音消息展示  
    if (message.type === 'voice') {
      return <VoiceMessage {...contentProps} />;
    }
    
    // 视频消息展示
    if (message.type === 'video') {
      return <VideoMessage {...contentProps} />;
    }
    
    // 默认文本消息处理
    return <TextMessage {...contentProps} />;
  };
  
  return (
    <div
      id={`message-${message.id}`}
      data-testid={`message-${message.id}`}
      className={`relative my-4 mx-2 group ${
        isSelected ? 'bg-yellow-50 -mx-2 px-2 py-2 rounded-lg' : ''
      }`}
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => setShowActions(false)}
    >
      <div className="flex items-start space-x-3">
        {/* 头像 */}
        {showSender && (
          <div className="flex-shrink-0">
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
        
        <div className="flex-1 min-w-0 relative">
          {/* 发送者名称和时间 */}
          {showSender && (
            <div className="flex items-center mb-1">
              <span className="text-sm font-medium text-gray-700 mr-2">{name}</span>
              <span className="text-xs text-gray-500">
                {new Date(message.timestamp).toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'})}
              </span>
            </div>
          )}
          
          {/* 消息内容卡片 */}
          <div 
            className={`relative rounded-lg ${
              message.sender.type === 'customer' || message.sender.type === 'user'
                ? 'bg-white border border-gray-200 text-gray-800 shadow-sm'
                : message.sender.type === 'ai'
                  ? 'bg-blue-50 border border-blue-100 text-gray-800'
                  : message.sender.type === 'consultant'
                    ? 'bg-orange-50 border border-orange-200 text-gray-800'
                    : 'bg-gray-50 border border-gray-200 text-gray-800'
            } ${compact ? 'p-3' : 'p-4'} ${
              message.status === 'failed' ? 'border-red-200 bg-red-50' : ''
            }`}
          >
            {renderMessageContent()}
            
            {/* 消息状态指示器 */}
            {renderStatusIndicator()}
          </div>
          
          {/* 操作按钮栏 - 悬浮时显示在右上角 */}
          {renderActionButtons()}
        </div>
      </div>
    </div>
  );
}