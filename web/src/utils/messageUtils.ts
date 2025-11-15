/**
 * 消息相关工具函数
 */

/**
 * 生成消息ID
 */
export function generateMessageId(): string {
  return `msg_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
}

/**
 * 生成本地消息ID
 */
export function generateLocalId(): string {
  return `local_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
}

/**
 * 判断是否为本地消息
 */
export function isLocalMessage(messageId: string): boolean {
  return messageId.startsWith('local_');
}

/**
 * 格式化消息时间
 */
export function formatMessageTime(timestamp: string): string {
  try {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMinutes = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMinutes / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMinutes < 1) {
      return '刚刚';
    } else if (diffMinutes < 60) {
      return `${diffMinutes}分钟前`;
    } else if (diffHours < 24) {
      return `${diffHours}小时前`;
    } else if (diffDays < 7) {
      return `${diffDays}天前`;
    } else {
      return date.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: 'numeric',
        day: 'numeric'
      });
    }
  } catch (error) {
    console.error('格式化消息时间失败:', error);
    return '未知时间';
  }
}

/**
 * 提取消息内容摘要
 */
export function extractMessageSummary(content: string, maxLength: number = 50): string {
  if (!content) return '';
  
  // 如果是JSON内容（文件消息），尝试解析
  try {
    const parsed = JSON.parse(content);
    if (parsed.file_name) {
      return `📎 ${parsed.file_name}`;
    }
  } catch {
    // 不是JSON，按普通文本处理
  }

  // 移除多余的空白字符
  const cleaned = content.replace(/\s+/g, ' ').trim();
  
  if (cleaned.length <= maxLength) {
    return cleaned;
  }
  
  return cleaned.substring(0, maxLength) + '...';
}

/**
 * 验证消息内容
 */
export function validateMessageContent(content: string, type: 'text' | 'image' | 'voice' | 'file'): {
  valid: boolean;
  error?: string;
} {
  if (!content || content.trim() === '') {
    return {
      valid: false,
      error: '消息内容不能为空'
    };
  }

  // 文本消息长度限制
  if (type === 'text' && content.length > 5000) {
    return {
      valid: false,
      error: '文本消息长度不能超过5000字符'
    };
  }

  // 文件消息需要是有效的JSON
  if (type === 'file') {
    try {
      const parsed = JSON.parse(content);
      if (!parsed.file_url || !parsed.file_name) {
        return {
          valid: false,
          error: '文件消息格式无效'
        };
      }
    } catch {
      return {
        valid: false,
        error: '文件消息格式无效'
      };
    }
  }

  return { valid: true };
}

/**
 * 检查消息是否可以撤销（发送后1分钟内）
 */
export function canRecallMessage(messageTimestamp: string): boolean {
  try {
    const messageTime = new Date(messageTimestamp);
    const now = new Date();
    const diffMs = now.getTime() - messageTime.getTime();
    const diffMinutes = diffMs / (1000 * 60);
    
    return diffMinutes <= 1; // 1分钟内可撤销
  } catch {
    return false;
  }
}

/**
 * 生成消息排序键
 */
export function getMessageSortKey(timestamp: string, id: string): string {
  try {
    const date = new Date(timestamp);
    const timeMs = date.getTime();
    return `${timeMs}_${id}`;
  } catch {
    // 如果时间格式无效，使用ID
    return `0_${id}`;
  }
}

import { 
  Message, 
  MessageContent, 
  MediaInfo, 
  TextMessageContent, 
  MediaMessageContent, 
  SystemEventContent,
  StructuredMessageContent,
  CreateTextMessageData,
  CreateMediaMessageData,
  CreateSystemEventData,
  CardComponent
} from '@/types/chat';

/**
 * 消息工具类 - 提供处理新旧消息格式的便利方法
 */
export class MessageUtils {
  /**
   * 获取消息的文本内容
   */
  static getTextContent(message: Message): string | null {
    switch (message.type) {
      case 'text':
        return (message.content as TextMessageContent).text;
      case 'media':
        return (message.content as MediaMessageContent).text || null;
      case 'system':
        const systemContent = message.content as SystemEventContent;
        return MessageUtils.formatSystemEventText(systemContent);
      case 'structured':
        const structuredContent = message.content as StructuredMessageContent;
        return structuredContent.title;
      default:
        return null;
    }
  }

  /**
   * 获取消息的媒体信息
   */
  static getMediaInfo(message: Message): MediaInfo | null {
    if (message.type === 'media') {
      return (message.content as MediaMessageContent).media_info;
    }
    return null;
  }

  /**
   * 获取结构化消息的卡片数据
   */
  static getStructuredCardData(message: Message): any | null {
    if (message.type === 'structured') {
      return (message.content as StructuredMessageContent).data;
    }
    return null;
  }

  /**
   * 判断是否为文本消息
   */
  static isTextMessage(message: Message): boolean {
    return message.type === 'text';
  }

  /**
   * 判断是否为媒体消息
   */
  static isMediaMessage(message: Message): boolean {
    return message.type === 'media';
  }

  /**
   * 判断是否为系统消息
   */
  static isSystemMessage(message: Message): boolean {
    return message.type === 'system';
  }

  /**
   * 判断是否为结构化消息（卡片）
   */
  static isStructuredMessage(message: Message): boolean {
    return message.type === 'structured';
  }


  /**
   * 格式化系统事件为可读文本
   */
  static formatSystemEventText(content: SystemEventContent): string {
    const { system_event_type, status, participants } = content;
    
    switch (system_event_type) {
      case 'user_joined':
        return '用户加入了会话';
      case 'user_left':
        return '用户离开了会话';
      case 'takeover':
        return status === 'completed' ? '专家已接管会话' : '正在转接专家...';
      case 'release':
        return '会话已转回AI助手';
      case 'video_call_status':
        if (status === 'ended' && content.duration_seconds) {
          const duration = MessageUtils.formatDuration(content.duration_seconds);
          return `通话结束，时长 ${duration}`;
        }
        return `视频通话${status === 'initiated' ? '发起' : status}`;
      default:
        return '系统消息';
    }
  }

  /**
   * 获取消息的显示文本（用于会话列表等）
   */
  static getDisplayText(message: Message): string {
    switch (message.type) {
      case 'text':
        return (message.content as TextMessageContent).text;
      case 'media':
        const mediaContent = message.content as MediaMessageContent;
        const mediaType = MessageUtils.getMediaType(mediaContent.media_info.mime_type);
        return mediaContent.text || `[${mediaType}]`;
      case 'system':
        return MessageUtils.formatSystemEventText(message.content as SystemEventContent);
      case 'structured':
        const structuredContent = message.content as StructuredMessageContent;
        return `[${MessageUtils.getCardTypeDisplayName(structuredContent.card_type)}] ${structuredContent.title}`;
      default:
        return '未知消息类型';
    }
  }

  /**
   * 获取卡片类型的显示名称
   */
  static getCardTypeDisplayName(cardType: string): string {
    switch (cardType) {
      case 'service_recommendation':
        return '服务推荐';
      case 'consultation_summary':
        return '咨询总结';
      default:
        return '卡片';
    }
  }

  /**
   * 获取媒体类型
   */
  static getMediaType(mimeType: string): string {
    if (mimeType.startsWith('image/')) return '图片';
    if (mimeType.startsWith('video/')) return '视频';
    if (mimeType.startsWith('audio/')) return '语音';
    if (mimeType.includes('pdf')) return 'PDF';
    if (mimeType.includes('word') || mimeType.includes('document')) return '文档';
    if (mimeType.includes('excel') || mimeType.includes('spreadsheet')) return '表格';
    return '文件';
  }

  /**
   * 格式化文件大小
   */
  static formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  }

  /**
   * 格式化时长（秒 -> 分:秒）
   */
  static formatDuration(seconds: number): string {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  }

  /**
   * 创建文本消息内容
   */
  static createTextMessageContent(text: string): TextMessageContent {
    return { text };
  }

  /**
   * 创建媒体消息内容
   */
  static createMediaMessageContent(
    mediaInfo: MediaInfo, 
    text?: string
  ): MediaMessageContent {
    return {
      media_info: mediaInfo,
      text
    };
  }

  /**
   * 创建系统事件内容
   */
  static createSystemEventContent(
    eventType: string,
    data?: { [key: string]: any }
  ): SystemEventContent {
    return {
      system_event_type: eventType,
      ...data
    };
  }


  /**
   * 创建服务推荐卡片内容
   */
  static createServiceRecommendationContent(
    services: any[],
    title: string = '推荐服务'
  ): StructuredMessageContent {
    return {
      card_type: 'service_recommendation',
      title,
      data: { services },
      actions: {
        primary: { text: '查看详情', action: 'view_services' }
      }
    };
  }
}

// 导出便利函数
export const {
  getTextContent,
  getMediaInfo,
  isTextMessage,
  isMediaMessage,
  isSystemMessage,
  isStructuredMessage,
  getDisplayText,
  getStructuredCardData,
  getCardTypeDisplayName,
  getMediaType,
  formatFileSize,
  formatDuration,
  createTextMessageContent,
  createMediaMessageContent,
  createSystemEventContent,
  createServiceRecommendationContent
} = MessageUtils; 