/**
 * 通讯录与聊天系统的集成服务
 */
import { apiClient } from '@/service/apiClient';
import type { Conversation } from '@/types/chat';

/**
 * 与好友发起对话
 */
export async function startConversationWithFriend(friendId: string): Promise<Conversation> {
  try {
    // 使用新的API获取或创建与好友的会话
    const response = await apiClient.post(`/contacts/friends/${friendId}/conversation`);
    return response.data;
  } catch (error) {
    console.error('发起对话失败:', error);
    throw new Error('发起对话失败，请重试');
  }
}

/**
 * 获取所有好友会话
 */
export async function getFriendConversations(): Promise<Conversation[]> {
  try {
    const response = await apiClient.get('/contacts/conversations/friends');
    return response.data;
  } catch (error) {
    console.error('获取好友会话失败:', error);
    return [];
  }
}

/**
 * 从通讯录跳转到聊天页面
 */
export function navigateToChat(friendId: string, conversationId?: string) {
  const url = conversationId 
    ? `/chat?conversationId=${conversationId}`
    : `/chat?friend=${friendId}`;
  
  // 使用window.location进行页面跳转
  window.location.href = url;
}

/**
 * 在新标签页中打开聊天
 */
export function openChatInNewTab(friendId: string, conversationId?: string) {
  const url = conversationId 
    ? `/chat?conversationId=${conversationId}`
    : `/chat?friend=${friendId}`;
  
  window.open(url, '_blank');
}
