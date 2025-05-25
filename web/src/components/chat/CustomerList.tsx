'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { cn } from '@/service/utils';
import { getCustomerList, getCustomerConversations } from '@/service/chatService';
import { Customer, Conversation } from '@/types/chat';
import { useAuth } from '@/contexts/AuthContext';

interface CustomerListProps {
  onCustomerSelect?: (customerId: string, conversationId?: string) => void;
  selectedCustomerId?: string | null;
}

export default function CustomerList({ 
  onCustomerSelect, 
  selectedCustomerId 
}: CustomerListProps) {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { user } = useAuth();
  const isFirstLoad = useRef(true);

  // 加载客户列表
  const loadCustomers = useCallback(async (isInitialLoad = false) => {
    try {
      if (isInitialLoad) {
        setLoading(true);
      }
      setError(null);
      
      const data = await getCustomerList();
      
      // 按在线状态和最近消息时间排序
      const sortedCustomers = data.sort((a, b) => {
        // 在线客户优先
        if (a.isOnline !== b.isOnline) {
          return a.isOnline ? -1 : 1;
        }
        
        // 同样在线状态下，按最近消息时间排序
        const aTime = a.lastMessageTime ? new Date(a.lastMessageTime).getTime() : 0;
        const bTime = b.lastMessageTime ? new Date(b.lastMessageTime).getTime() : 0;
        return bTime - aTime;
      });
      
      // 增量更新客户列表，而不是完全替换
      setCustomers(prevCustomers => {
        // 如果是首次加载，直接替换整个列表
        if (isFirstLoad.current) {
          isFirstLoad.current = false;
          return sortedCustomers;
        }
        
        // 否则增量更新列表
        return sortedCustomers.map(newCustomer => {
          // 查找之前列表中的相同客户
          const existingCustomer = prevCustomers.find(c => c.id === newCustomer.id);
          if (!existingCustomer) return newCustomer; // 新客户直接添加
          
          // 智能合并：保留现有客户对象的某些属性，仅更新变化的内容
          return {
            ...existingCustomer,
            // 只更新可能变化的状态属性
            isOnline: newCustomer.isOnline,
            lastMessage: newCustomer.lastMessage,
            lastMessageTime: newCustomer.lastMessageTime,
            unreadCount: newCustomer.unreadCount,
            priority: newCustomer.priority,
            // 保留引用相同的不变属性，如头像、名称等静态内容
          };
        });
      });
    } catch (err) {
      console.error('获取客户列表失败:', err);
      setError('获取客户列表失败');
    } finally {
      if (isInitialLoad) {
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    if (user) {
      // 首次加载时显示加载状态
      loadCustomers(true);
      
      // 定期刷新客户在线状态，但不显示加载状态
      const interval = setInterval(() => loadCustomers(false), 30000); // 30秒刷新一次
      return () => clearInterval(interval);
    }
  }, [user, loadCustomers]);
  
  // 处理客户选择
  const handleCustomerSelect = useCallback(async (customer: Customer) => {
    try {
      console.log(`选择客户: ${customer.name} (ID: ${customer.id})`);
      
      // 使用更新后的API获取该客户的会话列表
      const conversations = await getCustomerConversations(customer.id);
      console.log(`获取到客户 ${customer.id} 的会话列表:`, conversations.length > 0 ? conversations.length + '个会话' : '无会话');
      
      // 找到活跃的会话或使用最近更新的会话
      let selectedConversation = conversations.find(conv => conv.status === 'active');
      
      // 如果没有活跃会话，则按更新时间排序选择最近的会话
      if (!selectedConversation && conversations.length > 0) {
        // 按更新时间降序排序
        const sortedConversations = [...conversations].sort((a, b) => {
          // 使用可选链和nullish合并运算符确保安全访问
          const dateA = new Date(a.updatedAt ?? '').getTime();
          const dateB = new Date(b.updatedAt ?? '').getTime();
          return dateB - dateA;
        });
        
        console.log(`未找到活跃会话，按时间排序后选择最新会话: ${sortedConversations[0].id}`);
        selectedConversation = sortedConversations[0];
      } else if (selectedConversation) {
        console.log(`找到活跃会话: ${selectedConversation.id}`);
      } else if (conversations.length > 0) {
        console.log(`无活跃会话且排序失败，使用第一个会话: ${conversations[0].id}`);
        selectedConversation = conversations[0];
      } else {
        console.log(`客户 ${customer.id} 没有会话记录`);
      }
      
      if (onCustomerSelect) {
        if (selectedConversation) {
          console.log(`为客户 ${customer.id} 选择会话: ${selectedConversation.id}`);
          
          // 确保在调用父组件回调之前等待会话选择完成
          // 使用短延迟确保选择会话后的UI更新和状态同步
          setTimeout(() => {
            if (onCustomerSelect) {
              onCustomerSelect(customer.id, selectedConversation!.id);
            }
          }, 100);
        } else {
          console.log(`客户 ${customer.id} 没有会话记录，只传递客户ID`);
          onCustomerSelect(customer.id);
        }
      }
    } catch (error) {
      console.error(`获取客户 ${customer.id} 会话失败:`, error);
      // 出错时只传递客户ID
      if (onCustomerSelect) {
        onCustomerSelect(customer.id);
      }
    }
  }, [onCustomerSelect]);
  
  // 自动选择默认客户
  useEffect(() => {
    // 确保客户列表已加载，并且当前没有选中的客户
    if (!loading && customers.length > 0 && !selectedCustomerId && onCustomerSelect) {
      console.log('CustomerList: 准备自动选择默认客户...');
      
      // 设置一个较长的延迟，确保不会与其他初始化逻辑冲突
      const timer = setTimeout(() => {
        // 再次检查是否仍然需要自动选择
        if (!selectedCustomerId && customers.length > 0) {
          console.log('CustomerList: 自动选择默认客户:', customers[0].name);
          
          // 延迟执行，确保DOM已更新且其他组件已准备好
          // 这有助于确保选择客户和加载会话历史的顺序正确
          setTimeout(() => {
            // 自动选择第一个客户
            handleCustomerSelect(customers[0]);
          }, 100);
        }
      }, 500); // 增加延迟时间，确保页面其他部分已完成初始化
      
      return () => clearTimeout(timer);
    }
  }, [loading, customers, selectedCustomerId, onCustomerSelect, handleCustomerSelect]);

  // 格式化最后消息时间
  const formatLastMessageTime = (timestamp?: string): string => {
    if (!timestamp) return '';
    
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffMins < 1) return '刚刚';
    if (diffMins < 60) return `${diffMins}分钟前`;
    if (diffHours < 24) return `${diffHours}小时前`;
    if (diffDays < 7) return `${diffDays}天前`;
    
    return date.toLocaleDateString();
  };

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-gray-300 border-t-orange-500"></div>
        <span className="ml-2 text-sm text-gray-500">加载客户列表...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-full flex-col items-center justify-center text-gray-500">
        <p className="text-sm">{error}</p>
        <button
          onClick={() => loadCustomers(true)}
          className="mt-2 rounded-md bg-orange-500 px-3 py-1 text-xs text-white hover:bg-orange-600"
        >
          重试
        </button>
      </div>
    );
  }

  if (customers.length === 0) {
    return (
      <div className="flex h-full flex-col items-center justify-center text-gray-500">
        <svg className="h-12 w-12 text-gray-300 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
        </svg>
        <p className="text-sm">暂无客户</p>
        <p className="text-xs text-gray-400 mt-1">等待客户咨询</p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* 标题 */}
      <div className="p-3 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-medium text-gray-700">客户列表</h3>
          <div className="flex items-center text-xs text-gray-500">
            <div className="flex items-center mr-3">
              <div className="w-2 h-2 bg-green-500 rounded-full mr-1"></div>
              在线
            </div>
            <div className="flex items-center">
              <div className="w-2 h-2 bg-gray-400 rounded-full mr-1"></div>
              离线
            </div>
          </div>
        </div>
      </div>

      {/* 客户列表 */}
      <div className="flex-1 overflow-y-auto">
        {customers.map(customer => (
          <div
            key={customer.id}
            onClick={() => handleCustomerSelect(customer)}
            className={cn(
              'flex items-center p-3 border-b border-gray-100 cursor-pointer transition-colors',
              selectedCustomerId === customer.id 
                ? 'bg-orange-50 border-orange-200' 
                : 'hover:bg-gray-50'
            )}
          >
            {/* 客户头像和在线状态 */}
            <div className="flex-shrink-0 mr-3 relative">
              <img
                src={customer.avatar}
                alt={customer.name}
                className="h-10 w-10 rounded-full bg-gray-100"
                onError={(e) => {
                  const target = e.target as HTMLImageElement;
                  target.onerror = null;
                  const nameInitial = customer.name.charAt(0);
                  target.style.display = 'flex';
                  target.style.alignItems = 'center';
                  target.style.justifyContent = 'center';
                  target.style.backgroundColor = '#FF9800';
                  target.style.color = '#FFFFFF';
                  target.style.fontSize = '14px';
                  target.style.fontWeight = 'bold';
                  target.src = 'data:image/svg+xml;charset=UTF-8,' + 
                    encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40"></svg>');
                  setTimeout(() => {
                    (target.parentNode as HTMLElement).innerHTML = 
                      `<div class="h-10 w-10 rounded-full flex items-center justify-center text-white text-sm font-bold" style="background-color: #FF9800">${nameInitial}</div>`;
                  }, 0);
                }}
              />
              {/* 在线状态指示器 */}
              <div className={cn(
                "absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full border-2 border-white",
                customer.isOnline ? "bg-green-500" : "bg-gray-400"
              )}></div>
            </div>

            {/* 客户信息 */}
            <div className="flex-1 min-w-0">
              {/* 姓名和时间 */}
              <div className="flex items-center justify-between mb-1">
                <h4 className="text-sm font-medium text-gray-800 truncate">
                  {customer.name}
                </h4>
                <span className="text-xs text-gray-500 flex-shrink-0 ml-2">
                  {formatLastMessageTime(customer.lastMessageTime)}
                </span>
              </div>

              {/* 最后一条消息 */}
              {customer.lastMessage && (
                <p className="text-xs text-gray-500 truncate">
                  {customer.lastMessage}
                </p>
              )}

              {/* 客户标签 */}
              {customer.tags && customer.tags.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-1">
                  {customer.tags.slice(0, 2).map(tag => (
                    <span 
                      key={tag}
                      className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800"
                    >
                      {tag}
                    </span>
                  ))}
                  {customer.tags.length > 2 && (
                    <span className="text-xs text-gray-400">+{customer.tags.length - 2}</span>
                  )}
                </div>
              )}
            </div>

            {/* 未读消息数和优先级 */}
            <div className="flex-shrink-0 ml-2 flex flex-col items-end">
              {customer.unreadCount > 0 && (
                <span className="inline-flex items-center justify-center h-5 w-5 text-xs font-medium text-white bg-red-500 rounded-full mb-1">
                  {customer.unreadCount > 99 ? '99+' : customer.unreadCount}
                </span>
              )}
              
              {customer.priority === 'high' && (
                <svg className="h-4 w-4 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
} 