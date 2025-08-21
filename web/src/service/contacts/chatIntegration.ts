/**
 * 通讯录与聊天系统的集成服务
 */
import { createConversation } from '@/service/chatService';
import { ChatApiService } from '@/service/chat/api';
import type { Conversation } from '@/types/chat';

/**
 * 与好友发起对话
 */
export async function startConversationWithFriend(friendId: string): Promise<Conversation> {
  try {
    // 检查是否已有与该好友的对话
    const existingConversation = await findExistingConversationWithFriend(friendId);
    
    if (existingConversation) {
      // 如果已有对话，直接返回
      return existingConversation;
    }
    
    // 创建新的对话
    const conversation = await createConversation(friendId);
    
    return conversation;
  } catch (error) {
    console.error('发起对话失败:', error);
    throw new Error('发起对话失败，请重试');
  }
}

/**
 * 查找与好友的现有对话
 */
async function findExistingConversationWithFriend(friendId: string): Promise<Conversation | null> {
  try {
    // TODO: 实现查找与特定好友的对话逻辑
    // 这需要后端支持根据参与者查询对话的API
    
    // 暂时返回null，总是创建新对话
    return null;
  } catch (error) {
    console.error('查找现有对话失败:', error);
    return null;
  }
}

/**
 * 从通讯录跳转到聊天页面
 */
export function navigateToChat(friendId: string, conversationId?: string) {
  const url = conversationId 
    ? `/chat?conversation=${conversationId}`
    : `/chat?friend=${friendId}`;
  
  // 使用window.location进行页面跳转
  window.location.href = url;
}

/**
 * 在新标签页中打开聊天
 */
export function openChatInNewTab(friendId: string, conversationId?: string) {
  const url = conversationId 
    ? `/chat?conversation=${conversationId}`
    : `/chat?friend=${friendId}`;
  
  window.open(url, '_blank');
}
