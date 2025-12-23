/**
 * 聊天服务协调器
 * 重构后的轻量级聊天服务，协调各模块间的交互
 * 保持向后兼容性，确保现有代码不会中断
 */

import { authService } from "./authService";
import { ApiClientError, ErrorType } from './apiClient';

// 导入重构后的模块
import {
  chatState,
  ChatApiService,
  type Message,
  type Conversation,
  type CustomerProfile,
  type Customer,
  type ConsultationHistoryItem,
  type ConversationParticipant,
  type ConversationParticipantRole,
} from './chat';

/**
 * 保存消息
 * @param message 消息
 * @returns 保存后的消息
 */
export async function saveMessage(message: Message): Promise<Message> {
  try {
    // 验证必要字段
    if (!message.conversationId) {
      throw new ApiClientError('消息缺少会话ID', {
        status: 400,
        type: ErrorType.VALIDATION,
      })
    }

    if (!message.content) {
      throw new ApiClientError('消息内容不能为空', {
        status: 400,
        type: ErrorType.VALIDATION,
      })
    }

    // 调用API保存消息
    const savedMessage = await ChatApiService.saveMessage(message);

    // 更新本地缓存
    if (savedMessage.conversationId) {
      chatState.addMessage(savedMessage.conversationId, savedMessage);
      // 同时更新会话的最后一条消息
      chatState.updateConversationLastMessage(savedMessage.conversationId, savedMessage);
    }

    return savedMessage;
  } catch (error) {
    console.error('保存消息失败:', error);
    
    // 如果是认证错误，抛出
    if (error instanceof ApiClientError && error.type === ErrorType.AUTHENTICATION) {
      throw error;
    }
    
    // 其他错误包装后抛出
    const errorMessage = error instanceof Error ? error.message : '保存消息失败';
    throw new ApiClientError(errorMessage, {
      status: 500,
      type: ErrorType.NETWORK,
    })
  }
}

/**
 * 同步聊天数据
 */
export async function syncChatData(conversationId: string): Promise<void> {
  try {
    // 重新获取会话数据和消息数据
    await Promise.all([
      getConversations(),
      getConversationMessages(conversationId)
    ]);
  } catch (error) {
    console.error('会话数据同步出错:', error);
  }
}

// ===== 会话和消息数据管理 =====

/**
 * 获取会话消息
 */
export async function getConversationMessages(conversationId: string, forceRefresh: boolean = false): Promise<Message[]> {
  // 获取缓存的消息
  const cachedMessages = chatState.getChatMessages(conversationId);
  
  // 检查是否有未完成的请求
  if (chatState.isRequestingMessagesForConversation(conversationId)) {
    return cachedMessages;
  }
  
  // 检查缓存是否有效
  if (!forceRefresh && cachedMessages.length > 0 && chatState.isMessagesCacheValid(conversationId)) {
    return cachedMessages;
  }
  
  try {
    // 设置请求标志
    chatState.setRequestingMessages(conversationId, true);
    
    // 使用API服务获取消息
    const messages = await ChatApiService.getConversationMessages(conversationId);
    
    // 如果返回的消息为空，且缓存有数据，使用缓存
    if (messages.length === 0 && cachedMessages.length > 0) {
      return cachedMessages;
    }
    
    // 更新本地缓存
    if (messages.length > 0) {
      chatState.setChatMessages(conversationId, messages);
      chatState.updateMessagesRequestTime(conversationId);
    }
    
    return messages;
  } catch (error) {
    console.error('获取会话消息出错:', error);
    
    // 如果是认证错误，抛出异常
    if (error instanceof ApiClientError && error.type === ErrorType.AUTHENTICATION) {
      throw error;
    }
    
    // 其他错误时返回缓存数据
    return cachedMessages;
  } finally {
    // 重置请求标志
    chatState.setRequestingMessages(conversationId, false);
  }
}

/**
 * 获取所有会话
 */
export async function getConversations(unassignedOnly: boolean = false): Promise<Conversation[]> {
  // 检查是否已有请求正在进行
  if (chatState.isRequestingConversationsState()) {
    return chatState.getConversations();
  }
  
  // 只有在非未分配过滤时才使用缓存
  if (!unassignedOnly) {
    const conversations = chatState.getConversations();
    if (conversations.length > 0 && chatState.isConversationsCacheValid()) {
      return conversations;
    }
  }
  
  try {
    // 设置请求标志
    chatState.setRequestingConversations(true);
    
    // 使用API服务获取会话列表
    const formattedConversations = await ChatApiService.getConversations(unassignedOnly);
    
    // 只有在非未分配过滤时才更新本地通用缓存
    if (!unassignedOnly) {
      chatState.setConversations(formattedConversations);
      chatState.updateConversationsRequestTime();
    }
    
    return formattedConversations;
  } catch (error) {
    console.error('获取会话列表出错:', error);
    
    // 如果是认证错误，抛出异常
    if (error instanceof ApiClientError && error.type === ErrorType.AUTHENTICATION) {
      throw error;
    }
    
    // 其他错误返回缓存数据
    return chatState.getConversations();
  } finally {
    // 重置请求标志
    chatState.setRequestingConversations(false);
  }
}

/**
 * 标记会话为已读
 */
export async function markConversationAsRead(conversationId: string): Promise<void> {
  try {
    // 1. 乐观更新本地缓存
    chatState.updateConversationUnreadCount(conversationId, 0);
    
    // 2. 调用 API
    await ChatApiService.markConversationAsRead(conversationId);
  } catch (error) {
    console.error('标记会话已读失败:', error);
    // 如果 API 失败，可能需要回滚，但为了用户体验通常不回滚已读状态
    throw error;
  }
}

export async function updateUnreadCountInCache(conversationId: string, increment: number): Promise<void> {
  const conversations = chatState.getConversations();
  const index = conversations.findIndex(c => c.id === conversationId);
  if (index !== -1) {
    const currentCount = conversations[index].unreadCount || 0;
    chatState.updateConversationUnreadCount(conversationId, currentCount + increment);
  }
}

export async function updateLastMessageInCache(conversationId: string, message: any): Promise<void> {
  chatState.updateConversationLastMessage(conversationId, message);
}


/**
 * 标记消息为重点
 */
export async function markMessageAsImportant(conversationId: string, messageId: string, isImportant: boolean): Promise<Message | null> {
  const messages = chatState.getChatMessages(conversationId);
  if (!messages.length) return null;
  
  try {
    // 找到对应的消息
    const messageIndex = messages.findIndex(msg => msg.id === messageId);
    if (messageIndex < 0) return null;
    
    // 更新本地状态
    const updatedMessage = {
      ...messages[messageIndex],
      is_important: isImportant,
    };
    
    // 更新本地消息
    messages[messageIndex] = updatedMessage;
    chatState.setChatMessages(conversationId, messages);
    
    // 尝试同步到服务器
    try {
      await ChatApiService.markMessageAsImportant(conversationId, messageId, isImportant);
    } catch (error) {
      console.error('更新重点消息状态到服务器失败:', error);
      // 仅本地更新，不影响用户体验
    }
    
    return updatedMessage;
  } catch (error) {
    console.error('标记重点消息失败:', error);
    return null;
  }
}

/**
 * 获取重点消息
 */
export function getImportantMessages(conversationId: string): Message[] {
  const messages = chatState.getChatMessages(conversationId);
  return messages.filter(msg => msg.is_important);
}

// ===== 会话参与者管理 =====

/**
 * 获取会话参与者列表
 */
export async function getConversationParticipants(
  conversationId: string
): Promise<ConversationParticipant[]> {
  try {
    return await ChatApiService.getConversationParticipants(conversationId);
  } catch (error) {
    console.error('获取会话参与者失败:', error);
    return [];
  }
}

/**
 * 添加会话参与者
 */
export async function addConversationParticipant(
  conversationId: string,
  userId: string,
  role: ConversationParticipantRole = 'member'
): Promise<ConversationParticipant | null> {
  try {
    return await ChatApiService.addConversationParticipant(conversationId, userId, role);
  } catch (error) {
    console.error('添加会话参与者失败:', error);
    return null;
  }
}

/**
 * 移除会话参与者
 */
export async function removeConversationParticipant(
  conversationId: string,
  participantId: string
): Promise<void> {
  try {
    await ChatApiService.removeConversationParticipant(conversationId, participantId);
  } catch (error) {
    console.error('移除会话参与者失败:', error);
    throw error;
  }
}

// ===== 客户档案和历史记录 =====

/**
 * 获取客户档案
 */
export async function getCustomerProfile(customerId: string): Promise<CustomerProfile | null> {
  try {
    return await ChatApiService.getCustomerProfile(customerId);
  } catch (error) {
    console.error('获取客户档案出错:', error);
    return null;
  }
}

/**
 * 获取客户历史咨询记录
 */
export async function getCustomerConsultationHistory(customerId: string): Promise<ConsultationHistoryItem[]> {
  try {
    // 获取客户的所有会话
    const conversations = await ChatApiService.getCustomerConversations(customerId);
    
    if (!conversations || conversations.length === 0) {
      return [];
    }
    
    // 转换为咨询历史记录格式
    const history = conversations.map(conversation => ({
      id: conversation.id,
      date: new Date(conversation.updatedAt).toLocaleDateString('zh-CN'),
      type: conversation.tag === 'consultation' ? '咨询会话' : '一般会话',
      description: conversation.title || '无咨询总结'
    }));
    
    // 按日期降序排序（最新的在前）
    return history.sort((a, b) => 
      new Date(b.date).getTime() - new Date(a.date).getTime()
    );
  } catch (error) {
    console.error('获取客户咨询历史出错:', error);
    return [];
  }
}

// ===== 接管状态管理 =====

/**
 * 设置接管状态（支持三种状态）
 */
export async function setTakeoverStatus(
  conversationId: string,
  status: 'full_takeover' | 'semi_takeover' | 'no_takeover'
): Promise<boolean> {
  try {
    console.log('setTakeoverStatus 调用:', { conversationId, status });
    
    // 发送接管状态到后端
    const result = await ChatApiService.setTakeoverStatus(conversationId, status);
    
    console.log('setTakeoverStatus 响应:', result);
    
    // 检查响应数据
    if (!result || typeof result.takeover_status !== 'string') {
      console.error('设置接管状态失败: 响应数据格式不正确', result);
      return false;
    }
    
    // 更新本地状态
    const isTakeover = result.takeover_status === 'full_takeover';
    chatState.setConsultantTakeover(conversationId, isTakeover);
    
    return true;
  } catch (error) {
    console.error('设置接管状态失败:', error);
    // 输出更详细的错误信息
    if (error instanceof Error) {
      console.error('错误详情:', {
        message: error.message,
        stack: error.stack,
        name: error.name
      });
    } else {
      console.error('错误对象:', JSON.stringify(error, null, 2));
    }
    return false;
  }
}

/**
 * 获取当前用户的接管状态
 */
export async function getTakeoverStatus(conversationId: string): Promise<'full_takeover' | 'semi_takeover' | 'no_takeover'> {
  try {
    // 尝试从后端获取当前用户的接管状态
    const status = await ChatApiService.getParticipantTakeoverStatus(conversationId);
    
    if (status !== null && ['full_takeover', 'semi_takeover', 'no_takeover'].includes(status)) {
      // 更新本地状态
      const isTakeover = status === 'full_takeover';
      chatState.setConsultantTakeover(conversationId, isTakeover);
      return status as 'full_takeover' | 'semi_takeover' | 'no_takeover';
    }
    
    // 如果无法获取状态，返回默认值
    return 'no_takeover';
  } catch (error) {
    console.error("获取接管状态失败:", error);
    return 'no_takeover';
  }
}

// ===== 会话创建和管理 =====

/**
 * 创建新会话
 */
export async function createConversation(customerId?: string): Promise<Conversation> {
  try {
    const userId = customerId || authService.getCurrentUserId();
    if (!userId) {
      throw new ApiClientError("用户ID不存在", {
        status: 401,
        type: ErrorType.AUTHENTICATION,
      })
    }
    
    const newConversation = await ChatApiService.createConversation(userId);
    
    // 更新本地会话列表
    const conversations = chatState.getConversations();
    conversations.unshift(newConversation);
    chatState.setConversations(conversations);
    
    return newConversation;
  } catch (error) {
    console.error("创建会话失败:", error);
    throw error;
  }
}

/**
 * 获取最近的会话
 */
export async function getRecentConversation(): Promise<Conversation | null> {
  try {
    // 先获取所有会话
    const allConversations = await getConversations();
    
    // 如果没有会话，返回null
    if (!allConversations || allConversations.length === 0) {
      return null;
    }
    
    // 按更新时间排序，返回最近的会话
    return [...allConversations].sort((a, b) => {
      const dateA = new Date(a.updatedAt || '').getTime();
      const dateB = new Date(b.updatedAt || '').getTime();
      return dateB - dateA;
    })[0];
  } catch (error) {
    console.error("获取最近会话失败:", error);
    return null;
  }
}

/**
 * 获取或创建会话
 */
export async function getOrCreateConversation(): Promise<Conversation> {
  try {
    // 尝试获取最近的会话
    const recentConversation = await getRecentConversation();
    
    // 如果有最近会话，检查活跃时间
    if (recentConversation) {
      const lastActive = new Date(recentConversation.updatedAt || '').getTime();
      const now = new Date().getTime();
      const hoursDifference = (now - lastActive) / (1000 * 60 * 60);
      
      // 如果会话在24小时内有活动，则使用该会话
      if (hoursDifference < 24) {
        return recentConversation;
      }
    }
    
    // 创建新会话，添加重试逻辑
    const maxRetries = 3;
    let attempt = 1;
    let lastError: any;
    
    while (attempt <= maxRetries) {
      try {
        return await createConversation();
      } catch (error) {
        lastError = error;
        console.error(`创建会话失败 (尝试 ${attempt}/${maxRetries}):`, error);
        
        if (attempt < maxRetries) {
          // 等待一段时间后重试
          const retryDelay = 1000 * attempt; // 递增延迟
          await new Promise(resolve => setTimeout(resolve, retryDelay));
          attempt++;
        } else {
          break;
        }
      }
    }
    
    throw lastError || new ApiClientError("创建会话失败，请稍后再试", {
      status: 500,
      type: ErrorType.UNKNOWN,
    })
  } catch (error) {
    console.error("获取或创建会话失败:", error);
    throw error;
  }
}

/**
 * 获取会话详情
 */
export async function getConversationDetails(conversationId: string): Promise<Conversation | null> {
  try {
    return await ChatApiService.getConversationDetails(conversationId);
  } catch (error) {
    console.error('获取会话详情出错:', error);
    return null;
  }
}

/**
 * 更新会话标题
 */
export async function updateConversationTitle(conversationId: string, title: string): Promise<void> {
  try {
    await ChatApiService.updateConversationTitle(conversationId, title);
    
    // 更新本地缓存中的会话标题
    chatState.updateConversationTitle(conversationId, title);
  } catch (error) {
    console.error('更新会话标题失败:', error);
    throw error;
  }
}

// ===== 客户管理功能（顾问端使用） =====

/**
 * 获取客户列表（顾问端使用）
 */
export async function getCustomerList(): Promise<Customer[]> {
  try {
    return await ChatApiService.getCustomerList();
  } catch (error) {
    console.error('获取客户列表失败:', error);
    throw error;
  }
}

/**
 * 获取指定客户的会话列表
 */
export async function getCustomerConversations(customerId: string): Promise<Conversation[]> {
  try {
    return await ChatApiService.getCustomerConversations(customerId);
  } catch (error) {
    console.error('获取客户会话失败:', error);
    throw error;
  }
} 