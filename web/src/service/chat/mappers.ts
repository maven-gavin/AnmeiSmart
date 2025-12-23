/**
 * 聊天模块数据映射工具
 * 负责API响应数据与前端类型的转换
 */

import { Conversation, Message, User } from '@/types/chat';
import {
  ConversationApiResponse,
  MessageApiResponse,
  ConversationParticipantApiResponse,
  ConversationParticipant,
} from './types';

/**
 * 数据映射工具类
 * 提供类型安全的数据转换方法
 */
export class ChatDataMapper {
  
  /**
   * 将API响应转换为Conversation类型
   */
  static mapConversation(apiResponse: ConversationApiResponse): Conversation {
    return {
      id: apiResponse.id,
      title: apiResponse.title,
      chat_mode: apiResponse.chat_mode,
      tag: apiResponse.tag,
      owner_id: apiResponse.owner_id,
      owner: apiResponse.owner ? this.mapUser(apiResponse.owner) : undefined,
      // first_participant_id 和 first_participant 字段已移除
      lastMessage: apiResponse.last_message ? this.mapMessage(apiResponse.last_message) : undefined,
      unreadCount: apiResponse.unread_count || 0,
      messageCount: apiResponse.message_count || 0,
      lastMessageAt: apiResponse.last_message_at,
      updatedAt: apiResponse.updated_at,
      createdAt: apiResponse.created_at,
      isActive: apiResponse.is_active,
      isArchived: apiResponse.is_archived,
      is_pinned: apiResponse.is_pinned || false,
      pinned_at: apiResponse.pinned_at,
      extra_metadata: apiResponse.extra_metadata
    };
  }

  /**
   * 将API响应转换为Message类型
   */
  static mapMessage(apiResponse: MessageApiResponse): Message {
    return {
      id: apiResponse.id,
      conversationId: apiResponse.conversation_id || '',
      content: this.mapMessageContent(apiResponse.content, apiResponse.type),
      type: this.mapMessageType(apiResponse.type),
      sender: this.mapSender(apiResponse),
      timestamp: apiResponse.timestamp || apiResponse.created_at || new Date().toISOString(),
      is_read: apiResponse.is_read,
      is_important: apiResponse.is_important,
      reply_to_message_id: apiResponse.reply_to_message_id,
      reactions: apiResponse.reactions,
      extra_metadata: apiResponse.extra_metadata
    };
  }

  /**
   * 将API响应转换为User类型
   */
  static mapUser(apiUser: { id: string; username?: string; email?: string; avatar?: string }): User {
    return {
      id: apiUser.id,
      name: apiUser.username || '未知用户',
      avatar: apiUser.avatar || '/avatars/user.png',
      tags: [] // 后端API中没有tags字段，如果需要可以从其他地方获取
    };
  }

  /**
   * 映射消息内容
   */
  private static mapMessageContent(content: any, type?: string): any {
    if (!content) return { text: '' };
    
    // 如果已经是对象格式，直接返回
    if (typeof content === 'object' && content !== null) {
      return content;
    }
    
    // 如果是字符串，转换为文本消息格式
    if (typeof content === 'string') {
      return { text: content };
    }
    
    // 默认返回空文本
    return { text: '' };
  }

  /**
   * 映射消息类型
   */
  private static mapMessageType(type?: string): 'text' | 'media' | 'system' | 'structured' {
    switch (type) {
      case 'text': return 'text';
      case 'media': return 'media';
      case 'system': return 'system';
      case 'structured': return 'structured';
      default: return 'text';
    }
  }

  /**
   * 映射发送者信息
   */
  private static mapSender(apiResponse: MessageApiResponse): Message['sender'] {
    // 优先使用sender对象
    if (apiResponse.sender) {
      return {
        id: apiResponse.sender.id,
        type: (apiResponse.sender.type as any) || 'user',
        name: apiResponse.sender.name || '未知用户',
        avatar: apiResponse.sender.avatar || '/avatars/user.png'
      };
    }
    
    // 回退到单独的字段
    return {
      id: apiResponse.sender_id || 'unknown',
      // 后端 sender_type 旧值为 chat/system，这里统一映射到 user/system，
      // 未来如果引入 AI 侧主动发消息，可直接返回 'ai'
      type: (apiResponse.sender_type as any) === 'system' ? 'system' : 'user',
      name: apiResponse.sender_name || '未知用户',
      avatar: apiResponse.sender_avatar || '/avatars/user.png'
    };
  }

  /**
   * 批量映射会话列表
   */
  static mapConversations(apiResponses: ConversationApiResponse[]): Conversation[] {
    return apiResponses.map(response => this.mapConversation(response));
  }

  /**
   * 批量映射消息列表
   */
  static mapMessages(apiResponses: MessageApiResponse[]): Message[] {
    return apiResponses.map(response => this.mapMessage(response));
  }

  /**
   * 将API响应转换为 ConversationParticipant 类型
   */
  static mapConversationParticipant(
    apiParticipant: ConversationParticipantApiResponse
  ): ConversationParticipant {
    return {
      id: apiParticipant.id,
      conversationId: apiParticipant.conversation_id,
      userId: apiParticipant.user_id,
      userName: apiParticipant.user_name,
      userAvatar: apiParticipant.user_avatar || '/avatars/user.png',
      role: apiParticipant.role,
      takeoverStatus: apiParticipant.takeover_status || 'no_takeover',
      isActive: apiParticipant.is_active,
    };
  }

  /**
   * 批量映射会话参与者列表
   */
  static mapConversationParticipants(
    apiParticipants: ConversationParticipantApiResponse[]
  ): ConversationParticipant[] {
    return apiParticipants.map(p => this.mapConversationParticipant(p));
  }
}
