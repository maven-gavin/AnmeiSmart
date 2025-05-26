import { EventEmitter } from 'events';
import { WebSocketConnection } from './connection';
import { ConnectionStatus } from '../types';

/**
 * WebSocket重连机制
 * 负责在连接断开时自动尝试重新连接
 */
export class WebSocketReconnector extends EventEmitter {
  private connection: WebSocketConnection;
  private attempts: number = 0;
  private maxAttempts: number = 10;
  private baseDelay: number = 1000;
  private maxDelay: number = 30000;
  private timer: NodeJS.Timeout | null = null;
  private isEnabled: boolean = true;
  private lastUrl: string = '';
  private lastParams: Record<string, any> = {};
  private exponentialBackoff: boolean = true;

  /**
   * 构造函数
   * @param connection WebSocket连接实例
   * @param options 重连选项
   */
  constructor(
    connection: WebSocketConnection, 
    options?: {
      maxAttempts?: number;
      baseDelay?: number;
      maxDelay?: number;
      exponentialBackoff?: boolean;
    }
  ) {
    super();
    this.connection = connection;
    
    // 应用选项
    if (options) {
      if (typeof options.maxAttempts === 'number' && options.maxAttempts > 0) {
        this.maxAttempts = options.maxAttempts;
      }
      
      if (typeof options.baseDelay === 'number' && options.baseDelay > 0) {
        this.baseDelay = options.baseDelay;
      }
      
      if (typeof options.maxDelay === 'number' && options.maxDelay > this.baseDelay) {
        this.maxDelay = options.maxDelay;
      }
      
      if (typeof options.exponentialBackoff === 'boolean') {
        this.exponentialBackoff = options.exponentialBackoff;
      }
    }
    
    // 监听连接状态变化
    this.connection.on('statusChange', this.handleConnectionStatusChange.bind(this));
    this.connection.on('open', this.handleConnectionOpen.bind(this));
    this.connection.on('close', this.handleConnectionClose.bind(this));
    this.connection.on('error', this.handleConnectionError.bind(this));
  }

  /**
   * 启用重连机制
   */
  public enable(): void {
    this.isEnabled = true;
    this.emit('enabled');
  }

  /**
   * 禁用重连机制
   */
  public disable(): void {
    this.isEnabled = false;
    
    // 取消可能正在进行的重连计时器
    this.cancelReconnect();
    
    this.emit('disabled');
  }

  /**
   * 立即触发重连
   */
  public reconnectNow(): void {
    // 取消现有重连计时器
    this.cancelReconnect();
    
    // 立即执行重连
    this.performReconnect();
  }

  /**
   * 重置重连状态
   */
  public reset(): void {
    this.attempts = 0;
    this.cancelReconnect();
    this.emit('reset');
  }

  /**
   * 获取重连状态
   */
  public getStatus(): {
    isEnabled: boolean;
    attempts: number;
    maxAttempts: number;
    nextDelay: number;
  } {
    return {
      isEnabled: this.isEnabled,
      attempts: this.attempts,
      maxAttempts: this.maxAttempts,
      nextDelay: this.calculateDelay()
    };
  }

  /**
   * 计算重连延迟时间
   */
  private calculateDelay(): number {
    if (!this.exponentialBackoff) {
      return this.baseDelay;
    }
    
    // 指数退避算法: baseDelay * 2^attempts
    const delay = this.baseDelay * Math.pow(2, this.attempts);
    
    // 添加一些随机性，避免多个客户端同时重连
    const jitter = Math.random() * 0.3 * delay;
    
    // 确保不超过最大延迟
    return Math.min(delay + jitter, this.maxDelay);
  }

  /**
   * 处理连接状态变化
   */
  private handleConnectionStatusChange(event: any): void {
    // 保存连接参数，用于重连
    if (event.newStatus === ConnectionStatus.CONNECTED) {
      this.lastUrl = this.connection.getUrl();
      this.lastParams = this.connection.getConnectionParams();
    }
  }

  /**
   * 处理连接打开事件
   */
  private handleConnectionOpen(event: any): void {
    // 连接成功，重置重连计数
    this.attempts = 0;
    this.cancelReconnect();
    this.emit('reconnected', { 
      attempts: this.attempts,
      connectionId: event.connectionId
    });
  }

  /**
   * 处理连接关闭事件
   */
  private handleConnectionClose(event: any): void {
    // 只有在启用了重连机制且不是正常关闭时才尝试重连
    if (!this.isEnabled) {
      return;
    }
    
    // 如果是服务器要求关闭或应用主动关闭，则不重连
    if (event.code === 1000 && event.wasClean) {
      return;
    }
    
    this.scheduleReconnect();
  }

  /**
   * 处理连接错误事件
   */
  private handleConnectionError(event: any): void {
    // 连接错误时，如果启用了重连，则尝试重连
    if (this.isEnabled) {
      this.scheduleReconnect();
    }
  }

  /**
   * 计划执行重连
   */
  private scheduleReconnect(): void {
    // 取消可能存在的重连计时器
    this.cancelReconnect();
    
    // 如果已经达到最大尝试次数，则不再重连
    if (this.attempts >= this.maxAttempts) {
      this.emit('maxAttemptsReached', {
        attempts: this.attempts,
        maxAttempts: this.maxAttempts
      });
      return;
    }
    
    // 计算延迟时间
    const delay = this.calculateDelay();
    
    // 发出计划重连事件
    this.emit('reconnectScheduled', {
      attempt: this.attempts + 1,
      delay,
      maxAttempts: this.maxAttempts
    });
    
    // 设置计时器，延迟执行重连
    this.timer = setTimeout(() => {
      this.performReconnect();
    }, delay);
  }

  /**
   * 取消重连计时器
   */
  private cancelReconnect(): void {
    if (this.timer) {
      clearTimeout(this.timer);
      this.timer = null;
    }
  }

  /**
   * 执行重连
   */
  private performReconnect(): void {
    // 如果没有保存URL，则无法重连
    if (!this.lastUrl) {
      console.error('WebSocket重连失败: 缺少连接URL', {
        lastUrl: this.lastUrl,
        lastParams: this.lastParams
      });
      this.emit('error', { message: '无法重连：缺少连接URL' });
      return;
    }

    // 确保URL格式正确
    try {
      new URL(this.lastUrl); // 测试URL是否有效
    } catch (error) {
      console.error('WebSocket重连失败: URL格式无效', {
        lastUrl: this.lastUrl,
        error
      });
      this.emit('error', { message: `无法重连：URL格式无效 (${this.lastUrl})` });
      return;
    }
    
    // 增加尝试次数
    this.attempts++;
    
    // 发出重连尝试事件
    console.log(`正在尝试WebSocket重连 (第${this.attempts}次)`, {
      url: this.lastUrl,
      params: this.lastParams
    });
    
    this.emit('reconnectAttempt', {
      attempt: this.attempts,
      maxAttempts: this.maxAttempts,
      url: this.lastUrl
    });
    
    // 尝试重连
    try {
      this.connection.connect(this.lastUrl, this.lastParams)
        .then(() => {
          console.log('WebSocket重连成功');
          // 重连成功，重置计数
          this.attempts = 0;
        })
        .catch(error => {
          console.error('WebSocket重连失败:', error);
          
          // 发出错误事件
          this.emit('reconnectFailure', {
            error,
            attempt: this.attempts,
            maxAttempts: this.maxAttempts
          });
          
          // 如果未达到最大尝试次数，计划下一次尝试
          if (this.attempts < this.maxAttempts) {
            this.scheduleReconnect();
          } else {
            this.emit('maxAttemptsReached', {
              attempts: this.attempts,
              maxAttempts: this.maxAttempts
            });
          }
        });
    } catch (error) {
      console.error('WebSocket重连出错:', error);
      
      // 发出错误事件
      this.emit('error', {
        error,
        message: '执行重连时出错'
      });
      
      // 如果未达到最大尝试次数，计划下一次尝试
      if (this.attempts < this.maxAttempts) {
        this.scheduleReconnect();
      } else {
        this.emit('maxAttemptsReached', {
          attempts: this.attempts,
          maxAttempts: this.maxAttempts
        });
      }
    }
  }
} 