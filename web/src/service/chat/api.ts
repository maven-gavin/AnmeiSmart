/**
 * 聊天API服务模块
 * 统一管理聊天相关的后端API调用
 */

import { apiClient, ApiClientError } from '../apiClient';
import { 
  Message, 
  Conversation, 
  CustomerProfile 
} from '@/types/chat';
import { 
  ConversationApiResponse, 
  MessageApiResponse, 
  AIServiceRequest,
  AI_INFO
} from './types';
import { 
  Customer,
  CreateConversationRequest,
  UpdateConversationTitleRequest
} from './types';
import { ChatDataMapper } from './mappers';

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
    try {
      const response = await apiClient.get<ConversationApiResponse[]>(`${this.BASE_PATH}/conversations`);
      return response.data ? ChatDataMapper.mapConversations(response.data) : [];
    } catch (error) {
      // 统一抛出可读错误，避免上层出现 {} 的错误对象
      if (error instanceof ApiClientError) {
        throw error;
      }
      throw new ApiClientError('获取会话列表失败', { status: 500 });
    }
  }
  
  /**
   * 获取会话详情
   */
  public static async getConversationDetails(conversationId: string): Promise<Conversation | null> {
    const response = await apiClient.get<ConversationApiResponse>(`${this.BASE_PATH}/conversations/${conversationId}`);
    return response.data ? ChatDataMapper.mapConversation(response.data) : null;
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
    
    return ChatDataMapper.mapConversation(response.data);
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
    return response.data ? ChatDataMapper.mapConversations(response.data) : [];
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
    return response.data ? ChatDataMapper.mapMessages(response.data) : [];
  }
  
  /**
   * 标记消息为重点
   */
  public static async markMessageAsImportant(
    conversationId: string, 
    messageId: string, 
    isImportant: boolean
  ): Promise<void> {
    await apiClient.patch(`${this.BASE_PATH}/conversations/${conversationId}/messages/${messageId}/important`, {
      is_important: isImportant
    });
  }

  /**
   * 保存消息
   */
  public static async saveMessage(message: Message): Promise<Message> {
    // 构造符合后端API期望的请求数据格式
    const requestData = {
      content: message.content,
      type: message.type
    };
    
    console.log('保存消息 - 发送请求:', JSON.stringify(requestData));
    
    const response = await apiClient.post<MessageApiResponse>(
      `${this.BASE_PATH}/conversations/${message.conversationId}/messages`, 
      requestData
    );
    
    if (!response.data) {
      throw new Error('保存消息失败：响应数据为空');
    }
    
    console.log('保存消息 - 服务器响应:', JSON.stringify(response.data));
    
    return ChatDataMapper.mapMessage(response.data);
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
    return response.data?.map(customer => {
      // 处理lastMessage的结构化内容
      let lastMessageText = '';
      if (customer.last_message?.content) {
        const content = customer.last_message.content;
        if (typeof content === 'string') {
          lastMessageText = content;
        } else if (typeof content === 'object') {
          // 新的结构化格式
          if (content.text) {
            lastMessageText = content.text;
          } else if (content.media_info && content.text) {
            lastMessageText = content.text || '[媒体消息]';
          } else if (content.media_info) {
            lastMessageText = '[媒体消息]';
          } else {
            lastMessageText = JSON.stringify(content);
          }
        }
      }

      return {
        id: customer.id,
        name: customer.name || "未知用户",
        avatar: customer.avatar || '/avatars/user.png',
        isOnline: customer.is_online || false,
        lastMessage: lastMessageText,
        lastMessageTime: customer.last_message?.created_at || customer.updated_at,
        unreadCount: customer.unread_count || 0,
        tags: customer.tags || [],
        priority: customer.priority || 'medium'
      };
    }) || [];
  }
  
  // ===== 数据映射已移至 ChatDataMapper 类 =====
} 