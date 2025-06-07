import { MessageHandler, MessageHandlerRegistry } from './messageHandler';
import { MessageEventHandler } from './messageEventHandler';
import { MessageType } from '../types';

/**
 * 创建默认的处理器注册表 - 新分布式架构
 * @returns 包含默认处理器的注册表
 */
export function createDefaultHandlerRegistry(): MessageHandlerRegistry {
  const registry = new MessageHandlerRegistry();
  
  // 注册新架构的事件处理器
  registry.registerHandler(new MessageEventHandler());
  
  return registry;
}

/**
 * 创建自定义消息处理器
 * @param name 处理器名称
 * @param types 支持的消息类型
 * @param handler 处理函数
 * @param priority 优先级
 * @returns 消息处理器实例
 */
export function createCustomHandler(
  name: string,
  types: MessageType[],
  handler: (message: any) => boolean,
  priority: number = 20
): MessageHandler {
  // 创建匿名处理器类
  class CustomHandler extends MessageHandler {
    constructor() {
      super(name, types, priority);
    }
    
    public handle(message: any): boolean {
      return handler(message);
    }
  }
  
  return new CustomHandler();
}

// 导出所有消息处理器
export {
  MessageHandler,
  MessageHandlerRegistry,
  MessageEventHandler
}; 