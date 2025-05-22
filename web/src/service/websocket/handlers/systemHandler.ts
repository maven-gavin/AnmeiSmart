import { MessageHandler } from './messageHandler';
import { MessageData, MessageType } from '../types';

/**
 * 系统消息处理器
 * 处理系统、连接等服务类消息
 */
export class SystemMessageHandler extends MessageHandler {
  /**
   * 构造函数
   * @param priority 处理器优先级
   */
  constructor(priority: number = 5) {
    // 系统消息通常需要优先处理，所以优先级设置较高（数字较小）
    super('SystemMessageHandler', [
      MessageType.SYSTEM,
      MessageType.CONNECT,
      MessageType.HEARTBEAT,
      MessageType.COMMAND
    ], priority);
  }
  
  /**
   * 处理系统消息
   * @param message 待处理的消息
   * @returns 处理结果，true表示已处理，false表示未处理
   */
  public handle(message: MessageData): boolean {
    if (!this.canHandle(message)) {
      return false;
    }
    
    // 根据消息类型调用不同的回调
    switch (message.type) {
      case MessageType.SYSTEM:
        this.invokeCallbacks('system', message);
        break;
        
      case MessageType.CONNECT:
        this.invokeCallbacks('connect', message);
        break;
        
      case MessageType.HEARTBEAT:
        this.invokeCallbacks('heartbeat', message);
        break;
        
      case MessageType.COMMAND:
        this.invokeCallbacks('command', message);
        
        // 如果消息中有特定命令，还可以针对命令类型调用特定回调
        if (message.metadata?.command) {
          this.invokeCallbacks(`command:${message.metadata.command}`, message);
        }
        break;
    }
    
    // 所有系统消息都通过公共系统消息事件发送
    this.invokeCallbacks('systemMessage', message);
    
    return true;
  }
  
  /**
   * 添加系统消息回调
   * @param callback 回调函数
   */
  public addSystemCallback(callback: (data: MessageData) => void): void {
    this.addCallback('system', callback);
  }
  
  /**
   * 添加连接消息回调
   * @param callback 回调函数
   */
  public addConnectCallback(callback: (data: MessageData) => void): void {
    this.addCallback('connect', callback);
  }
  
  /**
   * 添加心跳消息回调
   * @param callback 回调函数
   */
  public addHeartbeatCallback(callback: (data: MessageData) => void): void {
    this.addCallback('heartbeat', callback);
  }
  
  /**
   * 添加命令消息回调
   * @param command 命令名称，如果为空则处理所有命令
   * @param callback 回调函数
   */
  public addCommandCallback(command: string | null, callback: (data: MessageData) => void): void {
    if (command) {
      this.addCallback(`command:${command}`, callback);
    } else {
      this.addCallback('command', callback);
    }
  }
  
  /**
   * 移除系统消息回调
   * @param callback 回调函数
   */
  public removeSystemCallback(callback: (data: MessageData) => void): boolean {
    return this.removeCallback('system', callback);
  }
  
  /**
   * 移除连接消息回调
   * @param callback 回调函数
   */
  public removeConnectCallback(callback: (data: MessageData) => void): boolean {
    return this.removeCallback('connect', callback);
  }
  
  /**
   * 移除心跳消息回调
   * @param callback 回调函数
   */
  public removeHeartbeatCallback(callback: (data: MessageData) => void): boolean {
    return this.removeCallback('heartbeat', callback);
  }
  
  /**
   * 移除命令消息回调
   * @param command 命令名称，如果为空则移除所有命令回调
   * @param callback 回调函数
   */
  public removeCommandCallback(command: string | null, callback: (data: MessageData) => void): boolean {
    if (command) {
      return this.removeCallback(`command:${command}`, callback);
    } else {
      return this.removeCallback('command', callback);
    }
  }
} 