/**
 * 聊天API服务模块
 * 统一管理聊天相关的后端API调用
 */

import { apiClient } from '../apiClient';
import type { 
  Conversation, 
  Message, 
  CustomerProfile, 
  Customer,
  ConversationApiResponse,
  MessageApiResponse,
  CreateConversationRequest,
  UpdateConversationTitleRequest,
  AIServiceRequest,
  SenderType
} from './types';
import { AI_INFO } from './types';

/**
 * 聊天API服务类
 * 专门处理聊天相关的后端API调用
 */
export class ChatApiService {
  private static readonly BASE_PATH = '/chat';
  
  // ===== 会话相关API =====
  
  /**
   * 获取会话列表
   */
  public static async getConversations(): Promise<Conversation[]> {
    const response = await apiClient.get<ConversationApiResponse[]>(`${this.BASE_PATH}/conversations`);
    return response.data?.map(conv => this.formatConversation(conv)) || [];
  }
  
  /**
   * 获取会话详情
   */
  public static async getConversationDetails(conversationId: string): Promise<Conversation | null> {
    const response = await apiClient.get<ConversationApiResponse>(`${this.BASE_PATH}/conversations/${conversationId}`);
    return response.data ? this.formatConversation(response.data) : null;
  }
  
  /**
   * 创建新会话
   */
  public static async createConversation(customerId: string, title?: string): Promise<Conversation> {
    const requestData: CreateConversationRequest = {
      customer_id: customerId,
      title: title || `咨询会话 ${new Date().toLocaleDateString('zh-CN')}`
    };
    
    const response = await apiClient.post<ConversationApiResponse>(`${this.BASE_PATH}/conversations`, requestData);
    if (!response.data) {
      throw new Error('创建会话失败：响应数据为空');
    }
    
    return this.formatConversation(response.data);
  }
  
  /**
   * 更新会话标题
   */
  public static async updateConversationTitle(conversationId: string, title: string): Promise<void> {
    const requestData: UpdateConversationTitleRequest = {
      title: title.trim()
    };
    
    await apiClient.patch(`${this.BASE_PATH}/conversations/${conversationId}`, requestData);
  }
  
  /**
   * 获取指定客户的会话列表
   */
  public static async getCustomerConversations(customerId: string): Promise<Conversation[]> {
    const response = await apiClient.get<ConversationApiResponse[]>(`${this.BASE_PATH}/conversations?customer_id=${customerId}`);
    return response.data?.map(conv => this.formatConversation(conv)) || [];
  }
  
  // ===== 消息相关API =====
  
  /**
   * 获取会话消息
   */
  public static async getConversationMessages(conversationId: string): Promise<Message[]> {
    // 添加时间戳参数避免缓存
    const timestamp = Date.now();
    const url = `${this.BASE_PATH}/conversations/${conversationId}/messages?nocache=${timestamp}`;
    
    const response = await apiClient.get<MessageApiResponse[]>(url);
    return response.data?.map(msg => this.formatMessage(msg)) || [];
  }
  
  /**
   * 标记消息为重点
   */
  public static async markMessageAsImportant(
    conversationId: string, 
    messageId: string, 
    isImportant: boolean
  ): Promise<void> {
    await apiClient.put(`${this.BASE_PATH}/conversations/${conversationId}/messages/${messageId}/important`, {
      is_important: isImportant
    });
  }
  
  // ===== 接管状态API =====
  
  /**
   * 设置顾问接管状态
   */
  public static async setTakeoverStatus(conversationId: string, isAiControlled: boolean): Promise<void> {
    const endpoint = isAiControlled 
      ? `${this.BASE_PATH}/conversations/${conversationId}/release`
      : `${this.BASE_PATH}/conversations/${conversationId}/takeover`;
    
    await apiClient.post(endpoint);
  }
  
  // ===== AI服务API =====
  
  /**
   * 调用AI服务获取回复
   */
  public static async getAIResponse(conversationId: string, content: string): Promise<string> {
    const requestData: AIServiceRequest = {
      conversation_id: conversationId,
      content,
      type: "text"
    };
    
    const response = await apiClient.post<{ content: string }>('/ai/chat', requestData);
    return response.data?.content || '抱歉，AI服务暂时不可用，请稍后再试。';
  }
  
  // ===== 客户相关API =====
  
  /**
   * 获取客户档案
   */
  public static async getCustomerProfile(customerId: string): Promise<CustomerProfile | null> {
    const response = await apiClient.get<CustomerProfile>(`/customers/${customerId}/profile`);
    return response.data || null;
  }
  
  /**
   * 获取客户列表
   */
  public static async getCustomerList(): Promise<Customer[]> {
    const response = await apiClient.get<any[]>('/customers/');
    return response.data?.map(customer => ({
      id: customer.id,
      name: customer.name || "未知用户",
      avatar: customer.avatar || '/avatars/user.png',
      isOnline: customer.is_online || false,
      lastMessage: customer.last_message?.content || '',
      lastMessageTime: customer.last_message?.created_at || customer.updated_at,
      unreadCount: customer.unread_count || 0,
      tags: customer.tags || [],
      priority: customer.priority || 'medium'
    })) || [];
  }
  
  // ===== 数据格式化方法 =====
  
  /**
   * 格式化会话对象
   */
  private static formatConversation(conv: ConversationApiResponse): Conversation {
    let customerName = "未知用户";
    if (conv.customer) {
      customerName = conv.customer.username || "未知用户";
    }
    
    // 格式化最后一条消息
    let lastMessage: Message | undefined;
    if (conv.last_message) {
      lastMessage = this.formatMessage(conv.last_message);
    }
    
    return {
      id: conv.id,
      title: conv.title,
      user: {
        id: conv.customer_id,
        name: customerName,
        avatar: conv.customer?.avatar || '/avatars/user.png',
        tags: conv.customer?.tags ? (typeof conv.customer.tags === 'string' ? conv.customer.tags.split(',') : conv.customer.tags) : []
      },
      lastMessage,
      unreadCount: conv.unread_count || 0,
      updatedAt: conv.updated_at,
      status: (conv.status as "active" | "inactive" | "archived") || "active",
      consultationType: conv.consultation_type || '一般咨询',
      summary: conv.summary || ''
    };
  }
  
  /**
   * 格式化消息对象
   */
  private static formatMessage(msg: MessageApiResponse): Message {
    return {
      id: msg.id,
      content: msg.content,
      type: (msg.type as "text" | "image" | "voice") || 'text',
      sender: {
        id: msg.sender?.id || msg.sender_id || '',
        name: msg.sender?.name || msg.sender_name || '未知',
        avatar: msg.sender?.avatar || msg.sender_avatar || 
               (msg.sender?.type === 'ai' || msg.sender_type === 'ai' ? AI_INFO.avatar : '/avatars/user.png'),
        type: (msg.sender?.type || msg.sender_type || 'user') as SenderType,
      },
      timestamp: msg.timestamp || msg.created_at || new Date().toISOString(),
      isImportant: msg.is_important || false,
      isRead: msg.is_read || false,
      isSystemMessage: msg.is_system_message || false
    };
  }
} 