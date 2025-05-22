import { Message, Conversation, CustomerProfile } from "@/types/chat";
import { v4 as uuidv4 } from 'uuid';
import { authService } from "./authService";
// 引入新的WebSocket客户端架构
import { getWebSocketClient, ConnectionStatus } from './websocket';
import { SenderType } from './websocket/types';
import { TextMessageHandler } from './websocket/handlers/textHandler';
import { SystemMessageHandler } from './websocket/handlers/systemHandler';

// 保存运行时的消息数据（会话ID -> 消息数组）
const chatMessages: Record<string, Message[]> = {}; // 移除模拟数据初始化，改为空对象

// 保存运行时的会话数据
let conversations: Conversation[] = []; // 移除模拟数据初始化，改为空数组

// API基础URL
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';

// AI信息
const aiInfo = {
  id: 'ai_assistant',
  name: 'AI助手',
  avatar: '/avatars/ai.png',
  type: 'ai' as const,
};

// 系统用户信息（用于系统消息等）
const systemInfo = {
  id: 'system',
  name: '系统',
  avatar: '/avatars/system.png',
  type: 'system' as const,
};

// 保存AI状态（会话ID -> 是否由顾问接管）
const consultantTakeover: Record<string, boolean> = {};

// 消息队列，用于离线消息存储
const messageQueue: any[] = [];

// 添加用于跟踪最后连接的会话ID
let lastConnectedConversationId: string | null = null;

// 用于取消连接尝试的计时器
let connectionDebounceTimer: NodeJS.Timeout | null = null;

// 消息回调处理函数
type MessageCallback = (message: any) => void;
const messageCallbacks: Record<string, MessageCallback[]> = {};

// 保存已处理的消息ID，避免重复处理
const processedMessageIds = new Set<string>();

// 添加请求防抖标志，按会话ID跟踪
const isRequestingMessages: Record<string, boolean> = {};
const lastMessagesRequestTime: Record<string, number> = {};
const MESSAGES_CACHE_TIME = 5000; // 5秒缓存时间

// 添加请求防抖标志
let isRequestingConversations = false;
let lastConversationsRequestTime = 0;
const CONVERSATIONS_CACHE_TIME = 10000; // 10秒缓存时间

// 初始化WebSocket客户端
// 注意：这是一个懒加载的函数，只有在第一次调用时才会初始化WebSocket客户端
const initializeWebSocketClient = () => {
  try {
    // 获取协议
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsHost = process.env.NEXT_PUBLIC_WS_URL || 'localhost:8000';
    const baseUrl = `${wsProtocol}//${wsHost}/api/v1/chat/ws`;
    
    // 获取客户端实例
    const wsClient = getWebSocketClient({
      url: baseUrl,
      reconnectAttempts: 5,
      reconnectInterval: 1000,
      heartbeatInterval: 30000,
      connectionTimeout: 10000,
      debug: process.env.NODE_ENV === 'development'
    });
    
    // 注册消息处理器
    wsClient.registerHandler(new TextMessageHandler());
    wsClient.registerHandler(new SystemMessageHandler());
    
    // 添加处理器的回调
    const textHandler = wsClient.getHandlers().find(h => h.getName() === 'TextMessageHandler');
    if (textHandler) {
      textHandler.addCallback('message', (data) => {
        console.log('收到文本消息:', data);
        handleWebSocketMessage(data);
      });
    }
    
    const systemHandler = wsClient.getHandlers().find(h => h.getName() === 'SystemMessageHandler');
    if (systemHandler) {
      systemHandler.addCallback('system', (data) => {
        console.log('收到系统消息:', data);
        handleWebSocketMessage(data);
      });
    }
    
    return wsClient;
  } catch (error) {
    console.error('初始化WebSocket客户端失败:', error);
    throw error;
  }
};

// 获取WebSocket客户端实例
const getWsClient = () => {
  try {
    return getWebSocketClient();
  } catch (error) {
    // 如果客户端尚未初始化，则初始化它
    return initializeWebSocketClient();
  }
};

/**
 * 初始化WebSocket连接
 * @param userId 用户ID
 * @param conversationId 会话ID
 */
export function initializeWebSocket(userId: string, conversationId: string): void {
  try {
    // 获取当前用户信息和角色
    const token = authService.getToken() || '';
    const userRole = authService.getCurrentUserRole() || '';
    
    // 创建WebSocket客户端
    const wsClient = getWebSocketClient({
      url: process.env.NEXT_PUBLIC_WEBSOCKET_URL || 'ws://localhost:8000/ws',
      reconnectAttempts: 5,
      reconnectInterval: 2000,
      heartbeatInterval: 30000,
      debug: false
    });

    // 准备连接参数
    const connectionParams = {
      userId,
      conversationId,
      token,
      // 将UserRole映射到SenderType
      userType: mapUserRoleToSenderType(userRole)
    };
    
    console.log('初始化WebSocket连接:', connectionParams);
    
    // 连接到WebSocket服务器
    wsClient.connect(connectionParams)
      .then(() => {
        console.log('WebSocket连接成功');
        // 连接成功回调
      })
      .catch(error => {
        console.error('WebSocket连接失败:', error);
        // 连接失败回调
      });
  } catch (error) {
    console.error('初始化WebSocket连接出错:', error);
  }
}

/**
 * 将UserRole映射到SenderType
 * @param role 用户角色
 * @returns 对应的SenderType
 */
function mapUserRoleToSenderType(role: string): SenderType {
  switch (role) {
    case 'customer':
      return SenderType.CUSTOMER;
    case 'consultant':
      return SenderType.CONSULTANT;
    case 'doctor':
      return SenderType.DOCTOR;
    default:
      return SenderType.USER;
  }
}

// 同步聊天数据，确保多端一致性
export const syncChatData = async (conversationId: string): Promise<void> => {
  try {
    console.log(`同步会话数据: ${conversationId}`);
    
    // 重新获取会话数据
    await getConversations();
    
    // 重新获取消息数据
    await getConversationMessages(conversationId);
    
    console.log(`会话数据同步完成: ${conversationId}`);
  } catch (error) {
    console.error(`会话数据同步出错:`, error);
  }
};

// 修改handleWebSocketMessage函数，避免类型错误
const handleWebSocketMessage = (data: any) => {
  try {
    // 检查基本动作类型
    const action = data.action;
    
    // 检查必要的会话ID
    if (data.conversation_id) {
      // 如果是消息相关的动作，触发同步
      if (action === 'message' || action === 'connect') {
        // 异步同步数据，不阻塞消息处理
        syncChatData(data.conversation_id).catch(error => 
          console.error(`同步会话数据失败: ${error}`)
        );
      }
    }
    
    // 调用注册的回调函数
    if (action && action in messageCallbacks) {
      messageCallbacks[action].forEach(callback => {
        try {
          callback(data);
        } catch (callbackError) {
          console.error(`执行回调函数出错: ${callbackError}`);
        }
      });
    }
  } catch (error) {
    console.error(`处理WebSocket消息出错: ${error}`);
  }
};

// 添加消息回调
export const addMessageCallback = (action: string, callback: MessageCallback) => {
  if (!messageCallbacks[action]) {
    messageCallbacks[action] = [];
  }
  messageCallbacks[action].push(callback);
};

// 移除消息回调
export const removeMessageCallback = (action: string, callback: MessageCallback) => {
  if (messageCallbacks[action]) {
    messageCallbacks[action] = messageCallbacks[action].filter(cb => cb !== callback);
  }
};

// 发送WebSocket消息
export const sendWebSocketMessage = (message: any) => {
  console.log(`准备通过WebSocket发送消息:`, message);
  
  // 确保必要的字段存在
  if (!message.conversation_id) {
    console.error('发送的消息没有会话ID，无法继续');
    return false;
  }
  
  const conversationId = message.conversation_id;
  
  try {
    // 获取WebSocket客户端
    const wsClient = getWsClient();
    
    // 检查WebSocket连接状态
    if (wsClient.isConnected()) {
      // 检查当前连接的会话ID是否匹配
      const params = wsClient.getConnectionParams();
      if (params.conversationId !== conversationId) {
        console.warn(`当前WebSocket连接的会话ID(${params.conversationId})与要发送消息的会话ID(${conversationId})不一致，将重新连接`);
        
        // 将消息加入队列
        messageQueue.push(message);
        
        // 重新连接正确的会话
        const user = authService.getCurrentUser();
        if (user) {
          initializeWebSocket(user.id, conversationId);
        }
        
        return false;
      }
      
      // 发送消息
      return wsClient.sendMessage(message);
    } else {
      // WebSocket未连接，将消息加入队列
      console.log(`WebSocket未连接，将消息加入队列`);
      messageQueue.push(message);
      
      // 尝试连接
      const user = authService.getCurrentUser();
      if (user) {
        initializeWebSocket(user.id, conversationId);
      }
      
      return false;
    }
  } catch (error) {
    console.error('发送WebSocket消息失败:', error);
    
    // 将消息加入队列
    messageQueue.push(message);
    
    return false;
  }
};

// 关闭WebSocket连接
export const closeWebSocketConnection = () => {
  // 清除连接防抖计时器
  if (connectionDebounceTimer) {
    clearTimeout(connectionDebounceTimer);
    connectionDebounceTimer = null;
  }
  
  try {
    // 获取WebSocket客户端
    const wsClient = getWsClient();
    
    // 断开连接
    wsClient.disconnect();
    
    console.log('WebSocket连接已关闭');
  } catch (error) {
    console.error('关闭WebSocket连接时出错:', error);
  }
  
  // 清空消息队列，避免切换会话时发送旧消息
  if (messageQueue.length > 0) {
    console.log(`清空消息队列，丢弃${messageQueue.length}条消息`);
    messageQueue.length = 0;
  }
};

// 获取连接状态
export const getConnectionStatus = () => {
  try {
    const wsClient = getWsClient();
    return wsClient.getConnectionStatus();
  } catch (error) {
    return ConnectionStatus.DISCONNECTED;
  }
};

// 生成模拟AI回复
const generateAIResponse = async (content: string, conversationId: string): Promise<string> => {
  try {
    // 调用后端AI服务
    const API_URL = `${API_BASE_URL}/ai/chat`;
    
    // 获取当前用户的认证信息
    const token = authService.getToken();
    
    if (!token) {
      console.error("未登录，无法请求AI服务");
      return "请先登录以获取AI回复。";
    }
    
    // 构建请求数据
    const requestData = {
      conversation_id: conversationId,
      content: content,
      type: "text",
      sender_id: authService.getCurrentUserId() || "anonymous",
      sender_type: authService.getCurrentUserRole() || "user"
    };
    
    // 发送请求
    const response = await fetch(API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(requestData)
    });
    
    // 检查响应
    if (!response.ok) {
      const errorData = await response.json();
      console.error("AI服务请求失败:", errorData);
      return "抱歉，AI服务暂时不可用，请稍后再试。";
    }
    
    // 获取AI回复
    const data = await response.json();
    return data.content;
  } catch (error) {
    console.error("AI服务请求异常:", error);
    
    // 如果后端服务不可用，使用简单的规则响应
    if (content.includes('恢复') || content.includes('术后')) {
      return '术后恢复时间因人而异，一般需要1-2周的恢复期。建议术后遵循医生的指导，保持伤口清洁，避免剧烈运动，按时服用药物。';
    } else if (content.includes('价格') || content.includes('费用')) {
      return '我们的医美项目价格根据具体操作和材料有所不同。基础项目从数千元起，精细项目可能达到数万元。我们提供免费咨询和评估服务，可以根据您的需求提供详细报价。';
    } else if (content.includes('风险') || content.includes('副作用')) {
      return '任何医疗美容项目都存在一定风险。常见的副作用包括暂时性红肿、瘀斑等。严重但罕见的风险包括感染、过敏反应等。我们的专业医生会在术前详细告知您相关风险并制定个性化方案降低风险。';
    } else if (content.includes('玻尿酸') || content.includes('填充')) {
      return '玻尿酸是一种常见的注射填充剂，可用于面部轮廓塑造、唇部丰满等。效果通常可维持6-18个月，是一种临时性填充方案。注射过程快速，恢复期短，是许多客户的首选。';
    } else {
      return '感谢您的咨询。我们的专业医疗团队将为您提供个性化的方案和详细解答。您还有其他问题吗？';
    }
  }
};

// 发送文字消息
export const sendTextMessage = async (conversationId: string, content: string): Promise<Message> => {
  // 获取当前用户
  const currentUser = authService.getCurrentUser();
  if (!currentUser) {
    throw new Error('用户未登录');
  }
  
  // 确保使用用户的当前角色，避免角色混淆
  const userRole = currentUser.currentRole || 'customer';
  
  console.log(`发送文本消息: 会话ID=${conversationId}, 用户ID=${currentUser.id}, 角色=${userRole}`);
  console.log(`WebSocket状态: ${getConnectionStatus()}, 连接状态: ${getWsClient().isConnected()}`);
  
  // 创建用户消息
  const userMessage: Message = {
    id: `m_${uuidv4()}`,
    content,
    type: 'text',
    sender: {
      id: currentUser.id,
      type: userRole, // 明确使用当前角色
      name: currentUser.name,
      avatar: '/avatars/user.png', // 应使用用户头像
    },
    timestamp: new Date().toISOString(),
  };
  
  console.log(`创建本地消息对象:`, userMessage);
  
  // 添加到本地消息列表
  if (!chatMessages[conversationId]) {
    chatMessages[conversationId] = [];
  }
  chatMessages[conversationId].push(userMessage);
  console.log(`消息已添加到本地列表, 当前共${chatMessages[conversationId].length}条消息`);
  
  // 更新本地会话最后一条消息
  const conversationIndex = conversations.findIndex(conv => conv.id === conversationId);
  if (conversationIndex >= 0) {
    conversations[conversationIndex] = {
      ...conversations[conversationIndex],
      lastMessage: userMessage,
      updatedAt: userMessage.timestamp,
    };
    console.log(`已更新本地会话记录`);
  } else {
    console.log(`未找到本地会话记录，ID: ${conversationId}`);
  }
  
  // 通过WebSocket发送消息
  const wsMessage = {
    action: 'message',
    data: {
      content,
      type: 'text',
      sender_type: userRole // 明确使用当前角色
    },
    conversation_id: conversationId,
    timestamp: new Date().toISOString()
  };
  
  console.log(`准备通过WebSocket发送消息，会话ID: ${conversationId}, 角色: ${userRole}`, wsMessage);
  sendWebSocketMessage(wsMessage);
  
  return userMessage;
};

// 发送图片消息
export const sendImageMessage = async (conversationId: string, imageUrl: string): Promise<Message> => {
  // 获取当前用户
  const currentUser = authService.getCurrentUser();
  if (!currentUser) {
    throw new Error('用户未登录');
  }
  
  // 创建图片消息
  const imageMessage: Message = {
    id: `m_${uuidv4()}`,
    content: imageUrl,
    type: 'image',
    sender: {
      id: currentUser.id,
      type: currentUser.currentRole || 'customer',
      name: currentUser.name,
      avatar: currentUser.avatar || '/avatars/user.png',
    },
    timestamp: new Date().toISOString(),
  };
  
  // 添加到消息列表
  if (!chatMessages[conversationId]) {
    chatMessages[conversationId] = [];
  }
  chatMessages[conversationId].push(imageMessage);
  
  // 更新会话最后一条消息
  const conversationIndex = conversations.findIndex(conv => conv.id === conversationId);
  if (conversationIndex >= 0) {
    conversations[conversationIndex] = {
      ...conversations[conversationIndex],
      lastMessage: imageMessage,
      updatedAt: imageMessage.timestamp,
    };
  }
  
  // 模拟异步API调用
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(imageMessage);
    }, 500); // 图片上传通常需要更长时间
  });
};

// 发送语音消息
export const sendVoiceMessage = async (conversationId: string, audioUrl: string): Promise<Message> => {
  // 获取当前用户
  const currentUser = authService.getCurrentUser();
  if (!currentUser) {
    throw new Error('用户未登录');
  }
  
  // 创建语音消息
  const voiceMessage: Message = {
    id: `m_${uuidv4()}`,
    content: audioUrl,
    type: 'voice',
    sender: {
      id: currentUser.id,
      type: currentUser.currentRole || 'customer',
      name: currentUser.name, 
      avatar: currentUser.avatar || '/avatars/user.png',
    },
    timestamp: new Date().toISOString(),
  };
  
  // 添加到消息列表
  if (!chatMessages[conversationId]) {
    chatMessages[conversationId] = [];
  }
  chatMessages[conversationId].push(voiceMessage);
  
  // 更新会话最后一条消息
  const conversationIndex = conversations.findIndex(conv => conv.id === conversationId);
  if (conversationIndex >= 0) {
    conversations[conversationIndex] = {
      ...conversations[conversationIndex],
      lastMessage: voiceMessage,
      updatedAt: voiceMessage.timestamp,
    };
  }
  
  // 模拟异步API调用
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(voiceMessage);
    }, 500);
  });
};

// 获取AI回复
export const getAIResponse = async (conversationId: string, userMessage: Message): Promise<Message | null> => {
  // 如果顾问已接管，不再生成AI回复
  if (consultantTakeover[conversationId]) {
    return null;
  }
  
  // 根据用户消息内容生成AI回复
  const responseContent = await generateAIResponse(userMessage.content, conversationId);
  
  // 创建AI回复消息
  const aiMessage: Message = {
    id: `m_${uuidv4()}`,
    content: responseContent,
    type: 'text',
    sender: {
      id: aiInfo.id,
      type: aiInfo.type,
      name: aiInfo.name,
      avatar: aiInfo.avatar,
    },
    timestamp: new Date().toISOString(),
  };
  
  // 添加到消息列表
  chatMessages[conversationId].push(aiMessage);
  
  // 更新会话最后一条消息
  const conversationIndex = conversations.findIndex(conv => conv.id === conversationId);
  if (conversationIndex >= 0) {
    conversations[conversationIndex] = {
      ...conversations[conversationIndex],
      lastMessage: aiMessage,
      updatedAt: aiMessage.timestamp,
    };
  }
  
  return aiMessage;
};

// 获取会话消息
export const getConversationMessages = async (conversationId: string): Promise<Message[]> => {
  // 检查是否已有针对该会话的请求正在进行
  if (isRequestingMessages[conversationId]) {
    console.log(`已有获取会话(${conversationId})消息请求正在进行，返回缓存数据`);
    return chatMessages[conversationId] || [];
  }
  
  // 如果有本地缓存，检查缓存是否在有效期内
  const now = Date.now();
  const cachedMessages = chatMessages[conversationId] || [];
  if (cachedMessages.length > 0 && lastMessagesRequestTime[conversationId] && 
      (now - lastMessagesRequestTime[conversationId]) < MESSAGES_CACHE_TIME) {
    console.log(`使用会话(${conversationId})消息缓存数据，距上次请求时间:`, 
               now - lastMessagesRequestTime[conversationId], 'ms');
    return cachedMessages;
  }
  
  try {
    // 设置请求标志
    isRequestingMessages[conversationId] = true;
    
    // 获取认证令牌
    const token = authService.getToken();
    if (!token) {
      console.error("未登录，无法获取会话消息");
      return cachedMessages;
    }
    
    // 创建带超时的fetch请求
    const fetchWithTimeout = async (url: string, options: RequestInit, timeout = 3000) => {
      const controller = new AbortController();
      const { signal } = controller;
      
      const timeoutId = setTimeout(() => controller.abort(), timeout);
      
      try {
        const response = await fetch(url, {
          ...options,
          signal
        });
        
        clearTimeout(timeoutId);
        return response;
      } catch (err) {
        clearTimeout(timeoutId);
        throw err;
      }
    };
    
    // 从后端API获取消息，添加超时处理
    const response = await fetchWithTimeout(
      `${API_BASE_URL}/chat/conversations/${conversationId}/messages`, 
      {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      },
      5000 // 5秒超时
    );
    
    if (!response.ok) {
      // 处理错误响应
      const status = response.status;
      
      // 处理401认证错误
      if (status === 401) {
        console.error("认证失败，Token可能已过期");
        throw new Error(`401 Unauthorized: Token已过期`);
      }
      
      throw new Error(`获取消息失败: ${status}`);
    }
    
    const messages = await response.json();
    
    // 转换格式，适配前端格式
    const formattedMessages: Message[] = messages.map((msg: any) => ({
      id: msg.id,
      content: msg.content,
      type: msg.type,
      sender: {
        id: msg.sender.id,
        name: msg.sender.name,
        avatar: msg.sender.avatar || (msg.sender.type === 'ai' ? aiInfo.avatar : '/avatars/user.png'),
        type: msg.sender.type,
      },
      timestamp: msg.timestamp,
      isImportant: msg.is_important || false,
      isRead: msg.is_read || false
    }));
    
    // 更新本地缓存
    chatMessages[conversationId] = formattedMessages;
    
    // 更新请求时间戳
    lastMessagesRequestTime[conversationId] = Date.now();
    
    return formattedMessages;
  } catch (error) {
    console.error(`获取会话消息出错:`, error);
    
    // 如果是AbortError，则是超时
    if (error instanceof DOMException && error.name === 'AbortError') {
      console.error('获取消息请求超时');
    }
    
    // 如果是认证错误，不返回缓存数据，而是抛出异常
    if (error instanceof Error && error.message.includes('401')) {
      throw error;
    }
    
    // 其他错误时返回缓存数据
    return cachedMessages;
  } finally {
    // 重置请求标志
    isRequestingMessages[conversationId] = false;
  }
};

// 获取所有会话
export const getConversations = async (): Promise<Conversation[]> => {
  // 检查是否已有请求正在进行
  if (isRequestingConversations) {
    console.log('已有获取会话请求正在进行，返回缓存数据');
    return conversations;
  }
  
  // 检查缓存是否在有效期内
  const now = Date.now();
  if (conversations.length > 0 && (now - lastConversationsRequestTime) < CONVERSATIONS_CACHE_TIME) {
    console.log('使用会话缓存数据，距上次请求时间:', now - lastConversationsRequestTime, 'ms');
    return conversations;
  }
  
  try {
    // 设置请求标志
    isRequestingConversations = true;
    
    // 获取认证令牌
    const token = authService.getToken();
    if (!token) {
      console.error("未登录，无法获取会话列表");
      return [];
    }
    
    // 从后端API获取会话列表
    console.log('开始获取会话列表，API地址:', `${API_BASE_URL}/chat/conversations`);
    const response = await fetch(`${API_BASE_URL}/chat/conversations`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    // 处理错误响应
    if (!response.ok) {
      const status = response.status;
      const errorText = await response.text().catch(() => '');
      
      // 处理401认证错误
      if (status === 401) {
        console.error("认证失败，Token可能已过期");
        throw new Error(`401 Unauthorized: Token已过期`);
      }
      
      throw new Error(`获取会话列表失败: ${status} ${errorText}`);
    }
    
    // 克隆response以便打印
    const responseClone = response.clone();
    
    // 打印原始响应内容
    try {
      const rawData = await responseClone.text();
      console.log('会话列表原始响应数据(文本格式):', rawData);
      
      // 尝试解析为JSON以更易读
      try {
        const jsonData = JSON.parse(rawData);
        console.log('会话列表原始响应数据(JSON格式):', jsonData);
        
        // 深度分析每个会话对象的结构
        if (Array.isArray(jsonData)) {
          jsonData.forEach((conv, index) => {
            console.log(`分析会话[${index}]的结构:`, conv);
            console.log(`会话[${index}]的customer属性:`, conv.customer);
            console.log(`会话[${index}]的属性列表:`, Object.keys(conv));
          });
        }
      } catch (jsonError) {
        console.error('响应不是有效的JSON格式:', jsonError);
      }
    } catch (textError) {
      console.error('读取响应体失败:', textError);
    }
    
    const data = await response.json();
    console.log('会话列表原始数据(解析后):', data);
    
    // 转换格式，适配前端格式
    const formattedConversations: Conversation[] = await Promise.all(data.map(async (conv: any) => {
      // 获取最后一条消息
      let lastMessage: Message | undefined;
      try {
        // 避免为每个会话单独请求消息
        if (chatMessages[conv.id] && chatMessages[conv.id].length > 0) {
          lastMessage = chatMessages[conv.id][chatMessages[conv.id].length - 1];
        }
      } catch (error) {
        console.error(`获取会话${conv.id}的消息失败:`, error);
        // 如果获取消息失败，继续处理其他数据
      }
      
      // 详细记录客户信息日志，帮助调试
      console.log(`会话 ${conv.id} 原始客户数据:`, JSON.stringify(conv.customer));
      
      // 确保customer数据完整性，并提供有意义的默认值
      let customerName = "未知用户";
      if (conv.customer) {
        customerName = conv.customer.username || "未知用户";
        console.log(`会话 ${conv.id} 客户名称(来自customer对象): ${customerName}`);
      } else {
        console.log(`会话 ${conv.id} 缺少customer对象`);
      }
      
      return {
        id: conv.id,
        title: conv.title,
        user: {
          id: conv.customer_id,
          name: customerName,
          avatar: conv.customer?.avatar || '/avatars/user.png',
          tags: conv.customer?.tags ? (typeof conv.customer.tags === 'string' ? conv.customer.tags.split(',') : conv.customer.tags) : []
        },
        lastMessage: lastMessage,
        unreadCount: 0, // TODO: 实现未读消息计数
        updatedAt: conv.updated_at
      };
    }));
    
    // 更新本地缓存
    conversations = formattedConversations;
    
    // 更新请求时间戳
    lastConversationsRequestTime = Date.now();
    
    return formattedConversations;
  } catch (error) {
    console.error(`获取会话列表出错:`, error);
    // 如果是认证错误，不返回缓存数据，而是抛出异常
    if (error instanceof Error && error.message.includes('401')) {
      throw error;
    }
    // 其他错误返回缓存数据
    return conversations;
  } finally {
    // 重置请求标志
    isRequestingConversations = false;
  }
};

// 标记消息为重点
export const markMessageAsImportant = (conversationId: string, messageId: string, isImportant: boolean): Message | null => {
  const messages = chatMessages[conversationId];
  if (!messages) return null;
  
  const messageIndex = messages.findIndex(msg => msg.id === messageId);
  if (messageIndex >= 0) {
    const updatedMessage = {
      ...messages[messageIndex],
      isImportant,
    };
    
    // 更新消息
    messages[messageIndex] = updatedMessage;
    return updatedMessage;
  }
  
  return null;
};

// 获取重点消息
export const getImportantMessages = (conversationId: string): Message[] => {
  const messages = chatMessages[conversationId];
  if (!messages) return [];
  
  return messages.filter(msg => msg.isImportant);
};

// 获取客户档案
export const getCustomerProfile = async (customerId: string): Promise<CustomerProfile | null> => {
  try {
    // 获取认证令牌
    const token = authService.getToken();
    if (!token) {
      console.error("未登录，无法获取客户档案");
      return null;
    }
    
    // 从后端API获取客户档案
    const response = await fetch(`${API_BASE_URL}/customers/${customerId}/profile`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      throw new Error(`获取客户档案失败: ${response.status}`);
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error(`获取客户档案出错:`, error);
    return null;
  }
};

// 获取客户历史咨询记录
export const getCustomerConsultationHistory = async (customerId: string): Promise<CustomerProfile['consultationHistory']> => {
  const profile = await getCustomerProfile(customerId);
  if (!profile) return [];
  
  return profile.consultationHistory || [];
};

// 顾问接管会话
export const takeoverConversation = (conversationId: string): boolean => {
  consultantTakeover[conversationId] = true;
  
  // 发送系统消息通知顾问接管
  const systemMessage: Message = {
    id: `m_${uuidv4()}`,
    content: '顾问已接管会话',
    type: 'text',
    sender: {
      id: 'system',
      type: 'system',
      name: '系统',
      avatar: '',
    },
    timestamp: new Date().toISOString(),
    isSystemMessage: true,
  };
  
  // 添加到消息列表
  if (!chatMessages[conversationId]) {
    chatMessages[conversationId] = [];
  }
  chatMessages[conversationId].push(systemMessage);
  
  // 发送接管状态到后端，确保多端同步
  try {
    const token = authService.getToken();
    if (token) {
      fetch(`${API_BASE_URL}/chat/conversations/${conversationId}/takeover`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ is_ai_controlled: false }) // false表示顾问接管
      }).catch(err => console.error('发送接管状态到后端失败:', err));
    }
  } catch (error) {
    console.error('设置接管状态失败:', error);
  }
  
  return true;
};

// 切回AI模式
export const switchBackToAI = (conversationId: string): boolean => {
  consultantTakeover[conversationId] = false;
  
  // 发送系统消息通知切回AI模式
  const systemMessage: Message = {
    id: `m_${uuidv4()}`,
    content: 'AI助手已接管会话',
    type: 'text',
    sender: {
      id: 'system',
      type: 'system',
      name: '系统',
      avatar: '',
    },
    timestamp: new Date().toISOString(),
    isSystemMessage: true,
  };
  
  // 添加到消息列表
  if (!chatMessages[conversationId]) {
    chatMessages[conversationId] = [];
  }
  chatMessages[conversationId].push(systemMessage);
  
  // 发送接管状态到后端，确保多端同步
  try {
    const token = authService.getToken();
    if (token) {
      fetch(`${API_BASE_URL}/chat/conversations/${conversationId}/takeover`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ is_ai_controlled: true }) // true表示AI接管
      }).catch(err => console.error('发送接管状态到后端失败:', err));
    }
  } catch (error) {
    console.error('设置接管状态失败:', error);
  }
  
  return true;
};

// 是否处于顾问模式
export const isConsultantMode = (conversationId: string): boolean => {
  return !!consultantTakeover[conversationId];
};

// 生成短会话ID (确保不超过36个字符)
const generateShortId = () => {
  // 不使用前缀，直接生成适合长度的UUID
  return uuidv4().replace(/-/g, '').substring(0, 32);
};

// 创建新会话
export const createConversation = async (customerId?: string): Promise<Conversation> => {
  try {
    // 获取认证令牌
    const token = authService.getToken();
    if (!token) {
      throw new Error("未登录，无法创建会话");
    }
    
    // 使用当前用户ID或提供的客户ID
    const userId = customerId || authService.getCurrentUserId();
    if (!userId) {
      throw new Error("用户ID不存在");
    }
    
    console.log('创建新会话，用户ID:', userId);
    
    // 准备请求数据，不需要自己生成会话ID，后端会生成符合格式的ID
    const requestData = {
      customer_id: userId,
      title: `咨询会话 ${new Date().toLocaleDateString('zh-CN')}`
    };
    
    console.log('创建会话请求数据:', requestData);
    
    // 发送创建会话请求
    const response = await fetch(`${API_BASE_URL}/chat/conversations`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(requestData)
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error(`创建会话失败: ${response.status}`, errorText);
      throw new Error(`创建会话失败: ${response.status} - ${errorText}`);
    }
    
    const newConversation = await response.json();
    console.log('服务器返回的新会话:', newConversation);
    
    // 格式化会话对象
    const formattedConversation: Conversation = {
      id: newConversation.id,
      title: newConversation.title,
      user: {
        id: userId,
        name: newConversation.customer?.username || "未知用户",
        avatar: newConversation.customer?.avatar || '/avatars/user.png',
        tags: []
      },
      unreadCount: 0,
      updatedAt: newConversation.updated_at
    };
    
    // 更新本地会话列表
    conversations.unshift(formattedConversation);
    
    return formattedConversation;
  } catch (error) {
    console.error("创建会话失败:", error);
    throw error;
  }
};

// 获取最近的会话
export const getRecentConversation = async (): Promise<Conversation | null> => {
  try {
    // 先获取所有会话
    const allConversations = await getConversations();
    
    // 如果没有会话，返回null
    if (!allConversations || allConversations.length === 0) {
      return null;
    }
    
    // 按更新时间排序，返回最近的会话
    return allConversations.sort((a, b) => {
      const dateA = new Date(a.updatedAt || '').getTime();
      const dateB = new Date(b.updatedAt || '').getTime();
      return dateB - dateA;
    })[0];
  } catch (error) {
    console.error("获取最近会话失败:", error);
    return null;
  }
};

// 获取或创建会话
export const getOrCreateConversation = async (): Promise<Conversation> => {
  try {
    console.log('尝试获取现有会话或创建新会话...');
    
    try {
      // 先尝试获取会话列表，可能会抛出异常
      const allConversations = await getConversations();
      console.log(`成功获取会话列表，共 ${allConversations.length} 个会话`);
      
      // 检查最近会话是否存在且活跃
      if (allConversations && allConversations.length > 0) {
        // 按更新时间排序，获取最新的会话
        const sortedConversations = [...allConversations].sort((a, b) => {
          const dateA = new Date(a.updatedAt || '').getTime();
          const dateB = new Date(b.updatedAt || '').getTime();
          return dateB - dateA;
        });
        
        const recentConversation = sortedConversations[0];
        console.log('找到最近的会话:', recentConversation.id);
        
        // 获取会话的最后活跃时间
        const lastActive = new Date(recentConversation.updatedAt || '').getTime();
        const now = new Date().getTime();
        const hoursDifference = (now - lastActive) / (1000 * 60 * 60);
        
        // 如果会话在24小时内有活动，则使用该会话
        if (hoursDifference < 24) {
          console.log(`该会话活跃于 ${hoursDifference.toFixed(2)} 小时前，复用该会话`);
          return recentConversation;
        } else {
          console.log(`该会话活跃于 ${hoursDifference.toFixed(2)} 小时前，需要创建新会话`);
        }
      } else {
        console.log('没有找到现有会话，将创建新会话');
      }
    } catch (error) {
      console.error('获取会话列表时出错，将尝试创建新会话:', error);
    }
    
    // 如果没有最近活跃的会话，创建新会话
    console.log('开始创建新会话...');
    return await createConversation();
  } catch (error) {
    console.error("获取或创建会话失败:", error);
    throw error;
  }
};

// 获取会话详情
export const getConversationDetails = async (conversationId: string): Promise<Conversation | null> => {
  try {
    // 获取认证令牌
    const token = authService.getToken();
    if (!token) {
      console.error("未登录，无法获取会话详情");
      return null;
    }
    
    // 从后端API获取会话详情
    const response = await fetch(`${API_BASE_URL}/chat/conversations/${conversationId}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      throw new Error(`获取会话详情失败: ${response.status}`);
    }
    
    const conv = await response.json();
    
    // 获取最后一条消息
    const messages = await getConversationMessages(conversationId);
    const lastMessage = messages.length > 0 ? messages[messages.length - 1] : undefined;
    
    // 格式化会话对象
    return {
      id: conv.id,
      title: conv.title,
      user: {
        id: conv.customer_id,
        name: conv.customer?.username || "未知用户",
        avatar: conv.customer?.avatar || '/avatars/user.png',
        tags: []
      },
      lastMessage,
      unreadCount: 0,
      updatedAt: conv.updated_at
    };
  } catch (error) {
    console.error(`获取会话详情出错:`, error);
    return null;
  }
};

// 同步顾问接管状态
export const syncConsultantTakeoverStatus = async (conversationId: string): Promise<boolean> => {
  try {
    // 获取认证令牌
    const token = authService.getToken();
    if (!token) {
      console.error("未登录，无法获取顾问接管状态");
      return isConsultantMode(conversationId);
    }
    
    // 尝试从后端API获取会话状态
    try {
      const response = await fetch(`${API_BASE_URL}/chat/conversations/${conversationId}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error(`获取会话详情失败: ${response.status}`);
      }
      
      const convData = await response.json();
      
      // 检查会话是否包含控制状态字段
      if (convData && 'is_ai_controlled' in convData) {
        // 更新本地状态 - 注意这里的逻辑反转:
        // is_ai_controlled = true 表示AI控制 (顾问未接管)
        // is_ai_controlled = false 表示顾问控制 (顾问已接管)
        consultantTakeover[conversationId] = !convData.is_ai_controlled;
        console.log(`已同步会话${conversationId}的顾问接管状态: ${!convData.is_ai_controlled}`);
      }
    } catch (error) {
      console.error(`获取会话接管状态失败:`, error);
      // 如果API不支持，使用本地状态
    }
    
    return isConsultantMode(conversationId);
  } catch (error) {
    console.error("同步顾问接管状态失败:", error);
    return isConsultantMode(conversationId);
  }
}; 