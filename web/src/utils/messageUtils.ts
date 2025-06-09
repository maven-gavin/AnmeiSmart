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