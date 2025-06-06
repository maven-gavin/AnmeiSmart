'use client';

import { type Message } from '@/types/chat';
import { useState, useEffect } from 'react';
import { 
  markMessageAsImportant,
  saveMessage
} from '@/service/chatService';
import toast from 'react-hot-toast';

export interface ChatMessageProps {
  message: Message;
  isSelected?: boolean;
  searchTerm?: string;
  showSender?: boolean;
  compact?: boolean;
}

export default function ChatMessage({
  message,
  isSelected = false,
  searchTerm = '',
  showSender = true,
  compact = false
}: ChatMessageProps) {
  const [imageExpanded, setImageExpanded] = useState(false);
  const [showActions, setShowActions] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  
  // 消息发送者信息
  const avatar = message.sender?.avatar || '/avatars/default.png';
  const name = message.sender?.name || '未知用户';

  // 组件挂载时检查消息状态，如果是pending则自动保存
  useEffect(() => {
    const handlePendingMessage = async () => {
      // 检查消息是否为pending状态且有localId（表示是本地创建的待发送消息）
      if (message.status === 'pending' && message.localId && !isProcessing) {
        try {
          setIsProcessing(true);
          
          // 保存消息到后端
          const savedMessage = await saveMessage(message);
          
          if (savedMessage) {
            // 更新消息状态 - 直接修改message对象
            // 注意：这里直接修改props，在实际应用中可能需要通过回调传递给父组件
            message.status = 'sent';
            message.id = savedMessage.id;
            message.timestamp = savedMessage.timestamp;
            // 清除localId，表示已成功保存
            delete message.localId;
            // 设置撤销权限（1分钟内）
            message.canRecall = true;
            message.canRetry = false;
            message.canDelete = false;
            
            // 1分钟后取消撤销权限
            setTimeout(() => {
              message.canRecall = false;
            }, 60000);
          }
        } catch (error) {
          console.error('自动发送消息失败:', error);
          // 设置为失败状态
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
        // 调用重试逻辑
        const savedMessage = await saveMessage(message);
        if (savedMessage) {
          message.status = 'sent';
          message.id = savedMessage.id;
          message.timestamp = savedMessage.timestamp;
          // 清除错误信息和重试标记
          delete message.error;
          message.canRetry = false;
          message.canDelete = false;
          // 设置撤销权限（1分钟内）
          message.canRecall = true;
          
          // 1分钟后取消撤销权限
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
      // 调用删除逻辑 - 暂时只从UI删除，后续实现后端API
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
      // 调用撤销逻辑 - 暂时只显示提示，后续实现后端API
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
      const result = await markMessageAsImportant(
        message.conversationId, 
        message.id, 
        !message.isImportant
      );
      
      if (result) {
        toast.success(!message.isImportant ? '消息已标记为重点' : '已取消重点标记');
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

  // 渲染操作按钮
  const renderActionButtons = () => {
    const hasActions = message.canRetry || message.canDelete || message.canRecall;
    if (!hasActions || !showActions) return null;

    return (
      <div className="flex items-center space-x-2 mt-2 pt-2 border-t border-gray-100">
        {message.canRetry && (
          <button
            onClick={handleRetryMessage}
            disabled={isProcessing}
            className="flex items-center px-2 py-1 text-xs text-orange-600 hover:text-orange-700 hover:bg-orange-50 rounded disabled:opacity-50"
          >
            <svg className="h-3 w-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            重试
          </button>
        )}
        
        {message.canDelete && (
          <button
            onClick={handleDeleteMessage}
            disabled={isProcessing}
            className="flex items-center px-2 py-1 text-xs text-red-600 hover:text-red-700 hover:bg-red-50 rounded disabled:opacity-50"
          >
            <svg className="h-3 w-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
            删除
          </button>
        )}
        
        {message.canRecall && (
          <button
            onClick={handleRecallMessage}
            disabled={isProcessing}
            className="flex items-center px-2 py-1 text-xs text-gray-600 hover:text-gray-700 hover:bg-gray-50 rounded disabled:opacity-50"
          >
            <svg className="h-3 w-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
            </svg>
            撤销
          </button>
        )}
      </div>
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
      data-testid={`message-${message.id}`}
      className={`my-4 mx-2 ${
        isSelected ? 'bg-yellow-50 -mx-2 px-2 py-2 rounded-lg' : ''
      }`}
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => setShowActions(false)}
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
            className={`relative rounded-lg shadow-sm ${
              message.sender.type === 'customer' || message.sender.type === 'user'
                ? 'bg-white border border-gray-200 text-gray-800'
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
            
            {/* 操作按钮 */}
            {renderActionButtons()}
            
            {/* 重点标记按钮 */}
            <button
              onClick={handleToggleImportant}
              disabled={isProcessing}
              className={`absolute -right-1.5 -top-1.5 rounded-full p-1 shadow-sm disabled:opacity-50 ${
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
          </div>
        </div>
      </div>
    </div>
  );
} 