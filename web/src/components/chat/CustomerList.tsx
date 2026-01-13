'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { cn } from '@/service/utils';
import { getCustomerList, getCustomerConversations } from '@/service/chatService';
import { Customer } from '@/types/chat';
import { useAuthContext } from '@/contexts/AuthContext';

const MAX_UNREAD_DISPLAY = 99;

interface CustomerListProps {
  onCustomerChange?: (customerId: string, conversationId?: string) => void;
  selectedCustomerId?: string | null;
  selectedConversationId?: string | null;
}

// 客户头像组件
interface CustomerAvatarProps {
  customer: Customer;
}

function CustomerAvatar({ customer }: CustomerAvatarProps) {
  const handleImageError = useCallback((e: React.SyntheticEvent<HTMLImageElement>) => {
    const target = e.target as HTMLImageElement;
    target.onerror = null;
    const nameInitial = customer.name.charAt(0);
    const parent = target.parentNode as HTMLElement;
    
    if (parent) {
      parent.innerHTML = 
        `<div class="h-10 w-10 rounded-full flex items-center justify-center text-white text-sm font-bold" style="background-color: #FF9800">${nameInitial}</div>`;
    }
  }, [customer.name]);

  return (
    <div className="flex-shrink-0 mr-3 relative">
      <img
        src={customer.avatar}
        alt={customer.name}
        className="h-10 w-10 rounded-full bg-gray-100"
        onError={handleImageError}
      />
      {/* 在线状态指示器 */}
      <div className={cn(
        "absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full border-2 border-white",
        customer.isOnline ? "bg-green-500" : "bg-gray-400"
      )}></div>
    </div>
  );
}

interface CustomerStatusProps {
  unreadCount: number;
  lifeCycleStage?: string;
}

function CustomerStatus({ unreadCount, lifeCycleStage }: CustomerStatusProps) {
  return (
    <div className="flex-shrink-0 ml-2 flex flex-col items-end">
      {unreadCount > 0 && (
        <span className="inline-flex items-center justify-center h-5 w-5 text-xs font-medium text-white bg-red-500 rounded-full mb-1">
          {unreadCount > MAX_UNREAD_DISPLAY ? `${MAX_UNREAD_DISPLAY}+` : unreadCount}
        </span>
      )}
      
      {lifeCycleStage && (
        <span className="rounded-full bg-gray-100 px-2 py-0.5 text-[10px] text-gray-700">
          {lifeCycleStage}
        </span>
      )}
    </div>
  );
}

// 客户列表项组件
interface CustomerListItemProps {
  customer: Customer;
  isSelected: boolean;
  onSelect: (customer: Customer) => void;
}

function CustomerListItem({ customer, isSelected, onSelect }: CustomerListItemProps) {
  const formatLastMessageTime = useCallback((timestamp?: string): string => {
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
  }, []);

  return (
    <div
      onClick={() => onSelect(customer)}
      className={cn(
        'flex items-center p-3 border-b border-gray-100 cursor-pointer transition-colors',
        isSelected 
          ? 'bg-orange-50 border-orange-200' 
          : 'hover:bg-gray-50'
      )}
    >
      <CustomerAvatar customer={customer} />

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
      </div>

      <CustomerStatus 
        unreadCount={customer.unreadCount}
        lifeCycleStage={customer.lifeCycleStage}
      />
    </div>
  );
}

// 工具函数
const sortCustomers = (customers: Customer[]): Customer[] => {
  return customers.sort((a, b) => {
    // 在线客户优先
    if (a.isOnline !== b.isOnline) {
      return a.isOnline ? -1 : 1;
    }
    
    // 同样在线状态下，按最近消息时间排序
    const aTime = a.lastMessageTime ? new Date(a.lastMessageTime).getTime() : 0;
    const bTime = b.lastMessageTime ? new Date(b.lastMessageTime).getTime() : 0;
    return bTime - aTime;
  });
};

const mergeCustomers = (prevCustomers: Customer[], newCustomers: Customer[]): Customer[] => {
  return newCustomers.map(newCustomer => {
    const existingCustomer = prevCustomers.find(c => c.id === newCustomer.id);
    if (!existingCustomer) return newCustomer;
    
    // 智能合并：保留现有客户对象的某些属性，仅更新变化的内容
    return {
      ...existingCustomer,
      // 只更新可能变化的状态属性
      isOnline: newCustomer.isOnline,
      lastMessage: newCustomer.lastMessage,
      lastMessageTime: newCustomer.lastMessageTime,
      unreadCount: newCustomer.unreadCount,
      lifeCycleStage: newCustomer.lifeCycleStage,
    };
  });
};

// 空状态组件
function EmptyState() {
  return (
    <div className="flex h-full flex-col items-center justify-center text-gray-500">
      <svg className="h-12 w-12 text-gray-300 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
      </svg>
      <p className="text-sm">暂无客户</p>
      <p className="text-xs text-gray-400 mt-1">等待客户咨询</p>
    </div>
  );
}

// 加载状态组件
function LoadingState() {
  return (
    <div className="flex h-full items-center justify-center">
      <div className="h-6 w-6 animate-spin rounded-full border-2 border-gray-300 border-t-orange-500"></div>
      <span className="ml-2 text-sm text-gray-500">加载客户列表...</span>
    </div>
  );
}

// 错误状态组件
interface ErrorStateProps {
  error: string;
  onRetry: () => void;
}

function ErrorState({ error, onRetry }: ErrorStateProps) {
  return (
    <div className="flex h-full flex-col items-center justify-center text-gray-500">
      <p className="text-sm">{error}</p>
      <button
        onClick={onRetry}
        className="mt-2 rounded-md bg-orange-500 px-3 py-1 text-xs text-white hover:bg-orange-600"
      >
        重试
      </button>
    </div>
  );
}

// 列表头部组件
function CustomerListHeader() {
  return (
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
  );
}

export default function CustomerList({ 
  onCustomerChange, 
  selectedCustomerId,
  selectedConversationId: _ // 接收但不使用，避免 TypeScript 错误
}: CustomerListProps) {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { user } = useAuthContext();
  const isFirstLoad = useRef(true);

  // 加载客户列表
  const loadCustomers = useCallback(async (isInitialLoad = false) => {
    try {
      if (isInitialLoad) {
        setLoading(true);
      }
      setError(null);
      
      const data = await getCustomerList();
      const sortedCustomers = sortCustomers(data);
      
      // 增量更新客户列表，而不是完全替换
      setCustomers(prevCustomers => {
        // 如果是首次加载，直接替换整个列表
        if (isFirstLoad.current) {
          isFirstLoad.current = false;
          return sortedCustomers;
        }
        
        // 否则增量更新列表
        return mergeCustomers(prevCustomers, sortedCustomers);
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

  // 初始化客户列表
  useEffect(() => {
    if (user) {
      // 首次加载时显示加载状态
      loadCustomers(true);
    }
  }, [user, loadCustomers]);
  
  // 处理客户选择
  const handleCustomerSelect = useCallback(async (customer: Customer) => {
    try {
      console.log(`选择客户: ${customer.name} (ID: ${customer.id})`);
      
      // 获取该客户的会话列表
      const conversations = await getCustomerConversations(customer.id);
      console.log(`获取到客户 ${customer.id} 的会话列表:`, conversations.length > 0 ? conversations.length + '个会话' : '无会话');
      
      // 找到活跃的会话或使用最近更新的会话
      let selectedConversation = conversations.find(conv => conv.isActive) || conversations[0];
      
      // 如果没有活跃会话，则按更新时间排序选择最近的会话
      if (!selectedConversation && conversations.length > 0) {
        // 按更新时间降序排序
        const sortedConversations = [...conversations].sort((a, b) => {
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
      
      if (onCustomerChange) {
        if (selectedConversation) {
          console.log(`为客户 ${customer.id} 选择会话: ${selectedConversation.id}`);
          onCustomerChange(customer.id, selectedConversation.id);
        } else {
          console.log(`客户 ${customer.id} 没有会话记录，只传递客户ID`);
          onCustomerChange(customer.id);
        }
      }
    } catch (error) {
      console.error(`获取客户 ${customer.id} 会话失败:`, error);
      // 出错时只传递客户ID
      if (onCustomerChange) {
        onCustomerChange(customer.id);
      }
    }
  }, [onCustomerChange]);

  // 渲染不同状态
  if (loading) {
    return <LoadingState />;
  }

  if (error) {
    return <ErrorState error={error} onRetry={() => loadCustomers(true)} />;
  }

  if (customers.length === 0) {
    return <EmptyState />;
  }

  return (
    <div className="flex flex-col">
      <CustomerListHeader />

      {/* 客户列表 */}
      <div className="flex-1 overflow-y-auto">
        {customers.map(customer => (
          <CustomerListItem
            key={customer.id}
            customer={customer}
            isSelected={selectedCustomerId === customer.id}
            onSelect={handleCustomerSelect}
          />
        ))}
      </div>
    </div>
  );
} 