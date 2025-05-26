import { EventEmitter } from 'events';
import { ConnectionStatus } from '../types';

/**
 * WebSocket连接管理器 - 核心层
 * 负责WebSocket连接的创建、管理和监控
 */
export class WebSocketConnection extends EventEmitter {
  private socket: WebSocket | null = null;
  private url: string = '';
  private status: ConnectionStatus = ConnectionStatus.DISCONNECTED;
  private connectionId: string = '';
  private connectionParams: Record<string, any> = {};
  
  /**
   * 创建WebSocket连接
   * @param url WebSocket服务URL
   * @param params 连接参数
   * @returns 成功创建的连接
   */
  public connect(url: string, params: Record<string, any> = {}): Promise<WebSocket> {
    return new Promise((resolve, reject) => {
      try {
        // 验证URL
        if (!url || url.trim() === '') {
          const error = new Error('WebSocket连接URL不能为空');
          console.error(error);
          reject(error);
          return;
        }

        // 验证URL格式
        try {
          new URL(url);
        } catch (error) {
          console.error(`WebSocket连接URL格式无效: ${url}`, error);
          reject(new Error(`WebSocket连接URL格式无效: ${url}`));
          return;
        }

        console.log(`开始连接WebSocket: ${url}`, params);

        // 关闭现有连接
        this.close();
        
        // 保存连接参数
        this.url = url;
        this.connectionParams = { ...params };
        this.connectionId = params.connectionId || crypto.randomUUID();
        
        // 更新状态
        this.updateStatus(ConnectionStatus.CONNECTING);
        
        // 创建新连接
        this.socket = new WebSocket(url);
        
        // 设置事件监听
        this.socket.onopen = (event) => {
          console.log(`WebSocket连接成功: ${url}`);
          this.updateStatus(ConnectionStatus.CONNECTED);
          this.emit('open', { event, connectionId: this.connectionId });
          resolve(this.socket as WebSocket);
        };
        
        this.socket.onclose = (event) => {
          console.log(`WebSocket连接关闭: ${url}`, {
            code: event.code,
            reason: event.reason,
            wasClean: event.wasClean
          });
          this.updateStatus(ConnectionStatus.DISCONNECTED);
          this.emit('close', { 
            event, 
            connectionId: this.connectionId,
            code: event.code,
            reason: event.reason,
            wasClean: event.wasClean
          });
        };
        
        this.socket.onerror = (event) => {
          console.error(`WebSocket连接错误: ${url}`, event);
          this.updateStatus(ConnectionStatus.ERROR);
          this.emit('error', { 
            event, 
            connectionId: this.connectionId,
            message: 'WebSocket连接错误'
          });
          reject(new Error('WebSocket连接错误'));
        };
        
        this.socket.onmessage = (event) => {
          this.emit('message', { 
            data: event.data, 
            connectionId: this.connectionId 
          });
        };
      } catch (error) {
        console.error(`WebSocket连接初始化失败: ${url}`, error);
        this.updateStatus(ConnectionStatus.ERROR);
        this.emit('error', { 
          error, 
          connectionId: this.connectionId,
          message: 'WebSocket连接初始化失败'
        });
        reject(error);
      }
    });
  }
  
  /**
   * 关闭WebSocket连接
   */
  public close(): void {
    if (this.socket) {
      try {
        // 仅在连接或连接中状态才需要关闭
        if (this.socket.readyState === WebSocket.OPEN || 
            this.socket.readyState === WebSocket.CONNECTING) {
          this.socket.close();
        }
      } catch (error) {
        this.emit('error', { 
          error, 
          connectionId: this.connectionId,
          message: '关闭WebSocket连接时出错'
        });
      } finally {
        this.socket = null;
        this.updateStatus(ConnectionStatus.DISCONNECTED);
      }
    }
  }
  
  /**
   * 发送消息
   * @param data 要发送的数据
   * @returns 是否发送成功
   */
  public send(data: string | ArrayBufferLike | Blob | ArrayBufferView): boolean {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      this.emit('error', { 
        connectionId: this.connectionId,
        message: '无法发送消息：WebSocket未连接'
      });
      return false;
    }
    
    try {
      this.socket.send(data);
      return true;
    } catch (error) {
      this.emit('error', { 
        error, 
        connectionId: this.connectionId,
        message: '发送消息失败'
      });
      return false;
    }
  }
  
  /**
   * 获取当前连接状态
   */
  public getStatus(): ConnectionStatus {
    return this.status;
  }
  
  /**
   * 获取连接ID
   */
  public getConnectionId(): string {
    return this.connectionId;
  }
  
  /**
   * 获取连接参数
   */
  public getConnectionParams(): Record<string, any> {
    return { ...this.connectionParams };
  }
  
  /**
   * 获取URL
   */
  public getUrl(): string {
    return this.url;
  }
  
  /**
   * 检查连接是否处于已连接状态
   */
  public isConnected(): boolean {
    return this.status === ConnectionStatus.CONNECTED;
  }
  
  /**
   * 更新状态并触发状态变更事件
   */
  private updateStatus(newStatus: ConnectionStatus): void {
    const oldStatus = this.status;
    this.status = newStatus;
    
    if (oldStatus !== newStatus) {
      this.emit('statusChange', {
        oldStatus,
        newStatus,
        connectionId: this.connectionId
      });
    }
  }
} 