'use client';

import React, { useState, useMemo } from 'react';
import { type Message } from '@/types/chat';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  X, 
  Star, 
  MessageSquare, 
  User,
  Clock,
  Filter,
  SortAsc,
  SortDesc
} from 'lucide-react';
import { MessageUtils } from '@/utils/messageUtils';

interface ImportantMessagesPanelProps {
  messages: Message[];
  isOpen: boolean;
  onClose: () => void;
  onMessageClick?: (messageId: string) => void;
  onToggleImportant?: (messageId: string, currentStatus: boolean) => Promise<void>;
}

type SortOrder = 'asc' | 'desc';
type SortBy = 'timestamp' | 'sender';

export function ImportantMessagesPanel({ 
  messages, 
  isOpen, 
  onClose,
  onMessageClick,
  onToggleImportant
}: ImportantMessagesPanelProps) {
  const [sortBy, setSortBy] = useState<SortBy>('timestamp');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');
  const [filterSender, setFilterSender] = useState<string>('all');

  // 筛选重点消息
  const importantMessages = useMemo(() => {
    return messages.filter(msg => msg.is_important);
  }, [messages]);

  // 获取发送者列表用于筛选
  const senders = useMemo(() => {
    const senderMap = new Map();
    importantMessages.forEach(msg => {
      if (!senderMap.has(msg.sender.id)) {
        senderMap.set(msg.sender.id, {
          id: msg.sender.id,
          name: msg.sender.name,
          type: msg.sender.type
        });
      }
    });
    return Array.from(senderMap.values());
  }, [importantMessages]);

  // 应用筛选和排序
  const filteredAndSortedMessages = useMemo(() => {
    let filtered = [...importantMessages];
    
    // 应用发送者筛选
    if (filterSender !== 'all') {
      filtered = filtered.filter(msg => msg.sender.id === filterSender);
    }
    
    // 应用排序
    filtered.sort((a, b) => {
      let comparison = 0;
      
      if (sortBy === 'timestamp') {
        comparison = new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime();
      } else if (sortBy === 'sender') {
        comparison = a.sender.name.localeCompare(b.sender.name);
      }
      
      return sortOrder === 'asc' ? comparison : -comparison;
    });
    
    return filtered;
  }, [importantMessages, filterSender, sortBy, sortOrder]);

  // 格式化消息时间
  const formatMessageTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const isToday = date.toDateString() === now.toDateString();
    const isYesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000).toDateString() === date.toDateString();
    
    if (isToday) {
      return `今天 ${date.toLocaleTimeString('zh-CN', { 
        hour: '2-digit', 
        minute: '2-digit' 
      })}`;
    } else if (isYesterday) {
      return `昨天 ${date.toLocaleTimeString('zh-CN', { 
        hour: '2-digit', 
        minute: '2-digit' 
      })}`;
    } else {
      return date.toLocaleDateString('zh-CN', { 
        month: 'short', 
        day: 'numeric',
        hour: '2-digit', 
        minute: '2-digit' 
      });
    }
  };

  // 获取发送者类型的颜色
  const getSenderTypeColor = (type: string) => {
    switch (type) {
      case 'ai':
        return 'bg-blue-100 text-blue-800';
      case 'customer':
      case 'user':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  // 切换排序
  const toggleSort = (newSortBy: SortBy) => {
    if (sortBy === newSortBy) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(newSortBy);
      setSortOrder('desc');
    }
  };

  // 处理取消重点标记
  const handleToggleImportant = async (messageId: string) => {
    if (onToggleImportant) {
      try {
        await onToggleImportant(messageId, true); // 当前是重点消息，所以传true
      } catch (error) {
        console.error('取消重点标记失败:', error);
      }
    }
  };

  if (!isOpen) return null;

  return (
    <Card className="w-full h-[600px] flex flex-col shadow-lg">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-medium flex items-center">
            <Star className="w-5 h-5 mr-2 text-orange-500" />
            重点消息
            <Badge variant="secondary" className="ml-2">
              {importantMessages.length}
            </Badge>
          </CardTitle>
          <Button variant="ghost" size="sm" onClick={onClose} className="h-8 w-8 p-0">
            <X className="h-4 w-4" />
          </Button>
        </div>
        
        {/* 筛选和排序工具栏 */}
        <div className="space-y-3">
          {/* 发送者筛选 */}
          <div>
            <label className="text-sm font-medium text-gray-700 mb-2 block">筛选发送者</label>
            <select
              value={filterSender}
              onChange={(e) => setFilterSender(e.target.value)}
              className="w-full p-2 border border-gray-200 rounded-md text-sm"
            >
              <option value="all">全部发送者</option>
              {senders.map((sender) => (
                <option key={sender.id} value={sender.id}>
                  {sender.name}
                </option>
              ))}
            </select>
          </div>
          
          {/* 排序选项 */}
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-700">排序方式</span>
            <div className="flex items-center space-x-2">
              <Button
                variant={sortBy === 'timestamp' ? 'default' : 'outline'}
                size="sm"
                onClick={() => toggleSort('timestamp')}
                className="h-8"
              >
                <Clock className="w-3 h-3 mr-1" />
                时间
                {sortBy === 'timestamp' && (
                  sortOrder === 'asc' ? 
                    <SortAsc className="w-3 h-3 ml-1" /> : 
                    <SortDesc className="w-3 h-3 ml-1" />
                )}
              </Button>
              
              <Button
                variant={sortBy === 'sender' ? 'default' : 'outline'}
                size="sm"
                onClick={() => toggleSort('sender')}
                className="h-8"
              >
                <User className="w-3 h-3 mr-1" />
                发送者
                {sortBy === 'sender' && (
                  sortOrder === 'asc' ? 
                    <SortAsc className="w-3 h-3 ml-1" /> : 
                    <SortDesc className="w-3 h-3 ml-1" />
                )}
              </Button>
            </div>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="flex-1 overflow-hidden p-0">
        <div className="h-full overflow-y-auto p-4">
          {filteredAndSortedMessages.length === 0 && importantMessages.length === 0 && (
            <div className="text-center text-gray-500 py-8">
              <Star className="w-12 h-12 mx-auto mb-3 text-gray-300" />
              <p className="text-sm">暂无重点消息</p>
              <p className="text-xs text-gray-400 mt-1">
                在聊天中点击消息旁的星标来添加重点标记
              </p>
            </div>
          )}
          
          {filteredAndSortedMessages.length === 0 && importantMessages.length > 0 && (
            <div className="text-center text-gray-500 py-8">
              <Filter className="w-12 h-12 mx-auto mb-3 text-gray-300" />
              <p className="text-sm">当前筛选条件下没有消息</p>
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={() => setFilterSender('all')}
                className="mt-2"
              >
                清除筛选
              </Button>
            </div>
          )}
          
          {filteredAndSortedMessages.map((message) => {
            const textContent = MessageUtils.getTextContent(message) || '';
            
            return (
              <div
                key={message.id}
                className="group p-3 mb-3 rounded-lg bg-orange-50 border border-orange-100 hover:border-orange-200 transition-colors cursor-pointer"
                onClick={() => {
                  if (onMessageClick) {
                    onMessageClick(message.id);
                  }
                }}
              >
                {/* 消息头部 */}
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <Badge 
                      variant="secondary" 
                      className={getSenderTypeColor(message.sender.type)}
                    >
                      {message.sender.name}
                    </Badge>
                    <span className="text-xs text-gray-500">
                      {formatMessageTime(message.timestamp)}
                    </span>
                  </div>
                  
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleToggleImportant(message.id);
                    }}
                    className="h-6 w-6 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
                    title="取消重点标记"
                  >
                    <Star className="w-3 h-3 fill-orange-500 text-orange-500" />
                  </Button>
                </div>
                
                {/* 消息内容 */}
                <div className="text-sm text-gray-700">
                  {message.type === 'media' && (
                    <div className="flex items-center space-x-2 mb-1">
                      <MessageSquare className="w-4 h-4 text-gray-400" />
                      <span className="text-xs text-gray-500">媒体消息</span>
                    </div>
                  )}
                  <div className="line-clamp-3">
                    {textContent || '此消息包含媒体内容'}
                  </div>
                </div>
                
                {/* 消息类型指示器 */}
                {message.type === 'media' && (
                  <div className="mt-2 pt-2 border-t border-orange-200">
                    <div className="flex items-center text-xs text-gray-500">
                      <div className="w-2 h-2 bg-blue-400 rounded-full mr-2"></div>
                      包含媒体文件
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
