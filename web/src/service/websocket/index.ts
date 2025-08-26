import { WebSocketConnection } from './core/connection';
import { WebSocketHeartbeat } from './core/heartbeat';
import { WebSocketReconnector } from './core/reconnect';
import { WebSocketSerializer } from './core/serializer';
import { MessageAdapter } from './adapters/messageAdapter';
import { MessageHandler, MessageHandlerRegistry, createDefaultHandlerRegistry } from './handlers';
import { MessageQueue } from './core/messageQueue';
import { ConnectionStatus, WebSocketConfig, MessageData, ConnectionParams } from './types';

/**
 * WebSocket客户端服务
 * 整合所有WebSocket相关功能，提供统一的接口
 */
export class WebSocketClient {
  // 核心组件
  private connection: WebSocketConnection;
  private heartbeat: WebSocketHeartbeat;
  private reconnector: WebSocketReconnector;
  private serializer: WebSocketSerializer;
  private adapter: MessageAdapter;
  private handlerRegistry: MessageHandlerRegistry;
  private messageQueue: MessageQueue;
  
  // 配置
  private config: WebSocketConfig;
  
  // 状态
  private initialized: boolean = false;
  private connectionParams: ConnectionParams = {};
  
  /**
   * 构造函数
   * @param config WebSocket配置
   */
  constructor(config: WebSocketConfig) {
    // 保存配置 - 使用生产环境最佳实践默认值
    this.config = {
      ...{
        url: '',
        // 重连策略配置
        reconnectAttempts: 15,          // 15次重连
        reconnectInterval: 2000,        // 初始2秒间隔
        
        // 心跳配置
        heartbeatInterval: 45000,       // 45秒心跳间隔
        
        // 连接配置
        connectionTimeout: 20000,       // 20秒连接超时
        
        // 调试配置
        debug: false
      },
      ...config
    };
    
    // 初始化核心组件
    this.connection = new WebSocketConnection();
    this.serializer = new WebSocketSerializer();
    this.adapter = new MessageAdapter();
    this.handlerRegistry = createDefaultHandlerRegistry();
    this.messageQueue = new MessageQueue();
    
    // 初始化心跳机制
    this.heartbeat = new WebSocketHeartbeat(
      this.connection,
      this.config.heartbeatInterval
    );
    
    // 初始化重连机制 - 添加最大延迟配置
    this.reconnector = new WebSocketReconnector(
      this.connection,
      {
        maxAttempts: this.config.reconnectAttempts,
        baseDelay: this.config.reconnectInterval,
        maxDelay: 30000,                // 最大重连间隔30秒
        exponentialBackoff: true        // 启用指数退避
      }
    );
    
    // 设置消息处理
    this.connection.on('message', this.handleRawMessage.bind(this));
    
    // 处理重连事件
    this.reconnector.on('reconnected', this.handleReconnection.bind(this));
    
    // 处理重连器错误事件，防止未捕获的错误
    this.reconnector.on('error', (error: any) => {
      if (this.config.debug) {
        console.error('重连器错误:', error);
      }
      // 触发连接错误事件，让上层应用处理
      this.connection.emit('reconnectionError', error);
    });
    
    // 记录调试信息
    if (this.config.debug) {
      this.setupDebugListeners();
    }
    
    this.initialized = true;
  }
  
  /**
   * 连接WebSocket服务
   * @param params 连接参数
   * @returns Promise，连接成功时解析
   */
  public async connect(params: ConnectionParams = {}): Promise<void> {
    if (!this.config.url) {
      throw new Error('未设置WebSocket服务URL');
    }
    
    // 保存连接参数
    this.connectionParams = { ...params };
    
    // 构建完整URL - 分布式架构使用通用端点
    let url = this.config.url;
    console.log(`WebSocketClient: 连接分布式WebSocket端点: ${url}`);
    
    // 添加查询参数
    const queryParams = new URLSearchParams();
    
    if (params.token) {
      queryParams.append('token', params.token);
    }
    
    // 添加会话ID作为查询参数（分布式架构要求）
    if (params.conversationId) {
      queryParams.append('conversationId', params.conversationId);
    }
    
    // 添加其他参数
    Object.entries(params).forEach(([key, value]) => {
      if (!['token', 'conversationId'].includes(key) && value !== undefined) {
        queryParams.append(key, String(value));
      }
    });
    
    // 拼接完整URL
    const queryString = queryParams.toString();
    const fullUrl = queryString ? `${url}?${queryString}` : url;
    
    // 记录连接开始
    console.log(`WebSocketClient: 开始连接分布式WebSocket: ${fullUrl}`, {
      conversationId: params.conversationId,
      connectionId: params.connectionId || this.connectionParams.connectionId || '未指定',
      architecture: 'distributed-redis-pubsub'
    });
    
    try {
      // 建立连接 - 这里设置一个更长的超时等待
      await this.connection.connect(fullUrl, params);
      
      // 启动心跳
      this.heartbeat.start();
      
      // 处理消息队列
      if (params.conversationId) {
        this.processQueuedMessages(params.conversationId);
      }
      
      if (this.config.debug) {
        console.log(`WebSocketClient: 分布式连接成功: ${fullUrl}, 状态: ${this.getConnectionStatus()}`);
      }
    } catch (error) {
      // 记录连接失败详情
      if (this.config.debug) {
        console.error(`WebSocketClient: 分布式连接失败: ${fullUrl}`, error);
      }
      
      // 更新内部状态为断开连接
      const internalEvent = {
        oldStatus: this.connection.getStatus(),
        newStatus: ConnectionStatus.DISCONNECTED,
        connectionId: params.connectionId || this.connectionParams.connectionId || '未指定',
        timestamp: Date.now(),
        error
      };
      
      // 手动触发状态变更事件，以确保UI能够更新
      this.connection.emit('statusChange', internalEvent);
      
      // 向上传递错误
      throw error;
    }
  }
  
  /**
   * 关闭WebSocket连接
   */
  public disconnect(): void {
    try {
      // 先禁用重连，避免自动重连
      this.reconnector.disable();
      
      // 停止心跳
      this.heartbeat.stop();
      
      // 关闭连接
      this.connection.close();
      
      if (this.config.debug) {
        console.log('WebSocketClient: 连接已关闭');
      }
    } catch (error) {
      console.error('WebSocketClient: 关闭连接出错:', error);
    }
  }
  
  /**
   * 发送消息
   * @param message 要发送的消息
   * @param conversationId 可选的会话ID
   * @returns 是否发送成功
   */
  public sendMessage(message: MessageData | Record<string, any>, conversationId?: string): boolean {
    // 如果消息本身没有会话ID但提供了conversationId参数，则添加到消息中
    if (conversationId && !message.conversation_id && typeof message === 'object') {
      message = { ...message, conversation_id: conversationId };
    }
    
    // 实际的会话ID，优先使用消息中的
    const actualConversationId = (message as any).conversation_id || conversationId;
    
    try {
      // 检查连接状态
      if (!this.connection.isConnected()) {
        // 未连接，加入队列
        this.messageQueue.enqueue(message, actualConversationId);
        
        if (this.config.debug) {
          console.log('WebSocket未连接，消息已加入队列:', message);
        }
        
        return false;
      }
      
      // 序列化消息
      const serializedMessage = this.serializer.serialize(message);
      
      // 发送消息
      const result = this.connection.send(serializedMessage);
      
      if (this.config.debug && result) {
        console.log('WebSocket消息已发送:', message);
      } else if (this.config.debug && !result) {
        console.warn('WebSocket消息发送失败，加入队列:', message);
        this.messageQueue.enqueue(message, actualConversationId);
      }
      
      return result;
    } catch (error) {
      if (this.config.debug) {
        console.error('WebSocket消息发送出错:', error);
      }
      
      // 发送失败，加入队列
      this.messageQueue.enqueue(message, actualConversationId);
      
      return false;
    }
  }
  
  /**
   * 处理原始消息
   * @param event 消息事件
   */
  private handleRawMessage(event: any): void {
    try {
      // 反序列化消息
      let message: any;
      
      if (typeof event.data === 'string') {
        message = this.serializer.deserialize(event.data);
      } else if (event.data instanceof ArrayBuffer) {
        message = this.serializer.deserialize(event.data);
      } else if (event.data instanceof Blob) {
        // Blob需要异步处理，这里提前返回
        this.handleBlobMessage(event.data);
        return;
      } else {
        throw new Error('不支持的消息格式');
      }
      
      // 适配消息格式
      const adaptedMessage = this.adapter.adapt(message);
      
      // 分发到处理器
      const handled = this.handlerRegistry.dispatchMessage(adaptedMessage);
      
      // 只在开发模式下且消息类型重要时输出日志
      if (this.config.debug && this.shouldLogMessage(adaptedMessage)) {
        // 避免消息日志过于频繁
        const messageKey = `${(adaptedMessage as any).action || 'unknown'}_${adaptedMessage.type || 'unknown'}`;
        const lastLogTime = sessionStorage.getItem(`ws_msg_log_${messageKey}`);
        const now = Date.now();
        
        if (!lastLogTime || now - parseInt(lastLogTime) > 5000) { // 5秒内相同类型消息不重复日志
          console.log('WebSocket收到消息:', {
            action: (adaptedMessage as any).action || 'unknown',
            type: adaptedMessage.type || 'unknown',
            timestamp: new Date().toISOString(),
            handled
          });
          sessionStorage.setItem(`ws_msg_log_${messageKey}`, now.toString());
        }
      }
    } catch (error) {
      console.error('处理WebSocket消息出错:', error);
    }
  }

  /**
   * 判断是否应该记录消息日志
   * @param message 消息对象
   * @returns 是否应该记录
   */
  private shouldLogMessage(message: any): boolean {
    const action = message.action || '';
    const type = message.type || '';
    
    // 心跳消息不记录
    if (type === 'heartbeat' || action === 'ping' || action === 'pong') {
      return false;
    }
    
    // 频繁的状态更新消息减少记录
    if (action === 'typing_update' || action === 'presence_update') {
      // 每10次记录一次
      return Math.random() < 0.1;
    }
    
    // 其他消息正常记录
    return true;
  }
  
  /**
   * 处理Blob类型的消息
   * @param blob Blob数据
   */
  private async handleBlobMessage(blob: Blob): Promise<void> {
    try {
      // 异步反序列化Blob消息
      const message = await this.serializer.deserializeAsync(blob);
      
      // 适配消息格式
      const adaptedMessage = this.adapter.adapt(message);
      
      // 分发到处理器
      const handled = this.handlerRegistry.dispatchMessage(adaptedMessage);
      
      if (this.config.debug) {
        console.log('WebSocket收到Blob消息:', adaptedMessage, handled ? '(已处理)' : '(未处理)');
      }
    } catch (error) {
      if (this.config.debug) {
        console.error('处理WebSocket Blob消息出错:', error);
      }
    }
  }
  
  /**
   * 处理重连事件
   */
  private handleReconnection(event: any): void {
    // 重连成功后处理消息队列
    const conversationId = this.connectionParams.conversationId;
    
    if (conversationId) {
      this.processQueuedMessages(conversationId);
    }
    
    if (this.config.debug) {
      console.log(`WebSocket重连成功，处理消息队列，会话ID: ${conversationId}`);
    }
  }
  
  /**
   * 处理队列中的消息
   * @param conversationId 会话ID
   */
  private processQueuedMessages(conversationId: string): void {
    if (this.messageQueue.isEmpty()) {
      return;
    }
    
    // 处理特定会话的消息
    this.messageQueue.processQueue(
      // 消息处理器
      async (message) => {
        // 只有在连接状态才发送
        if (!this.connection.isConnected()) {
          return false;
        }
        
        try {
          // 序列化消息
          const serializedMessage = this.serializer.serialize(message);
          
          // 发送消息
          return this.connection.send(serializedMessage);
        } catch (error) {
          if (this.config.debug) {
            console.error('处理队列消息出错:', error);
          }
          return false;
        }
      },
      // 消息过滤器
      (queuedMessage) => queuedMessage.conversationId === conversationId
    );
  }
  
  /**
   * 注册消息处理器
   * @param handler 消息处理器
   */
  public registerHandler(handler: MessageHandler): void {
    this.handlerRegistry.registerHandler(handler);
    
    if (this.config.debug) {
      console.log(`注册消息处理器: ${handler.getName()}`);
    }
  }
  
  /**
   * 注销消息处理器
   * @param handlerName 处理器名称
   * @returns 是否成功注销
   */
  public unregisterHandler(handlerName: string): boolean {
    const result = this.handlerRegistry.unregisterHandler(handlerName);
    
    if (this.config.debug && result) {
      console.log(`注销消息处理器: ${handlerName}`);
    }
    
    return result;
  }
  
  /**
   * 获取连接状态
   */
  public getConnectionStatus(): ConnectionStatus {
    return this.connection.getStatus();
  }
  
  /**
   * 获取原生WebSocket连接状态（readyState）
   * 如果没有连接，返回WebSocket.CLOSED (3)
   */
  public getNativeConnectionState(): number {
    return this.connection.getNativeState();
  }
  
  /**
   * 添加连接状态变化监听器
   * @param listener 回调函数，参数为 { oldStatus: ConnectionStatus, newStatus: ConnectionStatus, connectionId: string }
   */
  public addConnectionStatusListener(listener: (event: any) => void): void {
    this.connection.on('statusChange', listener);
  }
  
  /**
   * 移除连接状态变化监听器
   * @param listener 要移除的回调函数
   */
  public removeConnectionStatusListener(listener: (event: any) => void): void {
    this.connection.off('statusChange', listener);
  }
  
  /**
   * 检查是否已连接
   */
  public isConnected(): boolean {
    return this.connection.isConnected();
  }
  
  /**
   * 手动触发重连
   */
  public reconnect(): void {
    this.reconnector.reconnectNow();
    
    if (this.config.debug) {
      console.log('手动触发WebSocket重连');
    }
  }
  
  /**
   * 获取消息队列
   */
  public getMessageQueue(): MessageQueue {
    return this.messageQueue;
  }
  
  /**
   * 获取连接参数
   */
  public getConnectionParams(): ConnectionParams {
    return { ...this.connectionParams };
  }
  
  /**
   * 设置调试模式
   * @param debug 是否启用调试
   */
  public setDebug(debug: boolean): void {
    this.config.debug = debug;
    
    if (debug) {
      this.setupDebugListeners();
    }
  }
  
  /**
   * 设置调试监听器
   */
  private setupDebugListeners(): void {
    // 连接状态变化
    this.connection.on('statusChange', (event) => {
      console.log(`WebSocket状态变化: ${event.oldStatus} -> ${event.newStatus}`);
    });
    
    // 心跳事件
    this.heartbeat.on('beat', (event) => {
      console.log(`WebSocket心跳: ${new Date(event.timestamp).toISOString()}`);
    });
    
    this.heartbeat.on('error', (event) => {
      console.warn(`WebSocket心跳错误: ${event.message}`);
    });
    
    // 重连事件
    this.reconnector.on('reconnectAttempt', (event) => {
      console.log(`WebSocket重连尝试: ${event.attempt}/${event.maxAttempts}`);
    });
    
    this.reconnector.on('reconnected', (event) => {
      console.log(`WebSocket重连成功: 尝试次数=${event.attempts}`);
    });
    
    this.reconnector.on('maxAttemptsReached', (event) => {
      console.error(`WebSocket重连失败: 已达到最大尝试次数${event.maxAttempts}`);
    });
    
    // 消息队列事件
    this.messageQueue.on('enqueue', (event) => {
      console.log(`消息已加入队列:`, event);
    });
    
    this.messageQueue.on('dequeue', (event) => {
      console.log(`消息已从队列移除:`, event);
    });
    
    this.messageQueue.on('processComplete', (event) => {
      console.log(`队列处理完成, 剩余消息: ${event.remainingCount}`);
    });
    
    this.messageQueue.on('error', (event) => {
      console.error(`队列消息处理错误:`, event);
    });
  }
  
  /**
   * 获取已注册的处理器列表
   */
  public getHandlers(): MessageHandler[] {
    return this.handlerRegistry.getHandlers();
  }
}

// 重新导出类型和核心组件
export { ConnectionStatus } from './types';
export type { WebSocketConfig, MessageData, ConnectionParams } from './types';
export type { MessageType, SenderType } from './types';
export type { MessageHandler } from './handlers/messageHandler';
export type { MessageQueue } from './core/messageQueue';

// 创建单例实例
let instance: WebSocketClient | null = null;

/**
 * 获取WebSocketClient单例
 * @param config 配置（仅首次调用时有效）
 * @returns WebSocketClient实例
 */
export function getWebSocketClient(config?: WebSocketConfig): WebSocketClient {
  if (!instance && config) {
    instance = new WebSocketClient(config);
  } else if (!instance && !config) {
    throw new Error('WebSocketClient未初始化，首次调用需提供配置');
  }
  
  return instance!;
}

/**
 * 重置WebSocketClient单例
 * 用于测试或需要重新初始化的场景
 */
export function resetWebSocketClient(): void {
  if (instance) {
    try {
      instance.disconnect();
    } catch (error) {
      // 忽略错误
    }
    instance = null;
  }
} 