import { MessageHandler } from './messageHandler';
import { MessageData, MessageType } from '../types';

/**
 * 消息事件处理器
 * 专门处理来自新WebSocket架构的消息广播事件
 * 
 * 新架构中，WebSocket主要接收以下类型的事件：
 * - new_message: 新消息广播
 * - presence_update: 在线状态更新
 * - typing_update: 输入状态更新
 * - conversation_update: 会话更新
 */
export class MessageEventHandler extends MessageHandler {
  /**
   * 构造函数
   * @param priority 处理器优先级
   */
  constructor(priority: number = 5) {
    // 处理所有类型的消息，因为我们需要根据event_type来判断
    super('MessageEventHandler', [MessageType.TEXT, MessageType.SYSTEM], priority);
  }
  
  /**
   * 处理消息事件
   * @param message 待处理的消息
   * @returns 处理结果，true表示已处理，false表示未处理
   */
  public handle(message: MessageData): boolean {
    // 检查是否是事件消息格式
    if (!this.isEventMessage(message)) {
      return false;
    }
    
    const eventType = this.getEventType(message);
    const eventData = this.getEventData(message);
    
    console.log(`处理WebSocket事件: ${eventType}`, eventData);
    
    // 根据事件类型分发处理
    switch (eventType) {
      case 'new_message':
        this.handleNewMessage(eventData);
        break;
        
      case 'presence_update':
        this.handlePresenceUpdate(eventData);
        break;
        
      case 'typing_update':
        this.handleTypingUpdate(eventData);
        break;
        
      case 'conversation_update':
        this.handleConversationUpdate(eventData);
        break;
        
      case 'system_notification':
        this.handleSystemNotification(eventData);
        break;
        
      default:
        console.log(`未知的事件类型: ${eventType}`, eventData);
        // 调用通用事件处理器
        this.invokeCallbacks('unknown_event', eventData);
        break;
    }
    
    // 调用通用事件回调
    this.invokeCallbacks('event', eventData);
    
    return true;
  }
  
  /**
   * 检查是否是事件消息格式
   */
  private isEventMessage(message: MessageData): boolean {
    return !!(message as any).event_type || !!(message as any).action;
  }
  
  /**
   * 获取事件类型
   */
  private getEventType(message: MessageData): string {
    return (message as any).event_type || (message as any).action || 'unknown';
  }
  
  /**
   * 获取事件数据
   */
  private getEventData(message: MessageData): any {
    return (message as any).data || (message as any).payload || message;
  }
  
  /**
   * 处理新消息事件
   */
  private handleNewMessage(eventData: any): void {
    console.log('[MessageEventHandler] 处理新消息事件:', {
      eventData,
      eventDataType: typeof eventData,
      eventDataKeys: eventData ? Object.keys(eventData) : [],
      conversationId: eventData?.conversation_id,
      messageId: eventData?.id
    });
    this.invokeCallbacks('new_message', eventData);
  }
  
  /**
   * 处理在线状态更新事件
   */
  private handlePresenceUpdate(eventData: any): void {
    this.invokeCallbacks('presence_update', eventData);
  }
  
  /**
   * 处理输入状态更新事件
   */
  private handleTypingUpdate(eventData: any): void {
    this.invokeCallbacks('typing_update', eventData);
  }
  
  /**
   * 处理会话更新事件
   */
  private handleConversationUpdate(eventData: any): void {
    this.invokeCallbacks('conversation_update', eventData);
  }
  
  /**
   * 处理系统通知事件
   */
  private handleSystemNotification(eventData: any): void {
    this.invokeCallbacks('system_notification', eventData);
  }
  
  /**
   * 添加新消息事件回调
   */
  public addNewMessageCallback(callback: (data: any) => void): void {
    this.addCallback('new_message', callback);
  }
  
  /**
   * 添加在线状态更新回调
   */
  public addPresenceUpdateCallback(callback: (data: any) => void): void {
    this.addCallback('presence_update', callback);
  }
  
  /**
   * 添加通用事件回调
   */
  public addEventCallback(callback: (data: any) => void): void {
    this.addCallback('event', callback);
  }
} 