import { MessageHandler } from './messageHandler';
import { MessageData, MessageType } from '../types';

/**
 * 文本消息处理器
 * 专门处理文本类型的消息
 */
export class TextMessageHandler extends MessageHandler {
  /**
   * 构造函数
   * @param priority 处理器优先级
   */
  constructor(priority: number = 10) {
    super('TextMessageHandler', [MessageType.TEXT], priority);
  }
  
  /**
   * 处理文本消息
   * @param message 待处理的消息
   * @returns 处理结果，true表示已处理，false表示未处理
   */
  public handle(message: MessageData): boolean {
    if (!this.canHandle(message)) {
      return false;
    }
    
    // 调用所有注册的回调
    this.invokeCallbacks('text', message);
    this.invokeCallbacks('message', message);
    
    return true;
  }
  
  /**
   * 添加文本消息处理回调
   * @param callback 回调函数
   */
  public addTextCallback(callback: (data: MessageData) => void): void {
    this.addCallback('text', callback);
  }
  
  /**
   * 移除文本消息处理回调
   * @param callback 回调函数
   */
  public removeTextCallback(callback: (data: MessageData) => void): boolean {
    return this.removeCallback('text', callback);
  }
} 