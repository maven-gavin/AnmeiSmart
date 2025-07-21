import { MessageData, MessageType, SenderType } from '../types';

/**
 * 消息适配器
 * 负责消息格式转换，确保不同来源的消息能够以统一格式处理
 */
export class MessageAdapter {
  /**
   * 将原始消息转换为标准MessageData格式
   * @param rawMessage 原始消息
   * @returns 标准格式的消息
   */
  public adapt(rawMessage: any): MessageData {
    try {
      // 如果已经是标准格式，直接返回
      if (this.isStandardMessage(rawMessage)) {
        return rawMessage;
      }
      
      // 根据消息类型进行适配
      if (rawMessage.type === 'text' || rawMessage.type === 'image' || rawMessage.type === 'voice') {
        return this.adaptContentMessage(rawMessage);
      } else if (rawMessage.type === 'system') {
        return this.adaptSystemMessage(rawMessage);
      } else if (rawMessage.type === 'connect' || rawMessage.type === 'heartbeat') {
        return this.adaptServiceMessage(rawMessage);
      } else {
        // 未知消息类型，尝试通用适配
        return this.adaptGenericMessage(rawMessage);
      }
    } catch (error) {
      // 如果适配失败，构造一个错误系统消息
      return this.createErrorMessage(error, rawMessage);
    }
  }

  /**
   * 检查消息是否已经是标准格式
   * @param message 要检查的消息
   * @returns 是否为标准格式
   */
  private isStandardMessage(message: any): message is MessageData {
    return (
      message &&
      typeof message === 'object' &&
      typeof message.id === 'string' &&
      typeof message.conversation_id === 'string' &&
      typeof message.type === 'string' &&
      message.sender &&
      typeof message.sender === 'object' &&
      typeof message.sender.id === 'string' &&
      typeof message.sender.type === 'string' &&
      typeof message.timestamp === 'string'
    );
  }

  /**
   * 适配内容消息（文本、图片、语音）
   * @param rawMessage 原始消息
   * @returns 标准格式的内容消息
   */
  private adaptContentMessage(rawMessage: any): MessageData {
    const now = new Date().toISOString();
    
    // 构建基本消息结构
    const message: MessageData = {
      id: rawMessage.id || this.generateId(),
      conversation_id: rawMessage.conversation_id || '',
      content: rawMessage.content || '',
      type: this.getMessageType(rawMessage.type),
      sender: this.getSender(rawMessage.sender),
      timestamp: rawMessage.timestamp || now,
    };
    
    // 添加可选字段 - 支持两种字段名格式
    if (rawMessage.isImportant !== undefined) {
      message.is_important = !!rawMessage.isImportant;
    } else if (rawMessage.is_important !== undefined) {
      message.is_important = !!rawMessage.is_important;
    }
    
    if (rawMessage.metadata) {
      message.metadata = { ...rawMessage.metadata };
    }
    
    return message;
  }

  /**
   * 适配系统消息
   * @param rawMessage 原始消息
   * @returns 标准格式的系统消息
   */
  private adaptSystemMessage(rawMessage: any): MessageData {
    const now = new Date().toISOString();
    
    // 系统消息通常没有发送者，使用默认系统发送者
    return {
      id: rawMessage.id || this.generateId(),
      conversation_id: rawMessage.conversation_id || '',
      content: rawMessage.content || '',
      type: MessageType.SYSTEM,
      sender: {
        id: 'system',
        type: SenderType.SYSTEM,
        name: '系统',
      },
      timestamp: rawMessage.timestamp || now,
      isSystemMessage: true,
      metadata: rawMessage.metadata || {},
    };
  }

  /**
   * 适配服务类消息（连接、心跳）
   * @param rawMessage 原始消息
   * @returns 标准格式的服务消息
   */
  private adaptServiceMessage(rawMessage: any): MessageData {
    const now = new Date().toISOString();
    
    return {
      id: rawMessage.id || this.generateId(),
      conversation_id: rawMessage.conversation_id || '',
      content: rawMessage.content || '',
      type: this.getMessageType(rawMessage.type),
      sender: {
        id: 'system',
        type: SenderType.SYSTEM,
        name: '系统',
      },
      timestamp: rawMessage.timestamp || now,
      isSystemMessage: true,
      metadata: rawMessage.metadata || {
        serviceType: rawMessage.type,
        payload: rawMessage.payload || {},
      },
    };
  }

  /**
   * 通用消息适配，尝试从原始数据中提取必要信息
   * @param rawMessage 原始消息
   * @returns 标准格式的消息
   */
  private adaptGenericMessage(rawMessage: any): MessageData {
    const now = new Date().toISOString();
    
    // 尝试推断消息类型
    const messageType = this.inferMessageType(rawMessage);
    
    // 尝试提取发送者信息
    const sender = this.extractSender(rawMessage);
    
    // 构建标准消息结构
    return {
      id: rawMessage.id || rawMessage.messageId || this.generateId(),
      conversation_id: rawMessage.conversation_id || rawMessage.conversationId || '',
      content: rawMessage.content || rawMessage.message || rawMessage.data || '',
      type: messageType,
      sender: sender,
      timestamp: rawMessage.timestamp || rawMessage.time || rawMessage.date || now,
      metadata: {
        originalMessage: rawMessage,
        adaptedBy: 'generic',
      },
    };
  }

  /**
   * 创建错误消息
   * @param error 错误信息
   * @param originalMessage 原始消息
   * @returns 标准格式的错误消息
   */
  private createErrorMessage(error: any, originalMessage?: any): MessageData {
    const now = new Date().toISOString();
    const errorMessage = error instanceof Error ? error.message : String(error);
    
    return {
      id: this.generateId(),
      conversation_id: originalMessage?.conversation_id || '',
      content: `消息处理错误: ${errorMessage}`,
      type: MessageType.SYSTEM,
      sender: {
        id: 'system',
        type: SenderType.SYSTEM,
        name: '系统',
      },
      timestamp: now,
      isSystemMessage: true,
      metadata: {
        error: errorMessage,
        originalMessage: originalMessage,
      },
    };
  }

  /**
   * 生成唯一ID
   * @returns 唯一ID字符串
   */
  private generateId(): string {
    return `msg_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
  }

  /**
   * 获取消息类型
   * @param type 原始类型
   * @returns 标准消息类型
   */
  private getMessageType(type: string): MessageType {
    // 检查是否是标准类型
    if (Object.values(MessageType).includes(type as MessageType)) {
      return type as MessageType;
    }
    
    // 尝试映射常见类型
    const typeMap: Record<string, MessageType> = {
      'text': MessageType.TEXT,
      'txt': MessageType.TEXT,
      'message': MessageType.TEXT,
      'img': MessageType.IMAGE,
      'image': MessageType.IMAGE,
      'photo': MessageType.IMAGE,
      'audio': MessageType.VOICE,
      'voice': MessageType.VOICE,
      'sound': MessageType.VOICE,
      'sys': MessageType.SYSTEM,
      'system': MessageType.SYSTEM,
      'notice': MessageType.SYSTEM,
      'conn': MessageType.CONNECT,
      'connect': MessageType.CONNECT,
      'connection': MessageType.CONNECT,
      'beat': MessageType.HEARTBEAT,
      'heartbeat': MessageType.HEARTBEAT,
      'ping': MessageType.HEARTBEAT,
      'cmd': MessageType.COMMAND,
      'command': MessageType.COMMAND,
    };
    
    // 返回映射类型或默认为文本
    return typeMap[type.toLowerCase()] || MessageType.TEXT;
  }

  /**
   * 从原始消息中推断消息类型
   * @param rawMessage 原始消息
   * @returns 推断的消息类型
   */
  private inferMessageType(rawMessage: any): MessageType {
    // 如果有明确的type字段
    if (rawMessage.type) {
      return this.getMessageType(rawMessage.type);
    }
    
    // 根据content内容推断
    if (rawMessage.content) {
      if (typeof rawMessage.content === 'string') {
        // 检查是否是图片URL
        if (rawMessage.content.match(/\.(jpg|jpeg|png|gif|webp)(\?.*)?$/i)) {
          return MessageType.IMAGE;
        }
        
        // 检查是否是语音URL
        if (rawMessage.content.match(/\.(mp3|wav|ogg|m4a)(\?.*)?$/i)) {
          return MessageType.VOICE;
        }
        
        // 默认为文本
        return MessageType.TEXT;
      }
    }
    
    // 如果有messageType字段
    if (rawMessage.messageType) {
      return this.getMessageType(rawMessage.messageType);
    }
    
    // 默认为文本类型
    return MessageType.TEXT;
  }

  /**
   * 获取标准格式的发送者信息
   * @param senderInfo 原始发送者信息
   * @returns 标准格式的发送者
   */
  private getSender(senderInfo: any): MessageData['sender'] {
    // 如果没有发送者信息，返回默认未知发送者
    if (!senderInfo) {
      return {
        id: 'unknown',
        type: SenderType.SYSTEM,
        name: '未知发送者',
      };
    }
    
    // 如果已经是标准格式，直接返回
    if (
      typeof senderInfo === 'object' &&
      typeof senderInfo.id === 'string' &&
      typeof senderInfo.type === 'string'
    ) {
      return {
        id: senderInfo.id,
        type: this.getSenderType(senderInfo.type),
        name: senderInfo.name || undefined,
        avatar: senderInfo.avatar || undefined,
      };
    }
    
    // 如果是简单字符串，尝试解析为ID或类型
    if (typeof senderInfo === 'string') {
      // 尝试作为类型解析
      const type = this.getSenderType(senderInfo);
      
      return {
        id: senderInfo,
        type: type,
        name: this.getDefaultNameForType(type),
      };
    }
    
    // 尝试从对象中提取信息
    return {
      id: senderInfo.id || senderInfo.userId || senderInfo.user_id || 'unknown',
      type: this.getSenderType(senderInfo.type || senderInfo.role),
      name: senderInfo.name || senderInfo.userName || senderInfo.nickname || undefined,
      avatar: senderInfo.avatar || senderInfo.avatarUrl || undefined,
    };
  }

  /**
   * 提取发送者信息
   * @param rawMessage 原始消息
   * @returns 标准格式的发送者
   */
  private extractSender(rawMessage: any): MessageData['sender'] {
    // 首先检查sender字段
    if (rawMessage.sender) {
      return this.getSender(rawMessage.sender);
    }
    
    // 检查user字段
    if (rawMessage.user) {
      return this.getSender(rawMessage.user);
    }
    
    // 检查from字段
    if (rawMessage.from) {
      return this.getSender(rawMessage.from);
    }
    
    // 尝试从分散的字段中组合信息
    if (rawMessage.userId || rawMessage.user_id || rawMessage.senderId || rawMessage.sender_id) {
      return {
        id: rawMessage.userId || rawMessage.user_id || rawMessage.senderId || rawMessage.sender_id,
        type: this.getSenderType(rawMessage.userType || rawMessage.user_type || rawMessage.senderType || rawMessage.sender_type),
        name: rawMessage.userName || rawMessage.user_name || rawMessage.senderName || rawMessage.sender_name || undefined,
        avatar: rawMessage.userAvatar || rawMessage.user_avatar || rawMessage.senderAvatar || rawMessage.sender_avatar || undefined,
      };
    }
    
    // 默认为系统发送者
    return {
      id: 'system',
      type: SenderType.SYSTEM,
      name: '系统',
    };
  }

  /**
   * 获取标准格式的发送者类型
   * @param type 原始类型
   * @returns 标准发送者类型
   */
  private getSenderType(type: string): SenderType {
    // 检查是否是标准类型
    if (Object.values(SenderType).includes(type as SenderType)) {
      return type as SenderType;
    }
    
    // 尝试映射常见类型
    const typeMap: Record<string, SenderType> = {
      'user': SenderType.USER,
      'customer': SenderType.CUSTOMER,
      'client': SenderType.CUSTOMER,
      'consultant': SenderType.CONSULTANT,
      'advisor': SenderType.CONSULTANT,
      'doctor': SenderType.DOCTOR,
      'physician': SenderType.DOCTOR,
      'ai': SenderType.AI,
      'bot': SenderType.AI,
      'assistant': SenderType.AI,
      'system': SenderType.SYSTEM,
      'sys': SenderType.SYSTEM,
    };
    
    // 返回映射类型或默认为用户
    return type ? (typeMap[type.toLowerCase()] || SenderType.USER) : SenderType.USER;
  }

  /**
   * 获取发送者类型的默认名称
   * @param type 发送者类型
   * @returns 默认名称
   */
  private getDefaultNameForType(type: SenderType): string {
    const nameMap: Record<SenderType, string> = {
      [SenderType.USER]: '用户',
      [SenderType.CUSTOMER]: '客户',
      [SenderType.CONSULTANT]: '顾问',
      [SenderType.DOCTOR]: '医生',
      [SenderType.AI]: 'AI助手',
      [SenderType.SYSTEM]: '系统',
    };
    
    return nameMap[type] || '未知';
  }
} 