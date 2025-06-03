import { Message, Conversation, CustomerProfile, Customer, ConsultationHistoryItem } from "@/types/chat";
import { v4 as uuidv4 } from 'uuid';
import { authService } from "./authService";
// 引入新的WebSocket客户端架构
import { getWebSocketClient, ConnectionStatus, WebSocketClient } from './websocket';
import { SenderType } from './websocket/types';
import { TextMessageHandler } from './websocket/handlers/textHandler';
import { SystemMessageHandler } from './websocket/handlers/systemHandler';

// 常量定义
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';
const MESSAGES_CACHE_TIME = 5000; // 5秒缓存时间
const CONVERSATIONS_CACHE_TIME = 10000; // 10秒缓存时间

// AI和系统用户信息
const aiInfo = {
  id: 'ai_assistant',
  name: 'AI助手',
  avatar: '/avatars/ai.png',
  type: 'ai' as const,
};

const systemInfo = {
  id: 'system',
  name: '系统',
  avatar: '/avatars/system.png',
  type: 'system' as const,
};

// 缓存和状态管理
class ChatState {
  private chatMessages: Record<string, Message[]> = {};
  private conversations: Conversation[] = [];
  private consultantTakeover: Record<string, boolean> = {};
  private messageQueue: any[] = [];
  private lastConnectedConversationId: string | null = null;
  private connectionDebounceTimer: NodeJS.Timeout | null = null;
  private messageCallbacks: Record<string, ((message: any) => void)[]> = {};
  private processedMessageIds = new Set<string>();
  private isRequestingMessages: Record<string, boolean> = {};
  private lastMessagesRequestTime: Record<string, number> = {};
  private isRequestingConversations = false;
  private lastConversationsRequestTime = 0;
  
  // 单例实例
  private static instance: ChatState;
  
  private constructor() {}
  
  public static getInstance(): ChatState {
    if (!ChatState.instance) {
      ChatState.instance = new ChatState();
    }
    return ChatState.instance;
  }
  
  // Getter和Setter方法
  public getChatMessages(conversationId: string): Message[] {
    return this.chatMessages[conversationId] || [];
  }
  
  public setChatMessages(conversationId: string, messages: Message[]): void {
    this.chatMessages[conversationId] = messages;
  }
  
  public addMessage(conversationId: string, message: Message): void {
    if (!this.chatMessages[conversationId]) {
      this.chatMessages[conversationId] = [];
    }
    // Avoid duplicates based on message ID if messages are coming too fast or from multiple sources
    if (!this.chatMessages[conversationId].some(m => m.id === message.id)) {
      this.chatMessages[conversationId].push(message);
    }
    
    this.updateConversationLastMessage(conversationId, message);
  }
  
  public updateConversationLastMessage(conversationId: string, message: Message): void {
    const conversationIndex = this.conversations.findIndex(conv => conv.id === conversationId);
    if (conversationIndex >= 0) {
      this.conversations[conversationIndex] = {
        ...this.conversations[conversationIndex],
        lastMessage: message,
        updatedAt: message.timestamp,
      };
    }
  }
  
  public getConversations(): Conversation[] {
    return this.conversations;
  }
  
  public setConversations(conversations: Conversation[]): void {
    this.conversations = conversations;
  }
  
  public isConsultantTakeover(conversationId: string): boolean {
    return !!this.consultantTakeover[conversationId];
  }
  
  public setConsultantTakeover(conversationId: string, value: boolean): void {
    this.consultantTakeover[conversationId] = value;
  }
  
  public getMessageQueue(): any[] {
    return this.messageQueue;
  }
  
  public addToMessageQueue(message: any): void {
    this.messageQueue.push(message);
  }
  
  public clearMessageQueue(): void {
    this.messageQueue.length = 0;
  }
  
  public getLastConnectedConversationId(): string | null {
    return this.lastConnectedConversationId;
  }
  
  public setLastConnectedConversationId(id: string | null): void {
    this.lastConnectedConversationId = id;
  }
  
  public getConnectionDebounceTimer(): NodeJS.Timeout | null {
    return this.connectionDebounceTimer;
  }
  
  public setConnectionDebounceTimer(timer: NodeJS.Timeout | null): void {
    this.connectionDebounceTimer = timer;
  }
  
  public addMessageCallback(action: string, callback: (message: any) => void): void {
    if (!this.messageCallbacks[action]) {
      this.messageCallbacks[action] = [];
    }
    this.messageCallbacks[action].push(callback);
  }
  
  public removeMessageCallback(action: string, callback: (message: any) => void): void {
    if (this.messageCallbacks[action]) {
      this.messageCallbacks[action] = this.messageCallbacks[action].filter(cb => cb !== callback);
    }
  }
  
  public getMessageCallbacks(action: string): ((message: any) => void)[] {
    return this.messageCallbacks[action] || [];
  }
  
  public addProcessedMessageId(id: string): void {
    this.processedMessageIds.add(id);
  }
  
  public hasProcessedMessageId(id: string): boolean {
    return this.processedMessageIds.has(id);
  }
  
  public setRequestingMessages(conversationId: string, value: boolean): void {
    this.isRequestingMessages[conversationId] = value;
  }
  
  public isRequestingMessagesForConversation(conversationId: string): boolean {
    return !!this.isRequestingMessages[conversationId];
  }
  
  public updateMessagesRequestTime(conversationId: string): void {
    this.lastMessagesRequestTime[conversationId] = Date.now();
  }
  
  public getMessagesRequestTime(conversationId: string): number {
    return this.lastMessagesRequestTime[conversationId] || 0;
  }
  
  public setRequestingConversations(value: boolean): void {
    this.isRequestingConversations = value;
  }
  
  public isRequestingConversationsState(): boolean {
    return this.isRequestingConversations;
  }
  
  public updateConversationsRequestTime(): void {
    this.lastConversationsRequestTime = Date.now();
  }
  
  public getConversationsRequestTime(): number {
    return this.lastConversationsRequestTime;
  }
}

// 获取状态实例
const chatState = ChatState.getInstance();

// WebSocket初始化和管理
/**
 * 初始化WebSocket连接
 * @param userId 用户ID
 * @param conversationId 会话ID
 */
export async function initializeWebSocket(userId: string, conversationId: string): Promise<void> {
  try {
    // 获取当前用户信息和角色
    const token = await authService.getValidToken();
    const userRole = authService.getCurrentUserRole() || '';
    
    // 如果token无效，不尝试连接
    if (!token) {
      console.log('Token无效或不存在，不尝试WebSocket连接');
      return;
    }
    
    // 准备连接参数
    const connectionParams = {
      userId,
      conversationId,
      token,
      userType: mapUserRoleToSenderType(userRole),
      connectionId: `${userId}_${conversationId}_${Date.now()}`
    };
    
    console.log('初始化WebSocket连接:', connectionParams);
    
    // 获取WebSocket客户端
    const wsClient = getWsClient();
    if (!wsClient) {
      console.error('initializeWebSocket: WebSocket客户端实例无效，无法连接。');
      return; // Exit if client is null
    }
    
    // 连接到WebSocket服务器
    // 使用更可靠的Promise处理
    try {
      await wsClient.connect(connectionParams);
      console.log('WebSocket连接成功建立');
    } catch (connectError: any) {
      console.error('WebSocket连接尝试失败:', connectError);
      
      // 连接失败，不设置防抖计时器，让UI可以立即重试
      if (connectError?.message && connectError.message.includes('401')) {
        console.error('WebSocket连接失败: 认证失败 (401)');
      }
    }
  } catch (error) {
    console.error('初始化WebSocket连接出错:', error);
  }
}

// 将UserRole映射到SenderType
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

// 获取WebSocket客户端实例
const getWsClient = (): WebSocketClient | null => {
  try {
    // 尝试获取已初始化的客户端实例
    return getWebSocketClient(); 
  } catch (error: any) {
    // 如果错误是 "WebSocketClient未初始化"，则尝试用默认配置初始化它
    if (error.message && error.message.includes('WebSocketClient未初始化')) {
      console.warn('getWsClient: WebSocketClient未初始化，尝试使用默认配置创建新实例。', error);
      try {
        return initializeWebSocketClient(); 
      } catch (initError) {
        console.error('getWsClient: 尝试初始化WebSocketClient失败:', initError);
        return null;
      }
    } else {
      // 其他类型的错误
      console.error('getWsClient: 获取WebSocket客户端实例时发生未知错误:', error);
      return null;
    }
  }
};

// 修改初始化WebSocket客户端函数，确保URL正确性
const initializeWebSocketClient = () => {
  try {
    // 获取协议
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    
    // 使用环境变量或回退到当前主机，并移除端口3000
    let wsHost = process.env.NEXT_PUBLIC_WS_URL || window.location.host;
    
    // 如果是localhost:3000，替换为正确的API端口
    if (wsHost === 'localhost:3000') {
      wsHost = 'localhost:8000';
    } else if (wsHost.includes(':3000')) {
      // 替换前端端口3000为后端端口8000
      wsHost = wsHost.replace(':3000', ':8000');
    }
    
    console.log('使用WebSocket主机:', wsHost);
    
    // 确保URL非空
    if (!wsHost) {
      throw new Error('WebSocket主机未配置');
    }
    
    // 修改这里，确保路径中不包含多余的ws部分，让WebSocketClient处理
    // 路径应该是 /api/v1/chat，而不是 /api/v1/chat/ws
    const baseUrl = `${wsProtocol}//${wsHost}/api/v1/chat`;
    console.log('WebSocket连接基础URL:', baseUrl);
    
    // 获取客户端实例，使用明确的配置
    const wsClient = getWebSocketClient({
      url: baseUrl,
      reconnectAttempts: 5,       // 5次重连尝试
      reconnectInterval: 2000,    // 2秒重连间隔
      heartbeatInterval: 30000,   // 30秒心跳
      connectionTimeout: 8000,    // 8秒连接超时
      debug: true                 // 开启调试日志
    });
    
    // 注册消息处理器
    wsClient.registerHandler(new TextMessageHandler());
    wsClient.registerHandler(new SystemMessageHandler());
    
    // 添加处理器的回调
    const textHandler = wsClient.getHandlers().find(h => h.getName() === 'TextMessageHandler');
    if (textHandler) {
      textHandler.addCallback('message', (data: any) => {
        console.log('收到文本消息:', data);
        handleWebSocketMessage(data);
      });
    }
    
    const systemHandler = wsClient.getHandlers().find(h => h.getName() === 'SystemMessageHandler');
    if (systemHandler) {
      systemHandler.addCallback('system', (data: any) => {
        console.log('收到系统消息:', data);
        handleWebSocketMessage(data);
      });
    }

    // 添加状态变更监听
    wsClient.addConnectionStatusListener((event: any) => {
      console.log('WebSocketClient状态变更:', event);
    });
    
    return wsClient;
  } catch (error) {
    console.error('初始化WebSocket客户端失败:', error);
    throw error;
  }
};

// 处理WebSocket消息
const handleWebSocketMessage = (data: any) => {
  try {
    // 检查基本动作类型
    const action = data.action;
    
    // 检查必要的会话ID
    if (data.conversation_id) {
      // 如果是消息相关的动作，触发同步
      if (action === 'message' || action === 'connect' || action === 'system') {
        // 异步同步数据，不阻塞消息处理
        syncChatData(data.conversation_id).catch((error: Error) => 
          console.error(`同步会话数据失败: ${error.message}`)
        );
      }
    }
    
    // 调用注册的回调函数
    const callbacks = chatState.getMessageCallbacks(action);
    if (callbacks.length > 0) {
      callbacks.forEach(callback => {
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

// 同步聊天数据
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

// 添加消息回调
export const addMessageCallback = (action: string, callback: (message: any) => void) => {
  chatState.addMessageCallback(action, callback);
};

// 移除消息回调
export const removeMessageCallback = (action: string, callback: (message: any) => void) => {
  chatState.removeMessageCallback(action, callback);
};

// 发送WebSocket消息
export const sendWebSocketMessage = (message: any) => {
  console.log(`准备通过WebSocket发送消息:`, message);
  if (!message.conversation_id) {
    console.error('发送的消息没有会话ID，无法继续');
    return false;
  }
  const conversationId = message.conversation_id;
  
  try {
    const wsClient = getWsClient();
    if (!wsClient) {
      console.error('sendWebSocketMessage: WebSocket客户端实例无效，消息加入队列。');
      chatState.addToMessageQueue(message); // Still queue if client is not available
      return false;
    }

    if (wsClient.isConnected()) {
      const params = wsClient.getConnectionParams();
      if (params.conversationId !== conversationId) {
        console.warn(`当前WebSocket连接的会话ID(${params.conversationId})与要发送消息的会话ID(${conversationId})不一致，将重新连接`);
        
        // 将消息加入队列
        chatState.addToMessageQueue(message);
        
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
      chatState.addToMessageQueue(message);
      
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
    chatState.addToMessageQueue(message);
    
    return false;
  }
};

// 关闭WebSocket连接
export const closeWebSocketConnection = () => {
  const timer = chatState.getConnectionDebounceTimer();
  if (timer) {
    clearTimeout(timer);
    chatState.setConnectionDebounceTimer(null);
  }
  
  try {
    const wsClient = getWsClient();
    if (!wsClient) {
      console.warn('closeWebSocketConnection: WebSocket客户端实例无效，无需关闭。');
      return; // Exit if client is null
    }
    
    if (wsClient.isConnected()) {
      wsClient.disconnect();
      console.log('WebSocket连接已关闭');
    } else {
      console.log('WebSocket未连接，无需关闭');
    }
  } catch (error) {
    console.error('关闭WebSocket连接时出错:', error);
  }
  
  // 清空消息队列
  const messageQueue = chatState.getMessageQueue();
  if (messageQueue.length > 0) {
    console.log(`清空消息队列，丢弃${messageQueue.length}条消息`);
    chatState.clearMessageQueue();
  }
  
  // 清除最后连接的会话ID
  chatState.setLastConnectedConversationId(null);
};

// 获取连接状态（仅兜底用途，不建议在组件渲染体内直接用）
export const getConnectionStatus = (): ConnectionStatus => {
  const wsClient = getWsClient();
  if (!wsClient) {
    console.warn('getConnectionStatus: WebSocket客户端实例无效，返回DISCONNECTED');
    return ConnectionStatus.DISCONNECTED;
  }
  try {
    const nativeStatus = wsClient.getNativeConnectionState();
    if (nativeStatus === WebSocket.OPEN) {
      return ConnectionStatus.CONNECTED;
    } else if (nativeStatus === WebSocket.CONNECTING) {
      return ConnectionStatus.CONNECTING;
    } else if (nativeStatus === WebSocket.CLOSING || nativeStatus === WebSocket.CLOSED) {
      return ConnectionStatus.DISCONNECTED;
    }
    return wsClient.getConnectionStatus();
  } catch (error) {
    console.error('获取WebSocket连接状态失败 (getConnectionStatus):', error);
    return ConnectionStatus.DISCONNECTED;
  }
};

// 添加WebSocket连接状态监听
export const addWsConnectionStatusListener = (listener: (event: any) => void) => {
  try {
    const wsClient = getWsClient();
    if (!wsClient) {
      console.error('addWsConnectionStatusListener: WebSocket客户端实例无效。');
      return; // Exit if client is null
    }
    wsClient.addConnectionStatusListener(listener);
  } catch (error) {
    console.error('添加WebSocket状态监听器失败:', error);
  }
};

// 移除WebSocket连接状态监听
export const removeWsConnectionStatusListener = (listener: (event: any) => void) => {
  try {
    const wsClient = getWsClient();
    if (!wsClient) {
      console.error('removeWsConnectionStatusListener: WebSocket客户端实例无效。');
      return; // Exit if client is null
    }
    wsClient.removeConnectionStatusListener(listener);
  } catch (error) {
    console.error('移除WebSocket状态监听器失败:', error);
  }
};

// API服务函数
class ChatApiService {
  private static async fetchWithAuth(url: string, options: RequestInit = {}): Promise<Response> {
    // 获取有效的令牌
    const token = await authService.getValidToken();
    if (!token) {
      throw new Error('未登录或Token无效');
    }
    
    // 添加认证头
    const headers = {
      ...options.headers,
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
    
    // 执行请求
    try {
      const response = await fetch(url, {
        ...options,
        headers
      });
      
      // 处理常见错误
      if (!response.ok) {
        const status = response.status;
        
        // 尝试读取错误信息
        let errorMessage;
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || `请求失败: ${status}`;
        } catch {
          errorMessage = `请求失败: ${status}`;
        }
        
        // 特殊处理401错误
        if (status === 401) {
          throw new Error('401 Unauthorized: Token已过期');
        }
        
        throw new Error(errorMessage);
      }
      
      return response;
    } catch (error) {
      console.error('API请求失败:', error);
      throw error;
    }
  }
  
  // 获取会话列表
  public static async getConversations(): Promise<Conversation[]> {
    const response = await this.fetchWithAuth(`${API_BASE_URL}/chat/conversations`);
    const data = await response.json();
    
    // 转换数据格式
    return data.map((conv: any) => this.formatConversation(conv));
  }
  
  // 获取会话详情
  public static async getConversationDetails(conversationId: string): Promise<Conversation | null> {
    const response = await this.fetchWithAuth(`${API_BASE_URL}/chat/conversations/${conversationId}`);
    const conv = await response.json();
    
    return this.formatConversation(conv);
  }
  
  // 获取会话消息
  public static async getConversationMessages(conversationId: string): Promise<Message[]> {
    // 添加时间戳参数避免缓存
    const timestamp = Date.now();
    const url = `${API_BASE_URL}/chat/conversations/${conversationId}/messages?nocache=${timestamp}`;
    
    const response = await this.fetchWithAuth(url);
    const messages = await response.json();
    
    // 转换格式
    return messages.map((msg: any) => this.formatMessage(msg));
  }
  
  // 创建新会话
  public static async createConversation(customerId?: string): Promise<Conversation> {
    const userId = customerId || authService.getCurrentUserId();
    if (!userId) {
      throw new Error("用户ID不存在");
    }
    
    const requestData = {
      customer_id: userId,
      title: `咨询会话 ${new Date().toLocaleDateString('zh-CN')}`
    };
    
    const response = await this.fetchWithAuth(`${API_BASE_URL}/chat/conversations`, {
      method: 'POST',
      body: JSON.stringify(requestData)
    });
    
    const newConversation = await response.json();
    return this.formatConversation(newConversation);
  }
  
  // 更新会话标题
  public static async updateConversationTitle(conversationId: string, title: string): Promise<void> {
    await this.fetchWithAuth(`${API_BASE_URL}/chat/conversations/${conversationId}`, {
      method: 'PATCH',
      body: JSON.stringify({ title: title.trim() })
    });
  }
  
  // 获取客户档案
  public static async getCustomerProfile(customerId: string): Promise<CustomerProfile | null> {
    const response = await this.fetchWithAuth(`${API_BASE_URL}/customers/${customerId}/profile`);
    return await response.json();
  }
  
  // 获取客户列表
  public static async getCustomerList(): Promise<Customer[]> {
    const response = await this.fetchWithAuth(`${API_BASE_URL}/customers/`);
    const data = await response.json();
    
    return data.map((customer: any) => ({
      id: customer.id,
      name: customer.name || "未知用户",
      avatar: customer.avatar || '/avatars/user.png',
      isOnline: customer.is_online || false,
      lastMessage: customer.last_message?.content || '',
      lastMessageTime: customer.last_message?.created_at || customer.updated_at,
      unreadCount: customer.unread_count || 0,
      tags: customer.tags || [],
      priority: customer.priority || 'medium'
    }));
  }
  
  // 获取指定客户的会话列表
  public static async getCustomerConversations(customerId: string): Promise<Conversation[]> {
    const response = await this.fetchWithAuth(`${API_BASE_URL}/chat/conversations?customer_id=${customerId}`);
    const data = await response.json();
    
    return data.map((conv: any) => this.formatConversation(conv));
  }
  
  // 设置顾问接管状态
  public static async setTakeoverStatus(conversationId: string, isAiControlled: boolean): Promise<void> {
    const endpoint = isAiControlled 
      ? `${API_BASE_URL}/chat/conversations/${conversationId}/release`
      : `${API_BASE_URL}/chat/conversations/${conversationId}/takeover`;
    
    await this.fetchWithAuth(endpoint, {
      method: 'POST'
    });
  }
  
  // 调用AI服务获取回复
  public static async getAIResponse(conversationId: string, content: string): Promise<string> {
    const userId = authService.getCurrentUserId();
    const userRole = authService.getCurrentUserRole();
    
    if (!userId) {
      throw new Error("未登录，无法请求AI服务");
    }
    
    // 构建请求数据
    const requestData = {
      conversation_id: conversationId,
      content,
      type: "text"
    };
    
    const response = await this.fetchWithAuth(`${API_BASE_URL}/ai/chat`, {
      method: 'POST',
      body: JSON.stringify(requestData)
    });
    
    const data = await response.json();
    return data.content;
  }
  
  // 格式化会话对象
  private static formatConversation(conv: any): Conversation {
    let customerName = "未知用户";
    if (conv.customer) {
      customerName = conv.customer.username || "未知用户";
    }
    
    // 格式化最后一条消息
    let lastMessage;
    if (conv.last_message) {
      lastMessage = this.formatMessage(conv.last_message);
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
      lastMessage,
      unreadCount: conv.unread_count || 0,
      updatedAt: conv.updated_at,
      status: conv.status,
      consultationType: conv.consultation_type || '一般咨询',
      summary: conv.summary || ''
    };
  }
  
  // 格式化消息对象
  private static formatMessage(msg: any): Message {
    return {
      id: msg.id,
      content: msg.content,
      type: msg.type || 'text',
      sender: {
        id: msg.sender?.id || msg.sender_id,
        name: msg.sender?.name || msg.sender_name || '未知',
        avatar: msg.sender?.avatar || msg.sender_avatar || 
               (msg.sender?.type === 'ai' || msg.sender_type === 'ai' ? aiInfo.avatar : '/avatars/user.png'),
        type: msg.sender?.type || msg.sender_type,
      },
      timestamp: msg.timestamp || msg.created_at,
      isImportant: msg.is_important || false,
      isRead: msg.is_read || false,
      isSystemMessage: msg.is_system_message || false
    };
  }
}

// 消息相关功能
// 发送文字消息
export const sendTextMessage = async (conversationId: string, content: string): Promise<Message> => {
  // 获取当前用户
  const currentUser = authService.getCurrentUser();
  if (!currentUser) {
    throw new Error('用户未登录');
  }
  
  // 确保使用用户的当前角色
  const userRole = currentUser.currentRole || 'customer';
  
  // 创建用户消息
  const userMessage: Message = {
    id: `m_${uuidv4()}`,
    content,
    type: 'text',
    sender: {
      id: currentUser.id,
      type: userRole,
      name: currentUser.name,
      avatar: currentUser.avatar || '/avatars/user.png',
    },
    timestamp: new Date().toISOString(),
  };
  
  // 添加到本地消息列表
  chatState.addMessage(conversationId, userMessage);
  
  // 通过WebSocket发送消息
  const wsMessage = {
    action: 'message',
    data: {
      content,
      type: 'text',
      sender_type: userRole
    },
    conversation_id: conversationId,
    timestamp: new Date().toISOString()
  };
  
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
  chatState.addMessage(conversationId, imageMessage);
  
  // 通过WebSocket发送消息
  const wsMessage = {
    action: 'message',
    data: {
      content: imageUrl,
      type: 'image',
      sender_type: currentUser.currentRole || 'customer'
    },
    conversation_id: conversationId,
    timestamp: new Date().toISOString()
  };
  
  sendWebSocketMessage(wsMessage);
  
  return imageMessage;
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
  chatState.addMessage(conversationId, voiceMessage);
  
  // 通过WebSocket发送消息
  const wsMessage = {
    action: 'message',
    data: {
      content: audioUrl,
      type: 'voice',
      sender_type: currentUser.currentRole || 'customer'
    },
    conversation_id: conversationId,
    timestamp: new Date().toISOString()
  };
  
  sendWebSocketMessage(wsMessage);
  
  return voiceMessage;
};

// 获取AI回复
export const getAIResponse = async (conversationId: string, userMessage: Message): Promise<Message | null> => {
  // 如果顾问已接管，不再生成AI回复
  if (chatState.isConsultantTakeover(conversationId)) {
    return null;
  }
  
  try {
    // 调用AI服务获取回复
    const responseContent = await ChatApiService.getAIResponse(conversationId, userMessage.content);
    
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
    chatState.addMessage(conversationId, aiMessage);
    
    return aiMessage;
  } catch (error) {
    console.error('获取AI回复失败:', error);
    
    // 返回一个友好的错误消息
    const errorMessage: Message = {
      id: `m_${uuidv4()}`,
      content: '抱歉，AI服务暂时不可用，请稍后再试。',
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
    chatState.addMessage(conversationId, errorMessage);
    
    return errorMessage;
  }
};

// 获取会话消息
export const getConversationMessages = async (conversationId: string, forceRefresh: boolean = false): Promise<Message[]> => {
  // 获取缓存的消息
  const cachedMessages = chatState.getChatMessages(conversationId);
  
  // 检查是否有未完成的请求
  if (chatState.isRequestingMessagesForConversation(conversationId)) {
    return cachedMessages;
  }
  
  // 检查缓存时间
  const lastRequestTime = chatState.getMessagesRequestTime(conversationId);
  const now = Date.now();
  
  // 如果未强制刷新且缓存有效，返回缓存数据
  if (!forceRefresh && cachedMessages.length > 0 && (now - lastRequestTime) < MESSAGES_CACHE_TIME) {
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
    
    // 更新本地缓存，只有在有数据时才更新
    if (messages.length > 0) {
      chatState.setChatMessages(conversationId, messages);
      chatState.updateMessagesRequestTime(conversationId);
    }
    
    return messages;
  } catch (error) {
    console.error(`获取会话消息出错:`, error);
    
    // 如果是认证错误，抛出异常
    if (error instanceof Error && error.message.includes('401')) {
      throw error;
    }
    
    // 其他错误时返回缓存数据
    return cachedMessages;
  } finally {
    // 重置请求标志
    chatState.setRequestingMessages(conversationId, false);
  }
};

// 获取所有会话
export const getConversations = async (): Promise<Conversation[]> => {
  // 检查是否已有请求正在进行
  if (chatState.isRequestingConversationsState()) {
    return chatState.getConversations();
  }
  
  // 检查缓存是否在有效期内
  const now = Date.now();
  const lastRequestTime = chatState.getConversationsRequestTime();
  const conversations = chatState.getConversations();
  
  if (conversations.length > 0 && (now - lastRequestTime) < CONVERSATIONS_CACHE_TIME) {
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
    console.error(`获取会话列表出错:`, error);
    
    // 如果是认证错误，抛出异常
    if (error instanceof Error && error.message.includes('401')) {
      throw error;
    }
    
    // 其他错误返回缓存数据
    return conversations;
  } finally {
    // 重置请求标志
    chatState.setRequestingConversations(false);
  }
};

// 标记消息为重点
export const markMessageAsImportant = async (conversationId: string, messageId: string, isImportant: boolean): Promise<Message | null> => {
  const messages = chatState.getChatMessages(conversationId);
  if (!messages.length) return null;
  
  try {
    // 找到对应的消息
    const messageIndex = messages.findIndex(msg => msg.id === messageId);
    if (messageIndex < 0) return null;
    
    // 更新本地状态
    const updatedMessage = {
      ...messages[messageIndex],
      isImportant,
    };
    
    // 更新本地消息
    messages[messageIndex] = updatedMessage;
    chatState.setChatMessages(conversationId, messages);
    
    // 尝试同步到服务器
    try {
      const token = await authService.getValidToken();
      if (token) {
        await fetch(`${API_BASE_URL}/chat/conversations/${conversationId}/messages/${messageId}/important`, {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ is_important: isImportant })
        });
      }
    } catch (error) {
      console.error('更新重点消息状态到服务器失败:', error);
      // 仅本地更新，不影响用户体验
    }
    
    return updatedMessage;
  } catch (error) {
    console.error('标记重点消息失败:', error);
    return null;
  }
};

// 获取重点消息
export const getImportantMessages = (conversationId: string): Message[] => {
  const messages = chatState.getChatMessages(conversationId);
  return messages.filter(msg => msg.isImportant);
};

// 获取客户档案
export const getCustomerProfile = async (customerId: string): Promise<CustomerProfile | null> => {
  try {
    return await ChatApiService.getCustomerProfile(customerId);
  } catch (error) {
    console.error(`获取客户档案出错:`, error);
    return null;
  }
};

// 获取客户历史咨询记录
export const getCustomerConsultationHistory = async (customerId: string): Promise<ConsultationHistoryItem[]> => {
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
      type: conversation.consultationType || '一般咨询',
      description: conversation.summary || '无咨询总结'
    }));
    
    // 按日期降序排序（最新的在前）
    return history.sort((a, b) => 
      new Date(b.date).getTime() - new Date(a.date).getTime()
    );
  } catch (error) {
    console.error(`获取客户咨询历史出错:`, error);
    return [];
  }
};

// 顾问接管会话
export const takeoverConversation = async (conversationId: string): Promise<boolean> => {
  try {
    // 更新本地状态
    chatState.setConsultantTakeover(conversationId, true);
    
    // 发送系统消息通知顾问接管
    const systemMessage: Message = {
      id: `m_${uuidv4()}`,
      content: '顾问已接管会话',
      type: 'text',
      sender: {
        id: 'system',
        type: 'system',
        name: '系统',
        avatar: systemInfo.avatar,
      },
      timestamp: new Date().toISOString(),
      isSystemMessage: true,
    };
    
    // 添加到消息列表
    chatState.addMessage(conversationId, systemMessage);
    
    // 发送接管状态到后端
    await ChatApiService.setTakeoverStatus(conversationId, false); // false表示顾问接管
    
    return true;
  } catch (error) {
    console.error('设置接管状态失败:', error);
    return false;
  }
};

// 切回AI模式
export const switchBackToAI = async (conversationId: string): Promise<boolean> => {
  try {
    // 更新本地状态
    chatState.setConsultantTakeover(conversationId, false);
    
    // 发送系统消息通知切回AI模式
    const systemMessage: Message = {
      id: `m_${uuidv4()}`,
      content: 'AI助手已接管会话',
      type: 'text',
      sender: {
        id: 'system',
        type: 'system',
        name: '系统',
        avatar: systemInfo.avatar,
      },
      timestamp: new Date().toISOString(),
      isSystemMessage: true,
    };
    
    // 添加到消息列表
    chatState.addMessage(conversationId, systemMessage);
    
    // 发送接管状态到后端
    await ChatApiService.setTakeoverStatus(conversationId, true); // true表示AI接管
    
    return true;
  } catch (error) {
    console.error('设置接管状态失败:', error);
    return false;
  }
};

// 是否处于顾问模式
export const isConsultantMode = (conversationId: string): boolean => {
  return chatState.isConsultantTakeover(conversationId);
};

// 创建新会话
export const createConversation = async (customerId?: string): Promise<Conversation> => {
  try {
    const newConversation = await ChatApiService.createConversation(customerId);
    
    // 更新本地会话列表
    const conversations = chatState.getConversations();
    conversations.unshift(newConversation);
    chatState.setConversations(conversations);
    
    return newConversation;
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
    return [...allConversations].sort((a, b) => {
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
    let lastError;
    
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
    
    throw lastError || new Error("创建会话失败，请稍后再试");
  } catch (error) {
    console.error("获取或创建会话失败:", error);
    throw error;
  }
};

// 获取会话详情
export const getConversationDetails = async (conversationId: string): Promise<Conversation | null> => {
  try {
    return await ChatApiService.getConversationDetails(conversationId);
  } catch (error) {
    console.error(`获取会话详情出错:`, error);
    return null;
  }
};

// 同步顾问接管状态
export const syncConsultantTakeoverStatus = async (conversationId: string): Promise<boolean> => {
  try {
    // 获取会话详情
    const conversation = await ChatApiService.getConversationDetails(conversationId);
    
    if (conversation && 'is_ai_controlled' in conversation) {
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
};

// 更新会话标题
export const updateConversationTitle = async (conversationId: string, title: string): Promise<void> => {
  try {
    await ChatApiService.updateConversationTitle(conversationId, title);
    
    // 更新本地缓存中的会话标题
    const conversations = chatState.getConversations();
    const updatedConversations = conversations.map(conv => 
      conv.id === conversationId 
        ? { ...conv, title: title.trim() }
        : conv
    );
    chatState.setConversations(updatedConversations);
  } catch (error) {
    console.error(`更新会话标题失败:`, error);
    throw error;
  }
};

// 获取客户列表（顾问端使用）
export const getCustomerList = async (): Promise<Customer[]> => {
  try {
    return await ChatApiService.getCustomerList();
  } catch (error) {
    console.error(`获取客户列表失败:`, error);
    throw error;
  }
};

// 获取指定客户的会话列表
export const getCustomerConversations = async (customerId: string): Promise<Conversation[]> => {
  try {
    return await ChatApiService.getCustomerConversations(customerId);
  } catch (error) {
    console.error(`获取客户会话失败:`, error);
    throw error;
  }
}; 