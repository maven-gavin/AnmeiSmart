import { MessageData, MessageType } from '../types';

/**
 * 消息处理器基类
 * 定义消息处理的基本接口和公共功能
 */
export abstract class MessageHandler {
  // 处理器名称
  protected readonly name: string;
  
  // 处理器优先级（越小优先级越高）
  protected readonly priority: number;
  
  // 消息类型过滤
  protected readonly supportedTypes: MessageType[];
  
  // 回调函数集合
  protected callbacks: Map<string, Set<(data: MessageData) => void>> = new Map();
  
  /**
   * 构造函数
   * @param name 处理器名称
   * @param supportedTypes 支持的消息类型
   * @param priority 处理器优先级
   */
  constructor(name: string, supportedTypes: MessageType[] = [], priority: number = 0) {
    this.name = name;
    this.supportedTypes = supportedTypes;
    this.priority = priority;
  }
  
  /**
   * 判断是否能够处理指定消息
   * @param message 待处理的消息
   * @returns 是否能够处理
   */
  public canHandle(message: MessageData): boolean {
    // 如果未指定支持的类型，则默认支持所有类型
    if (this.supportedTypes.length === 0) {
      return true;
    }
    
    // 检查消息类型是否在支持列表中
    return this.supportedTypes.includes(message.type);
  }
  
  /**
   * 处理消息（子类必须实现）
   * @param message 待处理的消息
   * @returns 处理结果，true表示已处理，false表示未处理
   */
  public abstract handle(message: MessageData): boolean;
  
  /**
   * 获取处理器名称
   */
  public getName(): string {
    return this.name;
  }
  
  /**
   * 获取处理器优先级
   */
  public getPriority(): number {
    return this.priority;
  }
  
  /**
   * 获取支持的消息类型
   */
  public getSupportedTypes(): MessageType[] {
    return [...this.supportedTypes];
  }
  
  /**
   * 添加消息回调
   * @param eventType 事件类型
   * @param callback 回调函数
   */
  public addCallback(eventType: string, callback: (data: MessageData) => void): void {
    if (!this.callbacks.has(eventType)) {
      this.callbacks.set(eventType, new Set());
    }
    
    this.callbacks.get(eventType)!.add(callback);
  }
  
  /**
   * 移除消息回调
   * @param eventType 事件类型
   * @param callback 回调函数
   * @returns 是否成功移除
   */
  public removeCallback(eventType: string, callback: (data: MessageData) => void): boolean {
    if (!this.callbacks.has(eventType)) {
      return false;
    }
    
    const callbacks = this.callbacks.get(eventType)!;
    const result = callbacks.delete(callback);
    
    // 如果集合为空，则删除该事件类型
    if (callbacks.size === 0) {
      this.callbacks.delete(eventType);
    }
    
    return result;
  }
  
  /**
   * 调用回调函数
   * @param eventType 事件类型
   * @param message 消息数据
   */
  protected invokeCallbacks(eventType: string, message: MessageData): void {
    // 检查是否有该事件类型的回调
    if (!this.callbacks.has(eventType)) {
      return;
    }
    
    // 调用所有回调
    const callbacks = this.callbacks.get(eventType)!;
    for (const callback of callbacks) {
      try {
        callback(message);
      } catch (error) {
        console.error(`处理器 ${this.name} 回调执行错误:`, error);
      }
    }
  }
  
  /**
   * 清除所有回调
   */
  public clearCallbacks(): void {
    this.callbacks.clear();
  }
}

/**
 * 消息处理器注册表
 * 管理和协调多个消息处理器
 */
export class MessageHandlerRegistry {
  private handlers: MessageHandler[] = [];
  
  /**
   * 注册消息处理器
   * @param handler 处理器实例
   */
  public registerHandler(handler: MessageHandler): void {
    // 检查是否已存在同名处理器
    const existingIndex = this.handlers.findIndex(h => h.getName() === handler.getName());
    if (existingIndex >= 0) {
      // 替换现有处理器
      this.handlers[existingIndex] = handler;
    } else {
      // 添加新处理器
      this.handlers.push(handler);
      
      // 按优先级排序
      this.handlers.sort((a, b) => a.getPriority() - b.getPriority());
    }
  }
  
  /**
   * 注销消息处理器
   * @param handlerName 处理器名称
   * @returns 是否成功注销
   */
  public unregisterHandler(handlerName: string): boolean {
    const initialLength = this.handlers.length;
    this.handlers = this.handlers.filter(handler => handler.getName() !== handlerName);
    return this.handlers.length < initialLength;
  }
  
  /**
   * 分发消息到合适的处理器
   * @param message 待处理的消息
   * @returns 是否有处理器处理了该消息
   */
  public dispatchMessage(message: MessageData): boolean {
    let handled = false;
    
    // 按优先级遍历处理器
    for (const handler of this.handlers) {
      if (handler.canHandle(message)) {
        try {
          // 如果处理器返回true，表示已处理该消息
          if (handler.handle(message)) {
            handled = true;
            break;
          }
        } catch (error) {
          console.error(`处理器 ${handler.getName()} 处理消息时出错:`, error);
        }
      }
    }
    
    return handled;
  }
  
  /**
   * 获取所有注册的处理器
   */
  public getHandlers(): MessageHandler[] {
    return [...this.handlers];
  }
  
  /**
   * 清除所有处理器
   */
  public clearHandlers(): void {
    this.handlers = [];
  }
} 