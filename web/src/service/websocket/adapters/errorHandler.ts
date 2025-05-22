import { ConnectionStatus } from '../types';

/**
 * 错误日志级别
 */
export enum LogLevel {
  DEBUG = 'debug',
  INFO = 'info',
  WARN = 'warn',
  ERROR = 'error'
}

/**
 * 错误类型枚举
 */
export enum ErrorType {
  CONNECTION = 'connection',     // 连接错误
  MESSAGE = 'message',           // 消息处理错误
  SERIALIZATION = 'serialization', // 序列化错误
  HEARTBEAT = 'heartbeat',       // 心跳错误
  TIMEOUT = 'timeout',           // 超时错误
  UNKNOWN = 'unknown'            // 未知错误
}

/**
 * WebSocket错误接口
 */
export interface WebSocketError {
  type: ErrorType | string;
  message: string;
  originalError?: any;
  details?: any;
  timestamp: Date;
  stack?: string;
  toString: () => string;
}

/**
 * WebSocket错误处理适配器
 * 负责统一处理不同类型的错误，提供一致的错误接口
 */
export class WebSocketErrorHandler {
  // 错误处理回调
  private handlers: Map<ErrorType | string, Set<(error: WebSocketError) => void>> = new Map();
  
  // 是否启用调试模式
  private debugMode: boolean = false;
  
  /**
   * 构造函数
   * @param debugMode 是否启用调试模式
   */
  constructor(debugMode: boolean = false) {
    this.debugMode = debugMode;
  }
  
  /**
   * 处理连接错误
   * @param error 错误对象
   * @param details 错误详情
   * @returns 标准化的错误对象
   */
  public handleConnectionError(error: any, details?: any): WebSocketError {
    const wsError = this.createError(
      ErrorType.CONNECTION,
      '连接错误',
      error,
      details
    );
    
    this.invokeHandlers(ErrorType.CONNECTION, wsError);
    this.logError(wsError, LogLevel.ERROR);
    
    return wsError;
  }
  
  /**
   * 处理消息错误
   * @param error 错误对象
   * @param message 相关消息
   * @returns 标准化的错误对象
   */
  public handleMessageError(error: any, message?: any): WebSocketError {
    const wsError = this.createError(
      ErrorType.MESSAGE,
      '消息处理错误',
      error,
      { message }
    );
    
    this.invokeHandlers(ErrorType.MESSAGE, wsError);
    this.logError(wsError, LogLevel.WARN);
    
    return wsError;
  }
  
  /**
   * 处理序列化错误
   * @param error 错误对象
   * @param data 相关数据
   * @returns 标准化的错误对象
   */
  public handleSerializationError(error: any, data?: any): WebSocketError {
    const wsError = this.createError(
      ErrorType.SERIALIZATION,
      '序列化/反序列化错误',
      error,
      { data }
    );
    
    this.invokeHandlers(ErrorType.SERIALIZATION, wsError);
    this.logError(wsError, LogLevel.WARN);
    
    return wsError;
  }
  
  /**
   * 处理心跳错误
   * @param error 错误对象
   * @param details 错误详情
   * @returns 标准化的错误对象
   */
  public handleHeartbeatError(error: any, details?: any): WebSocketError {
    const wsError = this.createError(
      ErrorType.HEARTBEAT,
      '心跳机制错误',
      error,
      details
    );
    
    this.invokeHandlers(ErrorType.HEARTBEAT, wsError);
    this.logError(wsError, LogLevel.WARN);
    
    return wsError;
  }
  
  /**
   * 处理超时错误
   * @param operation 超时的操作
   * @param timeout 超时时间（毫秒）
   * @returns 标准化的错误对象
   */
  public handleTimeoutError(operation: string, timeout: number): WebSocketError {
    const wsError = this.createError(
      ErrorType.TIMEOUT,
      `操作超时: ${operation}`,
      new Error(`操作超时: ${operation}，超时时间: ${timeout}ms`),
      { operation, timeout }
    );
    
    this.invokeHandlers(ErrorType.TIMEOUT, wsError);
    this.logError(wsError, LogLevel.WARN);
    
    return wsError;
  }
  
  /**
   * 处理其他类型错误
   * @param type 错误类型
   * @param error 错误对象
   * @param details 错误详情
   * @returns 标准化的错误对象
   */
  public handleError(type: string, error: any, details?: any): WebSocketError {
    const wsError = this.createError(
      type || ErrorType.UNKNOWN,
      `错误: ${type}`,
      error,
      details
    );
    
    this.invokeHandlers(type, wsError);
    this.invokeHandlers(ErrorType.UNKNOWN, wsError);
    this.logError(wsError, LogLevel.ERROR);
    
    return wsError;
  }
  
  /**
   * 注册错误处理器
   * @param type 错误类型，如果为空则处理所有类型错误
   * @param handler 处理函数
   */
  public registerHandler(type: ErrorType | string | null, handler: (error: WebSocketError) => void): void {
    // 如果类型为空，则注册为通用处理器
    const errorType = type || '*';
    
    if (!this.handlers.has(errorType)) {
      this.handlers.set(errorType, new Set());
    }
    
    this.handlers.get(errorType)!.add(handler);
  }
  
  /**
   * 注销错误处理器
   * @param type 错误类型
   * @param handler 处理函数
   * @returns 是否成功注销
   */
  public unregisterHandler(type: ErrorType | string, handler: (error: WebSocketError) => void): boolean {
    if (!this.handlers.has(type)) {
      return false;
    }
    
    const handlers = this.handlers.get(type)!;
    const result = handlers.delete(handler);
    
    // 如果集合为空，则删除该类型
    if (handlers.size === 0) {
      this.handlers.delete(type);
    }
    
    return result;
  }
  
  /**
   * 清除所有处理器
   */
  public clearHandlers(): void {
    this.handlers.clear();
  }
  
  /**
   * 设置调试模式
   * @param enabled 是否启用
   */
  public setDebugMode(enabled: boolean): void {
    this.debugMode = enabled;
  }
  
  /**
   * 创建标准错误对象
   * @param type 错误类型
   * @param message 错误消息
   * @param originalError 原始错误
   * @param details 错误详情
   * @returns 标准化的错误对象
   */
  private createError(
    type: ErrorType | string,
    message: string,
    originalError?: any,
    details?: any
  ): WebSocketError {
    // 提取原始错误信息
    const errorMessage = originalError instanceof Error 
      ? originalError.message 
      : typeof originalError === 'string'
        ? originalError
        : message;
    
    const errorStack = originalError instanceof Error 
      ? originalError.stack 
      : new Error().stack;
    
    // 创建标准错误对象
    return {
      type,
      message: message || errorMessage,
      originalError,
      details,
      timestamp: new Date(),
      stack: errorStack,
      toString: function() {
        return `[WebSocket Error] ${this.type}: ${this.message}`;
      }
    };
  }
  
  /**
   * 调用错误处理器
   * @param type 错误类型
   * @param error 错误对象
   */
  private invokeHandlers(type: ErrorType | string, error: WebSocketError): void {
    // 调用特定类型的处理器
    if (this.handlers.has(type)) {
      const handlers = this.handlers.get(type)!;
      for (const handler of handlers) {
        try {
          handler(error);
        } catch (e) {
          this.logError({
            type: ErrorType.UNKNOWN,
            message: '错误处理器执行失败',
            originalError: e,
            details: { handlerType: type },
            timestamp: new Date(),
            stack: e instanceof Error ? e.stack : undefined,
            toString: () => '[错误处理器执行失败]'
          }, LogLevel.ERROR);
        }
      }
    }
    
    // 调用通用处理器
    if (this.handlers.has('*')) {
      const handlers = this.handlers.get('*')!;
      for (const handler of handlers) {
        try {
          handler(error);
        } catch (e) {
          this.logError({
            type: ErrorType.UNKNOWN,
            message: '通用错误处理器执行失败',
            originalError: e,
            details: { handlerType: '*' },
            timestamp: new Date(),
            stack: e instanceof Error ? e.stack : undefined,
            toString: () => '[通用错误处理器执行失败]'
          }, LogLevel.ERROR);
        }
      }
    }
  }
  
  /**
   * 记录错误日志
   * @param error 错误对象
   * @param level 日志级别
   */
  private logError(error: WebSocketError, level: LogLevel = LogLevel.ERROR): void {
    if (!this.debugMode && level === LogLevel.DEBUG) {
      return;
    }
    
    const logMsg = `${error.toString()} - ${error.message}`;
    
    switch (level) {
      case LogLevel.DEBUG:
        console.debug(logMsg, error);
        break;
      case LogLevel.INFO:
        console.info(logMsg, error);
        break;
      case LogLevel.WARN:
        console.warn(logMsg, error);
        break;
      case LogLevel.ERROR:
      default:
        console.error(logMsg, error);
        break;
    }
  }
} 