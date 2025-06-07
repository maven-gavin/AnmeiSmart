/**
 * 聊天WebSocket管理模块
 * 统一管理聊天相关的WebSocket连接和消息处理
 */

import { authService } from '../authService';
import { getWebSocketClient, ConnectionStatus, WebSocketClient } from '../websocket';
import { SenderType } from '../websocket/types';
import { MessageEventHandler } from '../websocket/handlers/messageEventHandler';
import { getDeviceInfo, getWebSocketDeviceConfig, formatDeviceInfo, type DeviceInfo } from '../utils';
import type { WebSocketConnectionParams } from './types';

/**
 * WebSocket管理器
 * 专门处理聊天相关的WebSocket连接和消息
 */
export class ChatWebSocketManager {
  private wsClient: WebSocketClient | null = null;
  private messageHandlers: Map<string, (data: any) => void> = new Map();
  private deviceInfo: DeviceInfo | null = null;
  private initPromise: Promise<void> | null = null;
  
  constructor() {
    // 异步初始化，避免阻塞构造函数
    this.initPromise = this.initializeClient();
  }
  
  /**
   * 等待初始化完成
   */
  private async ensureInitialized(): Promise<void> {
    if (this.initPromise) {
      await this.initPromise;
    }
  }
  
  // ===== 初始化和连接 =====
  
  /**
   * 初始化WebSocket客户端
   */
  private async initializeClient(): Promise<void> {
    try {
      // 获取设备信息
      this.deviceInfo = await getDeviceInfo();
      console.log('设备信息:', formatDeviceInfo(this.deviceInfo));
      
      // 获取协议和主机
      const wsProtocol = typeof window !== 'undefined' && window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      let wsHost = process.env.NEXT_PUBLIC_WS_URL || (typeof window !== 'undefined' ? window.location.host : 'localhost:8000');
      
      // 处理端口映射
      if (wsHost === 'localhost:3000') {
        wsHost = 'localhost:8000';
      } else if (wsHost.includes(':3000')) {
        wsHost = wsHost.replace(':3000', ':8000');
      }
      
      if (!wsHost) {
        throw new Error('WebSocket主机未配置');
      }
      
      // 修改为新的通用WebSocket端点
      const baseUrl = `${wsProtocol}//${wsHost}/api/v1/ws`;
      console.log('WebSocket连接基础URL:', baseUrl);
      
      // 根据设备类型获取优化配置
      const deviceConfig = getWebSocketDeviceConfig(this.deviceInfo);
      
      // 获取客户端实例 - 使用设备优化配置
      this.wsClient = getWebSocketClient({
        url: baseUrl,
        // 重连策略 - 适合生产环境的配置
        reconnectAttempts: 15,           // 15次重连，覆盖5-10分钟断网
        reconnectInterval: deviceConfig.reconnectInterval,
        
        // 心跳配置 - 根据设备类型优化
        heartbeatInterval: deviceConfig.heartbeatInterval,
        
        // 连接超时 - 根据设备类型优化
        connectionTimeout: deviceConfig.connectionTimeout,
        
        // 调试模式
        debug: process.env.NODE_ENV === 'development'
      });
      
      // 注册消息处理器
      this.registerHandlers();
      
    } catch (error) {
      console.error('初始化WebSocket客户端失败:', error);
      this.wsClient = null;
    }
  }
  
  /**
   * 注册消息处理器 - 新的分布式WebSocket架构
   */
  private registerHandlers(): void {
    if (!this.wsClient) return;
    
    // 注册消息事件处理器（专为新架构设计）
    const eventHandler = new MessageEventHandler(1);
    this.wsClient.registerHandler(eventHandler);
    
    // 设置事件处理器回调
    eventHandler.addNewMessageCallback((data: any) => {
      if (process.env.NODE_ENV === 'development') {
        console.log('收到新消息广播:', {
          messageId: data.message?.id,
          conversationId: data.conversation_id,
          timestamp: new Date().toISOString()
        });
      }
      this.handleMessage({ action: 'new_message', data });
    });
    
    eventHandler.addPresenceUpdateCallback((data: any) => {
      if (process.env.NODE_ENV === 'development' && Math.random() < 0.2) {
        console.log('收到用户在线状态更新:', {
          userId: data.user_id,
          status: data.status,
          conversationId: data.conversation_id
        });
      }
      this.handleMessage({ action: 'presence_update', data });
    });
    
    eventHandler.addEventCallback((data: any) => {
      if (process.env.NODE_ENV === 'development') {
        console.log('收到分布式WebSocket事件:', {
          type: data.type || data.action,
          timestamp: new Date().toISOString()
        });
      }
      this.handleMessage(data);
    });
    
    // 添加连接状态监听
    this.wsClient.addConnectionStatusListener((event: any) => {
      console.log('分布式WebSocket连接状态变更:', event);
    });
  }
  
  /**
   * 连接到指定会话
   */
  public async connect(userId: string, conversationId: string): Promise<void> {
    try {
      // 确保初始化完成
      await this.ensureInitialized();
      
      const token = await authService.getValidToken();
      const userRole = authService.getCurrentUserRole() || '';
      
      if (!token) {
        console.log('Token无效或不存在，不尝试WebSocket连接');
        return;
      }
      
      // 构建连接参数 - 分布式WebSocket架构（纯连接层）
      const connectionParams: WebSocketConnectionParams = {
        userId,
        conversationId, // 仅用于前端逻辑，不传递给WebSocket连接
        token,
        userType: this.mapUserRoleToSenderType(userRole),
        connectionId: `${userId}_${Date.now()}`, // 移除conversationId，纯设备连接标识
        // 设备信息
        deviceId: this.deviceInfo?.deviceId,
        deviceType: this.deviceInfo?.type,
        deviceIP: this.deviceInfo?.ip,
        userAgent: this.deviceInfo?.userAgent,
        platform: this.deviceInfo?.platform,
        screenResolution: this.deviceInfo ? `${this.deviceInfo.screenWidth}x${this.deviceInfo.screenHeight}` : undefined
      };
      
      console.log('连接分布式WebSocket (全局连接层):', {
        userId: connectionParams.userId,
        connectionId: connectionParams.connectionId,
        deviceType: connectionParams.deviceType,
        userAgent: connectionParams.userAgent?.substring(0, 50) + '...', // 截断用户代理字符串
        deviceInfo: this.deviceInfo ? formatDeviceInfo(this.deviceInfo) : 'unknown',
        architecture: 'distributed-global',
        mode: conversationId === 'global' ? 'global-connection' : 'legacy-mode'
      });
      
      if (!this.wsClient) {
        await this.initializeClient();
      }
      
      if (!this.wsClient) {
        throw new Error('WebSocket客户端初始化失败');
      }
      
      await this.wsClient.connect(connectionParams);
      console.log(`分布式WebSocket连接成功 [${this.deviceInfo?.type?.toUpperCase() || 'UNKNOWN'}]`, {
        endpoint: '/api/v1/ws',
        architecture: 'distributed-redis-pubsub',
        layer: 'connection-only',
        note: `会话${conversationId}的业务逻辑将通过消息处理`
      });
      
    } catch (error: any) {
      console.error('WebSocket连接失败:', error);
      
      if (error?.message?.includes('401')) {
        console.error('WebSocket连接失败: 认证失败 (401)');
      }
      
      throw error;
    }
  }
  
  /**
   * 断开WebSocket连接
   */
  public disconnect(): void {
    try {
      if (this.wsClient?.isConnected()) {
        this.wsClient.disconnect();
        console.log('WebSocket连接已断开');
      }
    } catch (error) {
      console.error('断开WebSocket连接时出错:', error);
    }
  }
  
  // ===== 消息处理 =====
  
  /**
   * 发送消息
   */
  public sendMessage(message: any): boolean {
    if (!this.wsClient) {
      console.error('WebSocket客户端未初始化');
      return false;
    }
    
    if (!this.wsClient.isConnected()) {
      console.log('WebSocket未连接，无法发送消息');
      return false;
    }
    
    return this.wsClient.sendMessage(message);
  }
  
  /**
   * 处理接收到的消息
   */
  private handleMessage(data: any): void {
    try {
      const action = data.action;
      
      // 调用注册的处理器
      const handler = this.messageHandlers.get(action);
      if (handler) {
        handler(data);
      }
      
      // 调用通用处理器
      const generalHandler = this.messageHandlers.get('*');
      if (generalHandler) {
        generalHandler(data);
      }
      
    } catch (error) {
      console.error('处理WebSocket消息出错:', error);
    }
  }
  
  /**
   * 注册消息处理器
   */
  public addMessageHandler(action: string, handler: (data: any) => void): void {
    this.messageHandlers.set(action, handler);
  }
  
  /**
   * 移除消息处理器
   */
  public removeMessageHandler(action: string): void {
    this.messageHandlers.delete(action);
  }
  
  // ===== 状态查询 =====
  
  /**
   * 检查连接状态
   */
  public isConnected(): boolean {
    return this.wsClient?.isConnected() || false;
  }
  
  /**
   * 获取连接状态
   */
  public getConnectionStatus(): ConnectionStatus {
    if (!this.wsClient) {
      return ConnectionStatus.DISCONNECTED;
    }
    
    try {
      const nativeStatus = this.wsClient.getNativeConnectionState();
      if (nativeStatus === WebSocket.OPEN) {
        return ConnectionStatus.CONNECTED;
      } else if (nativeStatus === WebSocket.CONNECTING) {
        return ConnectionStatus.CONNECTING;
      } else {
        return ConnectionStatus.DISCONNECTED;
      }
    } catch (error) {
      console.error('获取WebSocket连接状态失败:', error);
      return ConnectionStatus.DISCONNECTED;
    }
  }
  
  /**
   * 添加连接状态监听器
   */
  public addConnectionStatusListener(listener: (event: any) => void): void {
    if (this.wsClient) {
      this.wsClient.addConnectionStatusListener(listener);
    }
  }
  
  /**
   * 移除连接状态监听器
   */
  public removeConnectionStatusListener(listener: (event: any) => void): void {
    if (this.wsClient) {
      this.wsClient.removeConnectionStatusListener(listener);
    }
  }
  
  // ===== 工具方法 =====
  
  /**
   * 将用户角色映射到发送者类型
   */
  private mapUserRoleToSenderType(role: string): SenderType {
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
  
  /**
   * 获取设备信息
   */
  public getDeviceInfo(): DeviceInfo | null {
    return this.deviceInfo;
  }
  
  /**
   * 获取设备ID
   */
  public getDeviceId(): string | null {
    return this.deviceInfo?.deviceId || null;
  }
  
  /**
   * 获取设备IP
   */
  public getDeviceIP(): string | null {
    return this.deviceInfo?.ip || null;
  }
}

/**
 * 导出WebSocket管理器单例
 */
export const chatWebSocket = new ChatWebSocketManager(); 