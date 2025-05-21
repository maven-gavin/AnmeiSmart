import { Message, Conversation, CustomerProfile } from "@/types/chat";
import { v4 as uuidv4 } from 'uuid';
import { authService } from "./authService";

// 扩展WebSocket接口，添加自定义属性
interface CustomWebSocket extends WebSocket {
  _conversationId?: string;
}

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

// WebSocket连接
let socket: CustomWebSocket | null = null;
let isConnecting = false;
const messageQueue: any[] = [];
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;
let heartbeatInterval: NodeJS.Timeout | null = null;
const HEARTBEAT_INTERVAL = 30000; // 30秒发送一次心跳

// 消息回调处理函数
type MessageCallback = (message: any) => void;
const messageCallbacks: Record<string, MessageCallback[]> = {};

// WebSocket连接状态
export enum ConnectionStatus {
  DISCONNECTED = 'disconnected',
  CONNECTING = 'connecting',
  CONNECTED = 'connected',
  ERROR = 'error'
}

let connectionStatus = ConnectionStatus.DISCONNECTED;

// 初始化WebSocket连接
export const initializeWebSocket = (userId: string, conversationId: string) => {
  // 如果传入的会话ID为空，使用一个安全默认值
  if (!conversationId) {
    console.error('初始化WebSocket时会话ID为空，使用默认值"1"');
    conversationId = "1";
  }

  if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
    // 如果已经连接到相同的会话，则不需要重新连接
    if (socket._conversationId === conversationId) {
      console.log(`WebSocket已连接到会话${conversationId}，不需要重新连接`);
      return;
    } else {
      console.log(`WebSocket已连接到会话${socket._conversationId}，但需要切换到会话${conversationId}，关闭当前连接`);
      try {
        closeWebSocketConnection();
        console.log('关闭已有WebSocket连接以切换会话');
      } catch (err) {
        console.warn('关闭已有连接时出错:', err);
      }
    }
  }
  
  if (isConnecting) {
    console.log('WebSocket正在连接中，请稍候...');
    return; // 防止多次同时连接
  }
  
  isConnecting = true;
  connectionStatus = ConnectionStatus.CONNECTING;
  
  const token = authService.getToken();
  if (!token) {
    console.error('无法建立WebSocket连接：未登录');
    connectionStatus = ConnectionStatus.ERROR;
    isConnecting = false;
    return;
  }
  
  // 建立连接
  try {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsHost = process.env.NEXT_PUBLIC_WS_URL || 'localhost:8000';
    const wsUrl = `${wsProtocol}//${wsHost}/api/v1/chat/ws/${userId}?token=${encodeURIComponent(token)}&conversation_id=${conversationId}`;
    
    console.log(`尝试连接WebSocket: 用户ID=${userId}, 会话ID=${conversationId}, URL=${wsUrl}`);
    
    socket = new WebSocket(wsUrl);
    // 保存会话ID到socket对象以便后续检查
    socket._conversationId = conversationId;
    
    socket.onopen = () => {
      console.log(`WebSocket连接已建立，会话ID: ${conversationId}`);
      connectionStatus = ConnectionStatus.CONNECTED;
      isConnecting = false;
      reconnectAttempts = 0;
      
      // 发送连接消息
      if (socket && socket.readyState === WebSocket.OPEN) {
        const connectMsg = {
          action: 'connect',
          conversation_id: conversationId,
          timestamp: new Date().toISOString()
        };
        console.log('发送WebSocket连接消息:', connectMsg);
        socket.send(JSON.stringify(connectMsg));
      }
      
      // 发送队列中的消息
      while (messageQueue.length > 0 && socket && socket.readyState === WebSocket.OPEN) {
        const message = messageQueue.shift();
        console.log('发送队列中的消息:', message);
        socket.send(JSON.stringify(message));
      }
      
      // 启动心跳检测
      if (heartbeatInterval) {
        clearInterval(heartbeatInterval);
      }
      
      heartbeatInterval = setInterval(() => {
        if (socket && socket.readyState === WebSocket.OPEN) {
          // 心跳消息中也包含会话ID
          socket.send(JSON.stringify({
            action: 'ping',
            conversation_id: conversationId,
            timestamp: new Date().toISOString()
          }));
        } else {
          if (heartbeatInterval) {
            clearInterval(heartbeatInterval);
            heartbeatInterval = null;
          }
          
          // 如果连接已关闭但状态未更新，尝试重连
          if (connectionStatus !== ConnectionStatus.DISCONNECTED && 
              connectionStatus !== ConnectionStatus.ERROR) {
            console.log('心跳检测到连接已关闭，更新状态');
            connectionStatus = ConnectionStatus.DISCONNECTED;
            
            // 尝试重连
            if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
              reconnectAttempts++;
              console.log(`心跳触发重连 (尝试 ${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})`);
              setTimeout(() => {
                initializeWebSocket(userId, conversationId);
              }, 1000);
            }
          }
        }
      }, HEARTBEAT_INTERVAL);
    };
    
    socket.onmessage = (event) => {
      try {
        console.log('收到WebSocket消息:', event.data);
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
      } catch (error) {
        console.error('处理WebSocket消息时出错:', error);
      }
    };
    
    socket.onerror = (error) => {
      console.error('WebSocket错误:', error);
      // 添加更详细的错误信息
      console.error('WebSocket状态:', socket?.readyState);
      console.error('WebSocket URL:', wsUrl);
      console.error('用户ID:', userId);
      console.error('会话ID:', conversationId);
      
      // 检查网络连接
      console.log('检查网络连接:', navigator.onLine ? '在线' : '离线');
      
      connectionStatus = ConnectionStatus.ERROR;
      isConnecting = false;
    };
    
    socket.onclose = (event) => {
      console.log(`WebSocket连接已关闭: 代码=${event.code}, 原因=${event.reason || '未提供'}, 是否干净关闭=${event.wasClean}`);
      connectionStatus = ConnectionStatus.DISCONNECTED;
      isConnecting = false;
      
      // 清除心跳
      if (heartbeatInterval) {
        clearInterval(heartbeatInterval);
        heartbeatInterval = null;
      }
      
      // 尝试重连
      if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
        reconnectAttempts++;
        const delay = 1000 * Math.pow(2, reconnectAttempts); // 指数退避重连
        console.log(`${delay}ms后尝试重连 (尝试 ${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})`);
        
        setTimeout(() => {
          initializeWebSocket(userId, conversationId);
        }, delay);
      } else {
        console.error(`达到最大重连尝试次数 (${MAX_RECONNECT_ATTEMPTS}), 停止重连`);
      }
    };
  } catch (error) {
    console.error('初始化WebSocket时出错:', error);
    connectionStatus = ConnectionStatus.ERROR;
    isConnecting = false;
  }
};

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

// 修改handleWebSocketMessage函数，增加数据同步逻辑
const handleWebSocketMessage = (data: any) => {
  try {
    const { action, conversation_id } = data;
    
    // 如果是消息相关的动作，触发同步
    if (action === 'message' || action === 'connect') {
      // 异步同步数据，不阻塞消息处理
      syncChatData(conversation_id).catch(console.error);
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
  
  // 尝试通过WebSocket发送消息
  if (socket && socket.readyState === WebSocket.OPEN) {
    try {
      console.log(`WebSocket已连接，直接发送消息到会话 ${conversationId}`);
      
      // 检查当前socket的会话ID是否与要发送的消息会话ID一致
      if (socket._conversationId !== conversationId) {
        console.warn(`当前WebSocket连接的会话ID(${socket._conversationId})与要发送消息的会话ID(${conversationId})不一致，将重新连接`);
        // 关闭当前连接并重新建立连接
        closeWebSocketConnection();
        
        // 将消息加入队列
        messageQueue.push(message);
        
        // 尝试为正确的会话建立连接
        const user = authService.getCurrentUser();
        if (user) {
          initializeWebSocket(user.id, conversationId);
        }
        
        return false;
      }
      
      const messageString = JSON.stringify(message);
      socket.send(messageString);
      return true;
    } catch (error) {
      console.error('发送WebSocket消息时出错:', error);
      // 发送失败，将消息加入队列
      messageQueue.push(message);
      
      // 尝试重新连接
      const user = authService.getCurrentUser();
      if (user) {
        console.log(`发送失败，尝试重新连接WebSocket，会话ID: ${conversationId}`);
        setTimeout(() => {
          initializeWebSocket(user.id, conversationId);
        }, 1000);
      }
      return false;
    }
  } else {
    console.log(`WebSocket未连接或未就绪，将消息加入队列`);
    // 如果连接未建立，将消息加入队列
    messageQueue.push(message);
    
    // 尝试建立连接
    if (connectionStatus === ConnectionStatus.DISCONNECTED && !isConnecting) {
      const user = authService.getCurrentUser();
      console.log(`尝试为用户${user?.id}建立WebSocket连接，会话ID: ${conversationId}`);
      if (user) {
        initializeWebSocket(user.id, conversationId);
      }
    }
    return false;
  }
};

// 关闭WebSocket连接
export const closeWebSocketConnection = () => {
  // 清除心跳
  if (heartbeatInterval) {
    clearInterval(heartbeatInterval);
    heartbeatInterval = null;
  }
  
  if (socket) {
    try {
      socket.close();
    } catch (error) {
      console.error('关闭WebSocket连接时出错:', error);
    }
    socket = null;
  }
  connectionStatus = ConnectionStatus.DISCONNECTED;
  isConnecting = false;
  console.log('WebSocket连接已关闭');
};

// 获取连接状态
export const getConnectionStatus = () => {
  return connectionStatus;
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
  
  console.log(`发送文本消息: 会话ID=${conversationId}, 用户ID=${currentUser.id}, 角色=${currentUser.currentRole}`);
  console.log(`WebSocket状态: ${connectionStatus}, 连接状态: ${socket?.readyState}`);
  
  // 创建用户消息
  const userMessage: Message = {
    id: `m_${uuidv4()}`,
    content,
    type: 'text',
    sender: {
      id: currentUser.id,
      type: currentUser.currentRole || 'customer',
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
      sender_type: currentUser.currentRole || 'customer'
    },
    conversation_id: conversationId,
    timestamp: new Date().toISOString()
  };
  
  console.log(`准备通过WebSocket发送消息，会话ID: ${conversationId}`, wsMessage);
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
  // 如果有本地缓存，先返回缓存数据
  const cachedMessages = chatMessages[conversationId] || [];
  
  try {
    // 获取认证令牌
    const token = authService.getToken();
    if (!token) {
      console.error("未登录，无法获取会话消息");
      return cachedMessages;
    }
    
    // 从后端API获取消息
    const response = await fetch(`${API_BASE_URL}/chat/conversations/${conversationId}/messages`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      throw new Error(`获取消息失败: ${response.status}`);
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
    
    return formattedMessages;
  } catch (error) {
    console.error(`获取会话消息出错:`, error);
    // 出错时返回缓存数据
    return cachedMessages;
  }
};

// 获取所有会话
export const getConversations = async (): Promise<Conversation[]> => {
  try {
    // 获取认证令牌
    const token = authService.getToken();
    if (!token) {
      console.error("未登录，无法获取会话列表");
      return conversations;
    }
    
    // 从后端API获取会话列表
    const response = await fetch(`${API_BASE_URL}/chat/conversations`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      throw new Error(`获取会话列表失败: ${response.status}`);
    }
    
    const data = await response.json();
    
    // 转换格式，适配前端格式
    const formattedConversations: Conversation[] = await Promise.all(data.map(async (conv: any) => {
      // 获取最后一条消息
      let lastMessage: Message | undefined;
      const messages = await getConversationMessages(conv.id);
      if (messages.length > 0) {
        lastMessage = messages[messages.length - 1];
      }
      
      return {
        id: conv.id,
        title: conv.title,
        user: {
          id: conv.customer_id,
          name: conv.customer?.username || "未知用户",
          avatar: conv.customer?.avatar || '/avatars/user.png',
          tags: []
        },
        lastMessage: lastMessage,
        unreadCount: 0, // TODO: 实现未读消息计数
        updatedAt: conv.updated_at
      };
    }));
    
    // 更新本地缓存
    conversations = formattedConversations;
    
    return formattedConversations;
  } catch (error) {
    console.error(`获取会话列表出错:`, error);
    // 出错时返回缓存数据
    return conversations;
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
  
  return true;
};

// 是否处于顾问模式
export const isConsultantMode = (conversationId: string): boolean => {
  return !!consultantTakeover[conversationId];
}; 