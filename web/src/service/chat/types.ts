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
 * API响应格式 - 与后端ConversationInfo schema保持一致
 */
export interface ConversationApiResponse {
  id: string;
  title: string;
  chat_mode: 'single' | 'group';
  tag: 'chat' | 'consultation';
  owner_id: string;
  owner?: {
    id: string;
    username?: string;
    email?: string;
    avatar?: string;
  };
  // first_participant_id 和 first_participant 字段已移除（重构后不再需要）
  last_message?: MessageApiResponse;
  unread_count: number;
  message_count: number;
  last_message_at?: string;
  updated_at: string;
  created_at: string;
  is_active: boolean;
  is_archived: boolean;
  is_pinned?: boolean;
  pinned_at?: string;
}

export interface MessageApiResponse {
  id: string;
  conversation_id?: string;
  content: any;
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
  reply_to_message_id?: string;
  reactions?: { [emoji: string]: string[] };
  extra_metadata?: { [key: string]: any };
}

/**
 * 创建会话请求参数 - 与后端ConversationCreate schema保持一致
 */
export interface CreateConversationRequest {
  customer_id: string; // 保持向后兼容，后端会映射到owner_id
  title: string;
  chat_mode?: 'single' | 'group';
  tag?: 'chat' | 'consultation';
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