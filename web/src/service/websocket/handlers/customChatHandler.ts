import { MessageHandler } from './messageHandler';
import { MessageData, MessageType, SenderType } from '../types';

/**
 * 自定义聊天消息处理器
 * 专门处理与聊天功能相关的消息
 */
export class CustomChatHandler extends MessageHandler {
  // 聊天相关事件类型
  private static readonly EVENT_NEW_MESSAGE = 'newMessage';
  private static readonly EVENT_MESSAGE_READ = 'messageRead';
  private static readonly EVENT_TAKEOVER = 'takeover';
  private static readonly EVENT_SYNC = 'sync';
  
  /**
   * 构造函数
   */
  constructor() {
    super(
      'CustomChatHandler',
      [MessageType.TEXT, MessageType.IMAGE, MessageType.VOICE],
      10 // 优先级设置为10
    );
  }
  
  /**
   * 处理消息
   * @param message 待处理的消息
   * @returns 是否已处理
   */
  public handle(message: MessageData): boolean {
    // 检查消息动作类型
    const action = message.metadata?.action;
    
    // 根据不同动作类型处理
    switch (action) {
      case 'message':
        // 处理新消息
        this.handleNewMessage(message);
        return true;
        
      case 'read':
        // 处理消息已读
        this.handleMessageRead(message);
        return true;
        
      case 'takeover':
        // 处理会话接管
        this.handleTakeover(message);
        return true;
        
      case 'sync':
        // 处理同步请求
        this.handleSync(message);
        return true;
        
      default:
        // 如果没有特定动作但消息类型是支持的，仍然触发新消息事件
        if (this.supportedTypes.includes(message.type)) {
          this.handleNewMessage(message);
          return true;
        }
        return false;
    }
  }
  
  /**
   * 处理新消息
   * @param message 消息数据
   */
  private handleNewMessage(message: MessageData): void {
    this.invokeCallbacks(CustomChatHandler.EVENT_NEW_MESSAGE, message);
  }
  
  /**
   * 处理消息已读状态
   * @param message 消息数据
   */
  private handleMessageRead(message: MessageData): void {
    this.invokeCallbacks(CustomChatHandler.EVENT_MESSAGE_READ, message);
  }
  
  /**
   * 处理会话接管
   * @param message 消息数据
   */
  private handleTakeover(message: MessageData): void {
    this.invokeCallbacks(CustomChatHandler.EVENT_TAKEOVER, message);
  }
  
  /**
   * 处理同步请求
   * @param message 消息数据
   */
  private handleSync(message: MessageData): void {
    this.invokeCallbacks(CustomChatHandler.EVENT_SYNC, message);
  }
  
  /**
   * 添加新消息监听器
   * @param callback 回调函数
   */
  public onNewMessage(callback: (data: MessageData) => void): void {
    this.addCallback(CustomChatHandler.EVENT_NEW_MESSAGE, callback);
  }
  
  /**
   * 添加消息已读监听器
   * @param callback 回调函数
   */
  public onMessageRead(callback: (data: MessageData) => void): void {
    this.addCallback(CustomChatHandler.EVENT_MESSAGE_READ, callback);
  }
  
  /**
   * 添加会话接管监听器
   * @param callback 回调函数
   */
  public onTakeover(callback: (data: MessageData) => void): void {
    this.addCallback(CustomChatHandler.EVENT_TAKEOVER, callback);
  }
  
  /**
   * 添加同步请求监听器
   * @param callback 回调函数
   */
  public onSync(callback: (data: MessageData) => void): void {
    this.addCallback(CustomChatHandler.EVENT_SYNC, callback);
  }
  
  /**
   * 移除新消息监听器
   * @param callback 回调函数
   */
  public offNewMessage(callback: (data: MessageData) => void): boolean {
    return this.removeCallback(CustomChatHandler.EVENT_NEW_MESSAGE, callback);
  }
  
  /**
   * 移除消息已读监听器
   * @param callback 回调函数
   */
  public offMessageRead(callback: (data: MessageData) => void): boolean {
    return this.removeCallback(CustomChatHandler.EVENT_MESSAGE_READ, callback);
  }
  
  /**
   * 移除会话接管监听器
   * @param callback 回调函数
   */
  public offTakeover(callback: (data: MessageData) => void): boolean {
    return this.removeCallback(CustomChatHandler.EVENT_TAKEOVER, callback);
  }
  
  /**
   * 移除同步请求监听器
   * @param callback 回调函数
   */
  public offSync(callback: (data: MessageData) => void): boolean {
    return this.removeCallback(CustomChatHandler.EVENT_SYNC, callback);
  }
} 