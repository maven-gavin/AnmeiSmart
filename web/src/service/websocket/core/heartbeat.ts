import { EventEmitter } from 'events';
import { WebSocketConnection } from './connection';

/**
 * WebSocket心跳机制
 * 负责定期发送心跳消息以保持连接活跃，并检测连接状态
 */
export class WebSocketHeartbeat extends EventEmitter {
  private connection: WebSocketConnection;
  private interval: number = 30000; // 默认30秒
  private timer: NodeJS.Timeout | null = null;
  private failedHeartbeats: number = 0;
  private maxFailedHeartbeats: number = 3;
  private lastHeartbeatResponse: number = 0;
  private isEnabled: boolean = false;

  /**
   * 构造函数
   * @param connection WebSocket连接实例
   * @param interval 心跳间隔(毫秒)
   */
  constructor(connection: WebSocketConnection, interval?: number) {
    super();
    this.connection = connection;
    
    if (interval && interval > 1000) {
      this.interval = interval;
    }
    
    // 监听连接状态变化
    this.connection.on('statusChange', this.handleConnectionStatusChange.bind(this));
    
    // 监听心跳响应
    this.connection.on('message', this.handleMessage.bind(this));
  }

  /**
   * 启动心跳机制
   */
  public start(): void {
    if (this.isEnabled) {
      return;
    }
    
    this.isEnabled = true;
    this.failedHeartbeats = 0;
    this.lastHeartbeatResponse = Date.now();
    
    // 清除可能存在的定时器
    this.stop();
    
    // 启动新的定时器
    this.timer = setInterval(() => {
      this.sendHeartbeat();
    }, this.interval);
    
    this.emit('start');
  }

  /**
   * 停止心跳机制
   */
  public stop(): void {
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
    }
    
    this.isEnabled = false;
    this.emit('stop');
  }

  /**
   * 设置心跳间隔
   * @param interval 心跳间隔(毫秒)
   */
  public setInterval(interval: number): void {
    if (interval < 1000) {
      throw new Error('心跳间隔不能小于1000毫秒');
    }
    
    this.interval = interval;
    
    // 如果心跳机制已启动，则重新启动以应用新间隔
    if (this.isEnabled) {
      this.stop();
      this.start();
    }
  }

  /**
   * 发送心跳消息
   */
  private sendHeartbeat(): void {
    if (!this.connection.isConnected()) {
      this.failedHeartbeats++;
      this.emit('error', { message: '心跳失败：连接已断开' });
      
      if (this.failedHeartbeats >= this.maxFailedHeartbeats) {
        this.emit('dead', { 
          failedHeartbeats: this.failedHeartbeats,
          lastResponse: this.lastHeartbeatResponse
        });
      }
      return;
    }
    
    try {
      // 发送心跳消息
      const heartbeatMessage = JSON.stringify({
        type: 'heartbeat',
        timestamp: Date.now()
      });
      
      const sent = this.connection.send(heartbeatMessage);
      
      if (!sent) {
        this.failedHeartbeats++;
        this.emit('error', { message: '心跳发送失败' });
        
        if (this.failedHeartbeats >= this.maxFailedHeartbeats) {
          this.emit('dead', { 
            failedHeartbeats: this.failedHeartbeats,
            lastResponse: this.lastHeartbeatResponse
          });
        }
      } else {
        this.emit('beat', { timestamp: Date.now() });
      }
    } catch (error) {
      this.failedHeartbeats++;
      this.emit('error', { 
        error, 
        message: '发送心跳消息时出错'
      });
      
      if (this.failedHeartbeats >= this.maxFailedHeartbeats) {
        this.emit('dead', { 
          failedHeartbeats: this.failedHeartbeats,
          lastResponse: this.lastHeartbeatResponse,
          error
        });
      }
    }
  }

  /**
   * 处理收到的消息
   * @param event 消息事件
   */
  private handleMessage(event: any): void {
    try {
      // 尝试解析消息
      const data = typeof event.data === 'string' 
        ? JSON.parse(event.data)
        : event.data;
      
      // 检查是否是心跳响应
      if (data && data.type === 'heartbeat') {
        this.lastHeartbeatResponse = Date.now();
        this.failedHeartbeats = 0;
        this.emit('response', { 
          timestamp: this.lastHeartbeatResponse,
          data
        });
      }
    } catch (error) {
      // 忽略非JSON消息
    }
  }

  /**
   * 处理连接状态变化
   * @param event 状态变化事件
   */
  private handleConnectionStatusChange(event: any): void {
    // 连接断开时停止心跳
    if (event.newStatus === 'DISCONNECTED' || event.newStatus === 'ERROR') {
      this.stop();
    }
    
    // 连接建立时启动心跳
    if (event.newStatus === 'CONNECTED' && !this.isEnabled) {
      this.start();
    }
  }

  /**
   * 获取当前心跳状态
   */
  public getStatus(): {
    isEnabled: boolean;
    interval: number;
    failedHeartbeats: number;
    lastResponse: number;
  } {
    return {
      isEnabled: this.isEnabled,
      interval: this.interval,
      failedHeartbeats: this.failedHeartbeats,
      lastResponse: this.lastHeartbeatResponse
    };
  }
} 