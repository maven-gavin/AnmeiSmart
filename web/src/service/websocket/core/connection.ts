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
  private timeoutId: NodeJS.Timeout | null = null;
  private connectionTimeout: number = 10000; // 默认10秒超时
  
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

        // 更详细的日志，包括完整URL
        console.log(`开始连接WebSocket: ${url}`, params);

        // 关闭现有连接
        this.close();
        
        // 保存连接参数
        this.url = url;
        this.connectionParams = { ...params };
        this.connectionId = params.connectionId || crypto.randomUUID();
        
        // 创建WebSocket对象
        const socket = new WebSocket(url);
        this.socket = socket;
        
        // 更新状态为连接中
        this.setStatus(ConnectionStatus.CONNECTING);
        
        // 设置连接超时
        if (this.connectionTimeout > 0) {
          this.timeoutId = setTimeout(() => {
            this.handleConnectionTimeout();
          }, this.connectionTimeout);
        }

        // 连接事件处理
        socket.onopen = (event) => {
          console.log(`WebSocket连接成功: ${url}`);
          
          // 清除超时定时器
          if (this.timeoutId) {
            clearTimeout(this.timeoutId);
            this.timeoutId = null;
          }
          
          // 更新状态为已连接
          this.setStatus(ConnectionStatus.CONNECTED);
          
          // 触发open事件
          this.emit('open', {
            event,
            connectionId: this.connectionId,
            timestamp: Date.now()
          });
          
          // 解析Promise
          resolve(socket);
        };

        // 消息事件处理
        socket.onmessage = (event) => {
          // 触发message事件
          this.emit('message', event);
        };

        // 关闭事件处理
        socket.onclose = (event) => {
          console.log(`WebSocket连接关闭: ${url}, code=${event.code}, reason=${event.reason}`);
          
          // 清除超时定时器
          if (this.timeoutId) {
            clearTimeout(this.timeoutId);
            this.timeoutId = null;
          }
          
          // 更新状态为断开
          this.setStatus(ConnectionStatus.DISCONNECTED);
          
          // 触发close事件
          this.emit('close', {
            event,
            code: event.code,
            reason: event.reason,
            wasClean: event.wasClean,
            connectionId: this.connectionId,
            timestamp: Date.now()
          });
          
          // 清理socket引用
          this.socket = null;
        };

        // 错误事件处理
        socket.onerror = (event) => {
          console.error(`WebSocket连接错误: ${url}`, event);
          
          // 清除超时定时器
          if (this.timeoutId) {
            clearTimeout(this.timeoutId);
            this.timeoutId = null;
          }
          
          // 更新状态为错误
          this.setStatus(ConnectionStatus.ERROR);
          
          // 触发error事件
          this.emit('error', {
            event,
            connectionId: this.connectionId,
            timestamp: Date.now()
          });
          
          // 如果仍在连接中，则reject Promise
          if (this.status === ConnectionStatus.CONNECTING) {
            reject(new Error('WebSocket连接错误'));
          }
        };
      } catch (error) {
        console.error('WebSocket连接失败:', error);
        
        // 清除超时定时器
        if (this.timeoutId) {
          clearTimeout(this.timeoutId);
          this.timeoutId = null;
        }
        
        // 更新状态为断开
        this.setStatus(ConnectionStatus.DISCONNECTED);
        
        // reject Promise
        reject(error);
      }
    });
  }
  
  /**
   * 关闭WebSocket连接
   */
  public close(): void {
    // 清除超时定时器
    if (this.timeoutId) {
      clearTimeout(this.timeoutId);
      this.timeoutId = null;
    }
    
    // 关闭WebSocket连接
    if (this.socket) {
      try {
        // 只有在连接已打开或连接中的情况下才关闭
        if (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING) {
          this.socket.close();
          
          // 手动关闭不会触发onclose事件，所以这里需要手动设置状态
          // 但如果状态已经是断开的，则不需要再次设置
          if (this.status !== ConnectionStatus.DISCONNECTED) {
            this.setStatus(ConnectionStatus.DISCONNECTED);
          }
        }
      } catch (error) {
        console.error('关闭WebSocket连接出错:', error);
      }
      
      // 清理socket引用
      this.socket = null;
    } else if (this.status !== ConnectionStatus.DISCONNECTED) {
      // 如果没有socket但状态不是断开，则更新状态
      this.setStatus(ConnectionStatus.DISCONNECTED);
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
   * 获取WebSocket原生连接状态
   * 返回WebSocket.readyState
   * CONNECTING = 0, OPEN = 1, CLOSING = 2, CLOSED = 3
   */
  public getNativeState(): number {
    if (this.socket) {
      return this.socket.readyState;
    }
    return WebSocket.CLOSED; // 默认返回已关闭状态
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
  private setStatus(newStatus: ConnectionStatus): void {
    if (this.status !== newStatus) {
      const oldStatus = this.status;
      this.status = newStatus;
      
      // 记录状态变更
      console.log(`WebSocket连接状态变更: ${oldStatus} -> ${newStatus}, ID=${this.connectionId}`);
      
      // 触发状态变更事件
      this.emit('statusChange', {
        oldStatus,
        newStatus,
        connectionId: this.connectionId,
        timestamp: Date.now()
      });
      
      // 特定状态事件
      if (newStatus === ConnectionStatus.CONNECTED) {
        this.emit('connected', {
          connectionId: this.connectionId,
          timestamp: Date.now()
        });
      } else if (newStatus === ConnectionStatus.DISCONNECTED) {
        this.emit('disconnected', {
          connectionId: this.connectionId,
          timestamp: Date.now()
        });
      }
    }
  }

  // 连接超时处理
  private handleConnectionTimeout(): void {
    if (this.status === ConnectionStatus.CONNECTING) {
      // 如果仍在连接中，则设置为断开
      this.setStatus(ConnectionStatus.DISCONNECTED);
      
      // 触发连接超时事件
      this.emit('timeout', {
        url: this.url,
        connectionId: this.connectionId,
        timestamp: Date.now()
      });
      
      // 关闭任何可能存在的连接
      if (this.socket) {
        try {
          this.socket.close();
        } catch (error) {
          // 忽略关闭错误
        }
        this.socket = null;
      }
      
      // 触发错误事件
      this.emit('error', {
        type: 'timeout',
        message: '连接超时',
        url: this.url,
        connectionId: this.connectionId,
        timestamp: Date.now()
      });
    }
  }
} 