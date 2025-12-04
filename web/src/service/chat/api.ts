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
    // 后端返回分页对象 { items, total, skip, limit }
    const response = await apiClient.get<{ items: ConversationApiResponse[]; total: number; skip: number; limit: number }>(`${this.BASE_PATH}/conversations`);
    // 从分页对象中提取 items 数组
    const items = response.data?.items || response.data || [];
    return ChatDataMapper.mapConversations(Array.isArray(items) ? items : []);
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
   * 标记会话为已读
   */
  public static async markConversationAsRead(conversationId: string): Promise<void> {
    await apiClient.patch(`${this.BASE_PATH}/conversations/${conversationId}/read`, {});
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
    // 如果是媒体消息，使用专门的媒体消息端点
    if (message.type === 'media' && message.content && typeof message.content === 'object' && 'media_info' in message.content) {
      return this.createMediaMessage(message);
    }
    
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

  /**
   * 创建媒体消息
   */
  public static async createMediaMessage(message: Message): Promise<Message> {
    const content = message.content as any;
    const mediaInfo = content.media_info;
    
    if (!mediaInfo || !mediaInfo.url) {
      throw new Error('媒体消息缺少媒体信息');
    }
    
    // 确保文件名和大小不为空
    // 如果文件名为空或"unknown"，尝试从URL中提取
    let fileName = mediaInfo.name;
    if (!fileName || fileName === 'unknown') {
      const urlPath = mediaInfo.url.split('?')[0];
      const pathParts = urlPath.split('/');
      const extractedName = pathParts[pathParts.length - 1];
      if (extractedName && extractedName.includes('.')) {
        fileName = decodeURIComponent(extractedName);
      } else {
        fileName = 'unknown';
      }
    }
    
    // 确保文件大小不为0，如果为0则尝试从metadata中获取
    let fileSize = mediaInfo.size_bytes;
    if (!fileSize || fileSize === 0) {
      if (mediaInfo.metadata && mediaInfo.metadata.size_bytes) {
        fileSize = mediaInfo.metadata.size_bytes;
      } else {
        fileSize = 0; // 如果确实没有大小信息，保持为0
      }
    }
    
    const requestData = {
      media_url: mediaInfo.url,
      media_name: fileName,  // 使用处理后的文件名
      mime_type: mediaInfo.mime_type || 'application/octet-stream',
      size_bytes: fileSize,  // 使用处理后的文件大小
      text: content.text || null,
      metadata: mediaInfo.metadata || {},
      is_important: false,
      upload_method: 'file_picker'
    };
    
    console.log('创建媒体消息 - 发送请求:', JSON.stringify(requestData));
    
    const response = await apiClient.post<MessageApiResponse>(
      `${this.BASE_PATH}/conversations/${message.conversationId}/messages/media`,
      requestData
    );
    
    if (!response.data) {
      throw new Error('创建媒体消息失败：响应数据为空');
    }
    
    console.log('创建媒体消息 - 服务器响应:', JSON.stringify(response.data));
    
    return ChatDataMapper.mapMessage(response.data);
  }
  
  // ===== 接管状态API =====
  
  /**
   * 设置参与者接管状态（支持三种状态）
   */
  public static async setTakeoverStatus(
    conversationId: string, 
    takeoverStatus: 'full_takeover' | 'semi_takeover' | 'no_takeover'
  ): Promise<{ conversation_id: string; user_id: string; takeover_status: string }> {
    const endpoint = `${this.BASE_PATH}/conversations/${conversationId}/takeover-status?takeover_status=${takeoverStatus}`;
    
    console.log('ChatApiService.setTakeoverStatus 调用:', { endpoint, takeoverStatus });
    
    try {
      const response = await apiClient.patch<{ conversation_id: string; user_id: string; takeover_status: string }>(
        endpoint,
        {}
      );
      
      console.log('ChatApiService.setTakeoverStatus 响应:', response);
      
      if (!response || !response.data) {
        console.error('setTakeoverStatus 响应数据为空:', response);
        throw new Error('API响应数据为空');
      }
      
      if (typeof response.data !== 'object' || !('takeover_status' in response.data)) {
        console.error('setTakeoverStatus 响应数据格式不正确:', response.data);
        throw new Error('API响应数据格式不正确');
      }
      
      return response.data;
    } catch (error) {
      console.error('setTakeoverStatus 调用失败:', error);
      // 输出更详细的错误信息
      if (error instanceof Error) {
        console.error('API调用错误详情:', {
          message: error.message,
          stack: error.stack,
          name: error.name
        });
      }
      throw error;
    }
  }
  
  /**
   * 获取当前用户的接管状态
   */
  public static async getParticipantTakeoverStatus(conversationId: string): Promise<string | null> {
    try {
      const endpoint = `${this.BASE_PATH}/conversations/${conversationId}/takeover-status`;
      const response = await apiClient.get<{ conversation_id: string; user_id: string; takeover_status: string }>(endpoint);
      
      if (!response || !response.data || typeof response.data.takeover_status !== 'string') {
        return null;
      }
      
      return response.data.takeover_status;
    } catch (error) {
      console.error('获取参与者接管状态失败:', error);
      return null;
    }
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