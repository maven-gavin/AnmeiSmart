'use client';

import React, { useState, useCallback, useRef, useEffect } from 'react';
import { type Message } from '@/types/chat';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { 
  Search, 
  X, 
  ChevronUp, 
  ChevronDown,
  Filter,
  RotateCcw,
  MessageSquare
} from 'lucide-react';
import { MessageUtils } from '@/utils/messageUtils';

interface ChatSearchPanelProps {
  messages: Message[];
  isOpen: boolean;
  onClose: () => void;
  onMessageClick?: (messageId: string) => void;
}

interface SearchFilters {
  dateRange: 'all' | 'today' | 'week' | 'month';
  messageType: 'all' | 'text' | 'media';
  sender: 'all' | 'user' | 'ai' | 'consultant';
}

export function ChatSearchPanel({ 
  messages, 
  isOpen, 
  onClose,
  onMessageClick 
}: ChatSearchPanelProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState<Message[]>([]);
  const [selectedMessageId, setSelectedMessageId] = useState<string | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<SearchFilters>({
    dateRange: 'all',
    messageType: 'all',
    sender: 'all'
  });
  
  const searchTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // 防抖搜索函数
  const debouncedSearch = useCallback((term: string, currentFilters: SearchFilters) => {
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }
    
    searchTimeoutRef.current = setTimeout(() => {
      if (!term.trim()) {
        setSearchResults([]);
        setSelectedMessageId(null);
        return;
      }
      
      let filteredMessages = [...messages];
      const normalizedTerm = term.toLowerCase();
      
      // 应用日期筛选
      if (currentFilters.dateRange !== 'all') {
        const now = new Date();
        const filterDate = new Date();
        
        switch (currentFilters.dateRange) {
          case 'today':
            filterDate.setHours(0, 0, 0, 0);
            break;
          case 'week':
            filterDate.setDate(now.getDate() - 7);
            break;
          case 'month':
            filterDate.setMonth(now.getMonth() - 1);
            break;
        }
        
        filteredMessages = filteredMessages.filter(msg => 
          new Date(msg.timestamp) >= filterDate
        );
      }
      
      // 应用消息类型筛选
      if (currentFilters.messageType !== 'all') {
        filteredMessages = filteredMessages.filter(msg => msg.type === currentFilters.messageType);
      }
      
      // 应用发送者筛选
      if (currentFilters.sender !== 'all') {
        filteredMessages = filteredMessages.filter(msg => {
          switch (currentFilters.sender) {
            case 'user':
              return msg.sender.type === 'user';
            case 'ai':
              return msg.sender.type === 'ai';
            case 'consultant':
              return false; // SenderType 不包含 'consultant'，返回 false
            default:
              return true;
          }
        });
      }
      
      // 文本搜索
      const results = filteredMessages.filter(msg => {
        const textContent = MessageUtils.getTextContent(msg);
        return textContent && textContent.toLowerCase().includes(normalizedTerm);
      });
      
      setSearchResults(results);
      
      // 如果有结果，选中第一条
      if (results.length > 0) {
        setSelectedMessageId(results[0].id);
      } else {
        setSelectedMessageId(null);
      }
    }, 300);
  }, [messages]);

  // 搜索处理
  const handleSearch = useCallback((term: string) => {
    setSearchTerm(term);
    debouncedSearch(term, filters);
  }, [debouncedSearch, filters]);

  // 筛选器更新
  const handleFiltersChange = useCallback((newFilters: Partial<SearchFilters>) => {
    const updatedFilters = { ...filters, ...newFilters };
    setFilters(updatedFilters);
    debouncedSearch(searchTerm, updatedFilters);
  }, [filters, searchTerm, debouncedSearch]);

  // 导航到上一个/下一个结果
  const goToResult = useCallback((direction: 'next' | 'prev') => {
    if (searchResults.length === 0 || !selectedMessageId) return;
    
    const currentIndex = searchResults.findIndex(msg => msg.id === selectedMessageId);
    let newIndex: number;
    
    if (direction === 'next') {
      newIndex = (currentIndex + 1) % searchResults.length;
    } else {
      newIndex = currentIndex === 0 ? searchResults.length - 1 : currentIndex - 1;
    }
    
    const newSelectedId = searchResults[newIndex].id;
    setSelectedMessageId(newSelectedId);
    
    // 通知父组件滚动到消息
    if (onMessageClick) {
      onMessageClick(newSelectedId);
    }
  }, [searchResults, selectedMessageId, onMessageClick]);

  // 重置搜索
  const resetSearch = useCallback(() => {
    setSearchTerm('');
    setSearchResults([]);
    setSelectedMessageId(null);
    setFilters({
      dateRange: 'all',
      messageType: 'all',
      sender: 'all'
    });
    setShowFilters(false);
  }, []);

  // 格式化消息时间
  const formatMessageTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const today = new Date();
    const isToday = date.toDateString() === today.toDateString();
    
    if (isToday) {
      return date.toLocaleTimeString('zh-CN', { 
        hour: '2-digit', 
        minute: '2-digit' 
      });
    } else {
      return date.toLocaleDateString('zh-CN', { 
        month: 'short', 
        day: 'numeric',
        hour: '2-digit', 
        minute: '2-digit' 
      });
    }
  };

  // 高亮搜索词
  const highlightSearchTerm = (text: string, term: string) => {
    if (!term.trim()) return text;
    
    const regex = new RegExp(`(${term})`, 'gi');
    const parts = text.split(regex);
    
    return parts.map((part, index) => 
      regex.test(part) ? (
        <mark key={index} className="bg-yellow-200 text-yellow-900">
          {part}
        </mark>
      ) : part
    );
  };

  // 清理定时器
  useEffect(() => {
    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, []);

  if (!isOpen) return null;

  const currentIndex = selectedMessageId 
    ? searchResults.findIndex(m => m.id === selectedMessageId) + 1 
    : 0;

  return (
    <Card className="w-full h-[600px] flex flex-col shadow-lg">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-medium">查找聊天内容</CardTitle>
          <Button variant="ghost" size="sm" onClick={onClose} className="h-8 w-8 p-0">
            <X className="h-4 w-4" />
          </Button>
        </div>
        
        {/* 搜索输入 */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <Input
            type="text"
            value={searchTerm}
            onChange={(e) => handleSearch(e.target.value)}
            placeholder="搜索消息内容..."
            className="pl-10 pr-10"
            autoFocus
          />
          {searchTerm && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleSearch('')}
              className="absolute right-2 top-1/2 transform -translate-y-1/2 h-6 w-6 p-0"
            >
              <X className="w-3 h-3" />
            </Button>
          )}
        </div>
        
        {/* 工具栏 */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowFilters(!showFilters)}
              className="h-8"
            >
              <Filter className="w-4 h-4 mr-1" />
              筛选
            </Button>
            
            <Button
              variant="outline"
              size="sm"
              onClick={resetSearch}
              className="h-8"
            >
              <RotateCcw className="w-4 h-4 mr-1" />
              重置
            </Button>
          </div>
          
          {searchResults.length > 0 && (
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-500">
                {currentIndex} / {searchResults.length}
              </span>
              <div className="flex items-center space-x-1">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => goToResult('prev')}
                  disabled={searchResults.length === 0}
                  className="h-8 w-8 p-0"
                >
                  <ChevronUp className="w-4 h-4" />
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => goToResult('next')}
                  disabled={searchResults.length === 0}
                  className="h-8 w-8 p-0"
                >
                  <ChevronDown className="w-4 h-4" />
                </Button>
              </div>
            </div>
          )}
        </div>
        
        {/* 筛选器面板 */}
        {showFilters && (
          <div className="space-y-3 p-3 bg-gray-50 rounded-md">
            {/* 时间范围 */}
            <div>
              <label className="text-sm font-medium text-gray-700 mb-2 block">时间范围</label>
              <select
                value={filters.dateRange}
                onChange={(e) => handleFiltersChange({ dateRange: e.target.value as SearchFilters['dateRange'] })}
                className="w-full p-2 border border-gray-200 rounded-md text-sm"
              >
                <option value="all">全部时间</option>
                <option value="today">今天</option>
                <option value="week">最近一周</option>
                <option value="month">最近一个月</option>
              </select>
            </div>
            
            {/* 消息类型 */}
            <div>
              <label className="text-sm font-medium text-gray-700 mb-2 block">消息类型</label>
              <select
                value={filters.messageType}
                onChange={(e) => handleFiltersChange({ messageType: e.target.value as SearchFilters['messageType'] })}
                className="w-full p-2 border border-gray-200 rounded-md text-sm"
              >
                <option value="all">全部类型</option>
                <option value="text">文字消息</option>
                <option value="media">媒体消息</option>
              </select>
            </div>
            
            {/* 发送者 */}
            <div>
              <label className="text-sm font-medium text-gray-700 mb-2 block">发送者</label>
              <select
                value={filters.sender}
                onChange={(e) => handleFiltersChange({ sender: e.target.value as SearchFilters['sender'] })}
                className="w-full p-2 border border-gray-200 rounded-md text-sm"
              >
                <option value="all">全部</option>
                <option value="user">用户</option>
                <option value="ai">AI助手</option>
                <option value="consultant">顾问</option>
              </select>
            </div>
          </div>
        )}
      </CardHeader>
      
      <CardContent className="flex-1 overflow-hidden p-0">
        {/* 搜索结果 */}
        <div className="h-full overflow-y-auto p-4">
          {searchResults.length === 0 && searchTerm && (
            <div className="text-center text-gray-500 py-8">
              <Search className="w-12 h-12 mx-auto mb-3 text-gray-300" />
              <p>未找到匹配的消息</p>
            </div>
          )}
          
          {searchResults.length === 0 && !searchTerm && (
            <div className="text-center text-gray-500 py-8">
              <MessageSquare className="w-12 h-12 mx-auto mb-3 text-gray-300" />
              <p>输入关键词开始搜索</p>
            </div>
          )}
          
          {searchResults.map((message) => {
            const textContent = MessageUtils.getTextContent(message) || '';
            const isSelected = selectedMessageId === message.id;
            
            return (
              <div
                key={message.id}
                onClick={() => {
                  setSelectedMessageId(message.id);
                  if (onMessageClick) {
                    onMessageClick(message.id);
                  }
                }}
                className={`p-3 mb-2 rounded-lg cursor-pointer transition-colors ${
                  isSelected 
                    ? 'bg-orange-50 border border-orange-200' 
                    : 'bg-gray-50 hover:bg-gray-100'
                }`}
              >
                <div className="flex items-start justify-between mb-1">
                  <span className="text-sm font-medium text-gray-700">
                    {message.sender.name}
                  </span>
                  <span className="text-xs text-gray-500">
                    {formatMessageTime(message.timestamp)}
                  </span>
                </div>
                <div className="text-sm text-gray-600 line-clamp-3">
                  {highlightSearchTerm(textContent, searchTerm)}
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
