import { Conversation, Message } from '@/types/chat';

/**
 * 格式化消息内容用于显示
 */
export const formatMessageContent = (content: any): string => {
  if (typeof content === 'string') {
    return content;
  }
  
  if (content && typeof content === 'object' && 'text' in content) {
    return content.text || '';
  }
  
  return JSON.stringify(content);
};

/**
 * 获取会话显示标题
 */
export const getDisplayTitle = (conversation: Conversation): string => {
  if (conversation.title) {
    return conversation.title;
  }
  
  // 如果有参与者名称，使用参与者名称
  if (conversation.first_participant?.name) {
    return conversation.first_participant.name;
  }
  
  // 使用最后一条消息的内容
  if (conversation.lastMessage?.content) {
    const textContent = formatMessageContent(conversation.lastMessage.content);
    return textContent.length > 20 ? textContent.substring(0, 20) + '...' : textContent;
  }
  
  return `会话 ${new Date(conversation.updatedAt).toLocaleDateString()}`;
};

/**
 * 格式化日期显示
 */
export const formatMessageDate = (timestamp: string): string => {
  const date = new Date(timestamp);
  const today = new Date();
  const yesterday = new Date();
  yesterday.setDate(yesterday.getDate() - 1);
  
  if (date.toDateString() === today.toDateString()) {
    return '今天';
  } else if (date.toDateString() === yesterday.toDateString()) {
    return '昨天';
  } else {
    return `${date.getFullYear()}年${date.getMonth() + 1}月${date.getDate()}日`;
  }
};

/**
 * 按日期分组消息
 */
export const groupMessagesByDate = (messages: Message[]) => {
  const groups: { date: string; messages: Message[] }[] = [];
  
  messages.forEach((msg: Message) => {
    const dateStr = formatMessageDate(msg.timestamp);
    
    let group = groups.find(g => g.date === dateStr);
    if (!group) {
      group = { date: dateStr, messages: [] };
      groups.push(group);
    }
    
    group.messages.push(msg);
  });
  
  return groups;
};
