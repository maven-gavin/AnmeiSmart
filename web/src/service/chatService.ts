/**
 * 聊天服务协调器
 * 重构后的轻量级聊天服务，协调各模块间的交互
 * 保持向后兼容性，确保现有代码不会中断
 */

import { authService } from "./authService";
import { AppError, ErrorType } from './errors';

// 导入重构后的模块
import {
  chatState,
  ChatApiService,
  type Message,
  type Conversation,
  type CustomerProfile,
  type Customer,
  type ConsultationHistoryItem
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
      throw new AppError(ErrorType.VALIDATION, 400, '消息缺少会话ID');
    }

    if (!message.content) {
      throw new AppError(ErrorType.VALIDATION, 400, '消息内容不能为空');
    }

    // 调用API保存消息
    const savedMessage = await ChatApiService.saveMessage(message);

    // 更新本地缓存
    if (savedMessage.conversationId) {
      chatState.addMessage(savedMessage.conversationId, savedMessage);
    }

    return savedMessage;
  } catch (error) {
    console.error('保存消息失败:', error);
    
    // 如果是认证错误，抛出
    if (error instanceof AppError && error.type === ErrorType.AUTHENTICATION) {
      throw error;
    }
    
    // 其他错误包装后抛出
    const errorMessage = error instanceof Error ? error.message : '保存消息失败';
    throw new AppError(ErrorType.NETWORK, 500, errorMessage);
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
    if (error instanceof AppError && error.type === ErrorType.AUTHENTICATION) {
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
export async function getConversations(): Promise<Conversation[]> {
  // 检查是否已有请求正在进行
  if (chatState.isRequestingConversationsState()) {
    return chatState.getConversations();
  }
  
  // 检查缓存是否在有效期内
  const conversations = chatState.getConversations();
  if (conversations.length > 0 && chatState.isConversationsCacheValid()) {
    return conversations;
  }
  
  try {
    // 设置请求标志
    chatState.setRequestingConversations(true);
    
    // 使用API服务获取会话列表
    const formattedConversations = await ChatApiService.getConversations();
    
    // 更新本地缓存
    chatState.setConversations(formattedConversations);
    chatState.updateConversationsRequestTime();
    
    return formattedConversations;
  } catch (error) {
    console.error('获取会话列表出错:', error);
    
    // 如果是认证错误，抛出异常
    if (error instanceof AppError && error.type === ErrorType.AUTHENTICATION) {
      throw error;
    }
    
    // 其他错误返回缓存数据
    return conversations;
  } finally {
    // 重置请求标志
    chatState.setRequestingConversations(false);
  }
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

// ===== 顾问接管功能 =====

/**
 * 顾问接管会话
 */
export async function takeoverConversation(conversationId: string): Promise<boolean> {
  try {
    // 更新本地状态
    chatState.setConsultantTakeover(conversationId, true);
    
    // 发送接管状态到后端
    await ChatApiService.setTakeoverStatus(conversationId, false); // false表示顾问接管
    
    return true;
  } catch (error) {
    console.error('设置接管状态失败:', error);
    return false;
  }
}

/**
 * 切回AI模式
 */
export async function switchBackToAI(conversationId: string): Promise<boolean> {
  try {
    // 更新本地状态
    chatState.setConsultantTakeover(conversationId, false);
    
    // 发送接管状态到后端
    await ChatApiService.setTakeoverStatus(conversationId, true); // true表示AI接管
    
    return true;
  } catch (error) {
    console.error('设置接管状态失败:', error);
    return false;
  }
}

/**
 * 是否处于顾问模式 - 从服务器获取最新状态
 */
export async function isConsultantMode(conversationId: string): Promise<boolean> {
  try {
    // 获取会话详情
    const conversation = await ChatApiService.getConversationDetails(conversationId);
    
    if (conversation && 'is_ai_controlled' in conversation && typeof conversation.is_ai_controlled === 'boolean') {
      // 更新本地状态
      const isConsultantMode = !conversation.is_ai_controlled;
      chatState.setConsultantTakeover(conversationId, isConsultantMode);
      return isConsultantMode;
    }
    
    // 如果无法获取状态，返回当前本地状态
    return chatState.isConsultantTakeover(conversationId);
  } catch (error) {
    console.error("获取顾问模式状态失败:", error);
    return chatState.isConsultantTakeover(conversationId);
  }
}

/**
 * 同步顾问接管状态
 */
export async function syncConsultantTakeoverStatus(conversationId: string): Promise<boolean> {
  try {
    // 获取会话详情
    const conversation = await ChatApiService.getConversationDetails(conversationId);
    
    if (conversation && 'is_ai_controlled' in conversation && typeof conversation.is_ai_controlled === 'boolean') {
      // 更新本地状态
      const isConsultantMode = !conversation.is_ai_controlled;
      chatState.setConsultantTakeover(conversationId, isConsultantMode);
      return isConsultantMode;
    }
    
    // 如果无法获取状态，返回当前本地状态
    return chatState.isConsultantTakeover(conversationId);
  } catch (error) {
    console.error("同步顾问接管状态失败:", error);
    return chatState.isConsultantTakeover(conversationId);
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
      throw new AppError(ErrorType.AUTHENTICATION, 401, "用户ID不存在");
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
    
    throw lastError || new AppError(ErrorType.UNKNOWN, 500, "创建会话失败，请稍后再试");
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