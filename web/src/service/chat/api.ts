/**
 * 聊天API服务模块
 * 统一管理聊天相关的后端API调用
 */

import { apiClient } from '../apiClient';
import { 
  Message, 
  MessageContent, 
  Conversation, 
  SenderType, 
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
    
    const response = await apiClient.post<MessageApiResponse>(
      `${this.BASE_PATH}/conversations/${message.conversationId}/messages`, 
      requestData
    );
    
    if (!response.data) {
      throw new Error('保存消息失败：响应数据为空');
    }
    
    return this.formatMessage(response.data);
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
    // 处理消息内容：确保content是结构化格式
    let formattedContent: MessageContent;
    let messageType: 'text' | 'media' | 'system' | 'structured';

    // 处理type字段，支持新旧格式
    const rawType = msg.type || 'text';
    if (rawType === 'media' || rawType === 'image' || rawType === 'voice' || rawType === 'file') {
      messageType = 'media';
    } else if (rawType === 'text') {
      messageType = 'text';
    } else if (rawType === 'system') {
      messageType = 'system';
    } else if (rawType === 'structured') {
      messageType = 'structured';
    } else {
      messageType = 'text'; // 默认为text
    }

    // 处理消息内容
    if (typeof msg.content === 'string') {
      // 旧格式：字符串内容，转换为新的结构化格式
      if (messageType === 'media') {
        // 媒体消息：尝试从URL推断媒体类型
        const mimeType = this.inferMimeTypeFromUrl(msg.content);
        formattedContent = {
          text: '',
          media_info: {
            url: msg.content,
            name: this.getFileNameFromUrl(msg.content),
            mime_type: mimeType,
            size_bytes: 0,
            metadata: {}
          }
        };
      } else {
        // 文本消息
        formattedContent = { text: msg.content };
      }
    } else if (typeof msg.content === 'object' && msg.content !== null) {
      // 新格式：已经是结构化内容
      formattedContent = msg.content as MessageContent;
    } else {
      // 异常情况：使用默认文本内容
      formattedContent = { text: '' };
    }

    return {
      id: msg.id,
      conversationId: msg.conversation_id || '',
      content: formattedContent,
      type: messageType,
      sender: {
        id: msg.sender?.id || msg.sender_id || '',
        name: msg.sender?.name || msg.sender_name || '未知',
        avatar: msg.sender?.avatar || msg.sender_avatar || 
               (msg.sender?.type === 'ai' || msg.sender_type === 'ai' ? AI_INFO.avatar : '/avatars/user.png'),
        type: (msg.sender?.type || msg.sender_type || 'user') as SenderType,
      },
      timestamp: msg.timestamp || msg.created_at || new Date().toISOString(),
      is_important: msg.is_important || false,
      is_read: msg.is_read || false,
      reply_to_message_id: msg.reply_to_message_id || undefined,
      reactions: msg.reactions || undefined,
      extra_metadata: msg.extra_metadata || undefined
    };
  }

  // 辅助方法：从URL推断MIME类型
  private static inferMimeTypeFromUrl(url: string): string {
    const ext = url.split('.').pop()?.toLowerCase();
    switch (ext) {
      case 'jpg':
      case 'jpeg':
        return 'image/jpeg';
      case 'png':
        return 'image/png';
      case 'gif':
        return 'image/gif';
      case 'webp':
        return 'image/webp';
      case 'mp3':
        return 'audio/mpeg';
      case 'wav':
        return 'audio/wav';
      case 'ogg':
        return 'audio/ogg';
      case 'm4a':
        return 'audio/m4a';
      case 'mp4':
        return 'video/mp4';
      case 'webm':
        return 'video/webm';
      case 'pdf':
        return 'application/pdf';
      case 'txt':
        return 'text/plain';
      default:
        return 'application/octet-stream';
    }
  }

  // 辅助方法：从URL获取文件名
  private static getFileNameFromUrl(url: string): string {
    try {
      const urlObj = new URL(url);
      const pathname = urlObj.pathname;
      const fileName = pathname.split('/').pop();
      return fileName || 'unknown_file';
    } catch {
      return 'unknown_file';
    }
  }
} 