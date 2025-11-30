/**
 * 通讯录与聊天系统的集成服务
 */
import { apiClient } from '@/service/apiClient';
import { ChatDataMapper } from '@/service/chat/mappers';
import type { Conversation } from '@/types/chat';
import type { ConversationApiResponse } from '@/service/chat/types';

/**
 * 与好友发起对话
 */
export async function startConversationWithFriend(friendId: string): Promise<Conversation> {
  // 使用新的API获取或创建与好友的会话
  // 后端返回 ApiResponse<ConversationInfo>，apiClient 解包后得到 ConversationInfo (对应前端 ConversationApiResponse)
  // apiClient 会自动处理错误 Toast，无需在此处 try-catch
  const response = await apiClient.post<ConversationApiResponse>(`/contacts/friends/${friendId}/conversation`);
  return ChatDataMapper.mapConversation(response.data);
}

/**
 * 获取所有好友会话
 */
export async function getFriendConversations(): Promise<Conversation[]> {
  try {
    const response = await apiClient.get<ConversationApiResponse[]>('/contacts/conversations/friends');
    return ChatDataMapper.mapConversations(response.data || []);
  } catch (error) {
    console.error('获取好友会话失败:', error);
    // 返回空数组作为降级处理，apiClient 已显示错误提示
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
