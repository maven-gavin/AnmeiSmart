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

// 添加用于跟踪最后连接的会话ID
let lastConnectedConversationId: string | null = null;

// 用于取消连接尝试的计时器
let connectionDebounceTimer: NodeJS.Timeout | null = null;

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

// 保存已处理的消息ID，避免重复处理
const processedMessageIds = new Set<string>();

// 初始化WebSocket连接
export const initializeWebSocket = (userId: string, conversationId: string) => {
  if (!userId || !conversationId) {
    console.error('初始化WebSocket失败: 缺少用户ID或会话ID');
    return;
  }
  
  console.log(`初始化WebSocket连接: 用户ID=${userId}, 会话ID=${conversationId}`);
  
  // 检查认证状态
  if (!authService.isLoggedIn()) {
    console.error('初始化WebSocket失败: 用户未登录');
    return;
  }
  
  // 设置重试次数上限，避免无限重试
  reconnectAttempts = 0;
  
  // 关闭现有连接
  if (socket) {
    try {
      console.log('关闭现有WebSocket连接');
      closeWebSocketConnection();
    } catch (err) {
      console.warn('关闭现有连接时出错:', err);
    }
  }
  
  // 建立新连接
  return establishWebSocketConnection(userId, conversationId);
};

// 实际建立WebSocket连接的函数
const establishWebSocketConnection = (userId: string, conversationId: string) => {
  // 标记当前会话ID，用于防止在会话切换过程中发生的重复连接
  let isCancelled = false;
  
  // 如果已经连接到相同的会话，则不需要重新连接
  if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
    if (socket._conversationId === conversationId) {
      console.log(`WebSocket已连接到会话${conversationId}，不需要重新连接`);
      return;
    } else {
      console.log(`WebSocket已连接到会话${socket._conversationId}，但需要切换到会话${conversationId}，关闭当前连接`);
      try {
        closeWebSocketConnection();
      } catch (err) {
        console.warn('关闭已有连接时出错:', err);
      }
    }
  }
  
  if (isConnecting) {
    console.log('WebSocket正在连接中，请稍候...');
    return; // 防止多次同时连接
  }
  
  // 更新最后连接的会话ID
  lastConnectedConversationId = conversationId;
  
  isConnecting = true;
  connectionStatus = ConnectionStatus.CONNECTING;
  
  // 使用验证后的有效token，而不是直接获取
  const getValidTokenAndConnect = async () => {
    try {
      // 获取令牌
      const token = authService.getToken();
      let tokenToUse = token;
      
      if (!token) {
        console.warn('无法获取令牌，尝试自动登录或刷新令牌');
        // 尝试通过 getValidToken 获取或刷新令牌
        tokenToUse = await authService.getValidToken();
        if (!tokenToUse) {
          console.error('无法建立WebSocket连接：未能获取有效令牌');
          connectionStatus = ConnectionStatus.ERROR;
          isConnecting = false;
          return;
        }
      }
      
      // 构建WebSocket URL
      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsHost = process.env.NEXT_PUBLIC_WS_URL || 'localhost:8000';
      const wsUrl = `${wsProtocol}//${wsHost}/api/v1/chat/ws/${userId}?token=${encodeURIComponent(tokenToUse || '')}&conversation_id=${conversationId}`;
      
      console.log(`尝试连接WebSocket: 用户ID=${userId}, 会话ID=${conversationId}`);
      
      // 添加连接超时处理
      const connectionTimeoutId = setTimeout(() => {
        if (isCancelled) return;
        
        if (connectionStatus === ConnectionStatus.CONNECTING) {
          console.error('WebSocket连接超时');
          connectionStatus = ConnectionStatus.ERROR;
          isConnecting = false;
          
          // 如果socket存在但尚未连接，则关闭它
          if (socket && socket.readyState === WebSocket.CONNECTING) {
            socket.close();
            socket = null;
          }
        }
      }, 10000); // 10秒连接超时
      
      socket = new WebSocket(wsUrl);
      // 保存会话ID到socket对象以便后续检查
      socket._conversationId = conversationId;
      
      socket.onopen = () => {
        // 检查会话ID是否仍然是最新的
        if (lastConnectedConversationId !== conversationId) {
          console.log(`WebSocket连接已建立，但会话ID已变更 (${conversationId} -> ${lastConnectedConversationId})，关闭连接`);
          socket?.close();
          clearTimeout(connectionTimeoutId);
          isConnecting = false;
          return;
        }
        
        if (isCancelled) {
          console.log(`WebSocket连接已建立，但会话已被取消，关闭连接，会话ID: ${conversationId}`);
          socket?.close();
          clearTimeout(connectionTimeoutId);
          isConnecting = false;
          return;
        }
        
        clearTimeout(connectionTimeoutId); // 清除连接超时
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
        
        // 发送队列中的消息，只发送当前会话的消息
        if (messageQueue.length > 0) {
          console.log(`处理消息队列，当前有${messageQueue.length}条消息`);
          const currentSessionMessages = messageQueue.filter(msg => msg.conversation_id === conversationId);
          const otherSessionMessages = messageQueue.filter(msg => msg.conversation_id !== conversationId);
          
          // 移除其他会话的消息
          if (otherSessionMessages.length > 0) {
            console.log(`丢弃${otherSessionMessages.length}条其他会话的消息`);
            messageQueue.length = 0;
            messageQueue.push(...currentSessionMessages);
          }
          
          // 发送当前会话的消息
          while (messageQueue.length > 0 && socket && socket.readyState === WebSocket.OPEN) {
            const message = messageQueue.shift();
            console.log('发送队列中的消息:', message);
            socket.send(JSON.stringify(message));
          }
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
          }
        }, HEARTBEAT_INTERVAL);
        
        // 重连成功后主动同步数据
        if (reconnectAttempts > 0) {
          console.log(`WebSocket重连成功，同步会话数据，会话ID: ${conversationId}`);
          syncChatData(conversationId).catch(err => 
            console.error(`重连后同步数据失败: ${err}`)
          );
        }
      };
      
      socket.onmessage = (event) => {
        // 检查会话ID是否仍然是最新的
        if (lastConnectedConversationId !== conversationId) {
          console.log(`收到WebSocket消息，但会话ID已变更，忽略消息`);
          return;
        }
        
        if (isCancelled) return;
        
        try {
          console.log('收到WebSocket消息:', event.data);
          const data = JSON.parse(event.data);
          handleWebSocketMessage(data);
        } catch (error) {
          console.error('处理WebSocket消息时出错:', error);
        }
      };
      
      socket.onerror = (error) => {
        if (isCancelled) return;
        
        clearTimeout(connectionTimeoutId); // 清除连接超时
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
        if (isCancelled) return;
        
        clearTimeout(connectionTimeoutId); // 清除连接超时
        console.log(`WebSocket连接已关闭: 代码=${event.code}, 原因=${event.reason || '未提供'}, 是否干净关闭=${event.wasClean}`);
        connectionStatus = ConnectionStatus.DISCONNECTED;
        isConnecting = false;
        
        // 清除心跳
        if (heartbeatInterval) {
          clearInterval(heartbeatInterval);
          heartbeatInterval = null;
        }
        
        // 只有在非用户主动关闭的情况下尝试重连
        if (event.code !== 1000 && event.code !== 1001) {
          // 检查是否仍然是最新的会话ID
          if (lastConnectedConversationId === conversationId && reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
            reconnectAttempts++;
            const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000); // 指数退避，最大30秒
            console.log(`将在${delay}ms后尝试重连，尝试次数: ${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS}`);
            
            setTimeout(() => {
              if (lastConnectedConversationId === conversationId) {
                console.log(`尝试重新连接WebSocket，会话ID: ${conversationId}`);
                establishWebSocketConnection(userId, conversationId);
              } else {
                console.log(`不再重连到会话${conversationId}，因为当前会话已变为${lastConnectedConversationId}`);
              }
            }, delay);
          }
        }
      };
      
      // 返回取消函数，可以用于组件卸载或会话切换时取消连接
      return () => {
        console.log(`标记WebSocket连接为已取消，会话ID: ${conversationId}`);
        isCancelled = true;
        clearTimeout(connectionTimeoutId);
        // 不主动关闭连接，让onopen处理器决定是否关闭
      };
    } catch (error) {
      console.error('获取令牌或建立连接时出错:', error);
      connectionStatus = ConnectionStatus.ERROR;
      isConnecting = false;
      
      // 延迟后重试连接
      setTimeout(() => {
        if (lastConnectedConversationId === conversationId) {
          console.log('尝试重新建立WebSocket连接');
          establishWebSocketConnection(userId, conversationId);
        }
      }, 5000); // 5秒后重试
    }
  };
  
  // 启动连接流程
  getValidTokenAndConnect();
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
  
  // 清除连接防抖计时器
  if (connectionDebounceTimer) {
    clearTimeout(connectionDebounceTimer);
    connectionDebounceTimer = null;
  }
  
  // 获取当前连接的会话ID便于日志
  const currentConversationId = socket?._conversationId;
  
  if (socket) {
    try {
      // 记录关闭时的状态
      const previousReadyState = socket.readyState;
      
      // 只有在连接或连接中的状态才需要关闭
      if (previousReadyState === WebSocket.OPEN || previousReadyState === WebSocket.CONNECTING) {
        console.log(`关闭WebSocket连接，会话ID: ${currentConversationId}, 状态: ${previousReadyState}`);
        socket.close();
      } else {
        console.log(`WebSocket已经处于关闭状态，会话ID: ${currentConversationId}, 状态: ${previousReadyState}`);
      }
    } catch (error) {
      console.error('关闭WebSocket连接时出错:', error);
    }
    socket = null;
  } else {
    console.log('WebSocket连接不存在，无需关闭');
  }
  
  connectionStatus = ConnectionStatus.DISCONNECTED;
  isConnecting = false;
  
  // 清空消息队列，避免切换会话时发送旧消息
  if (messageQueue.length > 0) {
    console.log(`清空消息队列，丢弃${messageQueue.length}条消息`);
    messageQueue.length = 0;
  }
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
  
  // 确保使用用户的当前角色，避免角色混淆
  const userRole = currentUser.currentRole || 'customer';
  
  console.log(`发送文本消息: 会话ID=${conversationId}, 用户ID=${currentUser.id}, 角色=${userRole}`);
  console.log(`WebSocket状态: ${connectionStatus}, 连接状态: ${socket?.readyState}`);
  
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
  // 如果有本地缓存，先返回缓存数据
  const cachedMessages = chatMessages[conversationId] || [];
  
  try {
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
  }
};

// 获取所有会话
export const getConversations = async (): Promise<Conversation[]> => {
  try {
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
        const messages = await getConversationMessages(conv.id);
        if (messages.length > 0) {
          lastMessage = messages[messages.length - 1];
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
    
    return formattedConversations;
  } catch (error) {
    console.error(`获取会话列表出错:`, error);
    // 如果是认证错误，不返回缓存数据，而是抛出异常
    if (error instanceof Error && error.message.includes('401')) {
      throw error;
    }
    // 其他错误返回缓存数据
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
    
    // 发送创建会话请求
    const response = await fetch(`${API_BASE_URL}/chat/conversations`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        customer_id: userId,
        title: `咨询会话 ${new Date().toLocaleDateString()}`
      })
    });
    
    if (!response.ok) {
      throw new Error(`创建会话失败: ${response.status}`);
    }
    
    const newConversation = await response.json();
    
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
    
    // 初始化WebSocket连接
    const user = authService.getCurrentUser();
    if (user) {
      initializeWebSocket(user.id, formattedConversation.id);
    }
    
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
    // 先尝试获取最近的会话
    const recentConversation = await getRecentConversation();
    
    // 检查最近会话是否存在且活跃
    if (recentConversation) {
      // 获取会话的最后活跃时间
      const lastActive = new Date(recentConversation.updatedAt || '').getTime();
      const now = new Date().getTime();
      const hoursDifference = (now - lastActive) / (1000 * 60 * 60);
      
      // 如果会话在24小时内有活动，则使用该会话
      if (hoursDifference < 24) {
        return recentConversation;
      }
    }
    
    // 如果没有最近活跃的会话，创建新会话
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