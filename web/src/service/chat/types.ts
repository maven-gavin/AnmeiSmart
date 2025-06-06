/**
 * 聊天模块类型定义
 * 统一管理聊天相关的接口和枚举
 */

import type { Message, Conversation, CustomerProfile, Customer, ConsultationHistoryItem } from "@/types/chat";
import type { SenderType } from '../websocket/types';

// 导出核心类型
export type { Message, Conversation, CustomerProfile, Customer, ConsultationHistoryItem, SenderType };

/**
 * 缓存配置
 */
export interface CacheConfig {
  messagesTime: number;
  conversationsTime: number;
}

/**
 * WebSocket连接参数
 */
export interface WebSocketConnectionParams {
  userId: string;
  conversationId: string;
  token: string;
  userType: SenderType;
  connectionId: string;
  // 设备信息相关字段
  deviceId?: string;
  deviceType?: string;
  deviceIP?: string;
  userAgent?: string;
  platform?: string;
  screenResolution?: string;
}

/**
 * 聊天状态接口
 */
export interface ChatStateData {
  chatMessages: Record<string, Message[]>;
  conversations: Conversation[];
  consultantTakeover: Record<string, boolean>;
  messageQueue: any[];
  lastConnectedConversationId: string | null;
  connectionDebounceTimer: NodeJS.Timeout | null;
  messageCallbacks: Record<string, ((message: any) => void)[]>;
  processedMessageIds: Set<string>;
  isRequestingMessages: Record<string, boolean>;
  lastMessagesRequestTime: Record<string, number>;
  isRequestingConversations: boolean;
  lastConversationsRequestTime: number;
}

/**
 * API响应格式
 */
export interface ConversationApiResponse {
  id: string;
  title: string;
  customer_id: string;
  customer?: {
    id: string;
    username?: string;
    avatar?: string;
    tags?: string | string[];
  };
  last_message?: MessageApiResponse;
  unread_count?: number;
  updated_at: string;
  status: string;
  consultation_type?: string;
  summary?: string;
  is_ai_controlled?: boolean;
}

export interface MessageApiResponse {
  id: string;
  conversation_id?: string;
  content: string;
  type?: string;
  sender?: {
    id: string;
    name?: string;
    avatar?: string;
    type?: string;
  };
  sender_id?: string;
  sender_name?: string;
  sender_avatar?: string;
  sender_type?: string;
  timestamp?: string;
  created_at?: string;
  is_important?: boolean;
  is_read?: boolean;
  is_system_message?: boolean;
}

/**
 * 创建会话请求参数
 */
export interface CreateConversationRequest {
  customer_id: string;
  title: string;
}

/**
 * 更新会话标题请求参数
 */
export interface UpdateConversationTitleRequest {
  title: string;
}

/**
 * AI服务请求参数
 */
export interface AIServiceRequest {
  conversation_id: string;
  content: string;
  type: string;
}

/**
 * 系统信息常量
 */
export const AI_INFO = {
  id: 'ai_assistant',
  name: 'AI助手',
  avatar: '/avatars/ai.png',
  type: 'ai' as const,
} as const;

export const SYSTEM_INFO = {
  id: 'system',
  name: '系统',
  avatar: '/avatars/system.png',
  type: 'system' as const,
} as const;

/**
 * 缓存时间常量
 */
export const CACHE_TIME = {
  MESSAGES: 5000, // 5秒
  CONVERSATIONS: 10000, // 10秒
} as const; 