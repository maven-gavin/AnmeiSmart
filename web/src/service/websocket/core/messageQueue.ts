import { EventEmitter } from 'events';

/**
 * 消息队列配置
 */
export interface MessageQueueConfig {
  maxQueueSize?: number;         // 最大队列长度
  persistenceEnabled?: boolean;  // 是否启用持久化
  storageKey?: string;           // 本地存储键名
}

/**
 * 队列消息
 */
export interface QueuedMessage {
  id: string;              // 消息ID
  message: any;            // 消息内容
  timestamp: number;       // 消息时间戳
  retryCount: number;      // 重试次数
  conversationId?: string; // 会话ID
}

/**
 * 消息队列组件
 * 用于在连接中断或未建立时缓存消息，恢复连接后自动发送
 */
export class MessageQueue extends EventEmitter {
  private queue: QueuedMessage[] = [];
  private config: Required<MessageQueueConfig>;
  private isProcessing: boolean = false;
  
  /**
   * 构造函数
   * @param config 队列配置
   */
  constructor(config: MessageQueueConfig = {}) {
    super();
    
    // 设置默认配置
    this.config = {
      maxQueueSize: 100,
      persistenceEnabled: true,
      storageKey: 'ws_message_queue',
      ...config
    };
    
    // 加载持久化的消息
    this.loadPersistedMessages();
  }
  
  /**
   * 添加消息到队列
   * @param message 消息对象
   * @param conversationId 会话ID
   * @returns 队列消息对象
   */
  public enqueue(message: any, conversationId?: string): QueuedMessage {
    // 创建队列消息对象
    const queuedMessage: QueuedMessage = {
      id: message.id || crypto.randomUUID(),
      message,
      timestamp: Date.now(),
      retryCount: 0,
      conversationId
    };
    
    // 检查队列是否已满
    if (this.queue.length >= this.config.maxQueueSize) {
      // 队列已满，删除最旧的消息
      this.queue.shift();
      this.emit('overflow', { dropped: 1 });
    }
    
    // 添加到队列
    this.queue.push(queuedMessage);
    
    // 触发事件
    this.emit('enqueue', queuedMessage);
    
    // 持久化队列
    this.persistQueue();
    
    return queuedMessage;
  }
  
  /**
   * 从队列中移除消息
   * @param messageId 消息ID
   * @returns 是否成功移除
   */
  public dequeue(messageId: string): boolean {
    const initialLength = this.queue.length;
    this.queue = this.queue.filter(item => item.id !== messageId);
    
    const removed = initialLength > this.queue.length;
    
    if (removed) {
      // 触发事件
      this.emit('dequeue', { messageId });
      
      // 持久化队列
      this.persistQueue();
    }
    
    return removed;
  }
  
  /**
   * 获取指定会话的所有消息
   * @param conversationId 会话ID
   * @returns 队列中的消息
   */
  public getMessagesByConversation(conversationId: string): QueuedMessage[] {
    return this.queue.filter(item => item.conversationId === conversationId);
  }
  
  /**
   * 移除指定会话的所有消息
   * @param conversationId 会话ID
   * @returns 移除的消息数量
   */
  public removeConversationMessages(conversationId: string): number {
    const initialLength = this.queue.length;
    this.queue = this.queue.filter(item => item.conversationId !== conversationId);
    
    const removedCount = initialLength - this.queue.length;
    
    if (removedCount > 0) {
      // 触发事件
      this.emit('bulkRemove', { 
        conversationId, 
        count: removedCount 
      });
      
      // 持久化队列
      this.persistQueue();
    }
    
    return removedCount;
  }
  
  /**
   * 处理队列中的消息
   * @param processor 消息处理函数
   * @param filter 消息过滤函数
   */
  public async processQueue(
    processor: (message: any) => Promise<boolean>,
    filter?: (queuedMessage: QueuedMessage) => boolean
  ): Promise<void> {
    // 防止并发处理
    if (this.isProcessing) {
      return;
    }
    
    this.isProcessing = true;
    
    try {
      // 创建可处理消息的副本，避免处理过程中的修改
      let messagesToProcess = [...this.queue];
      
      // 应用过滤器
      if (filter) {
        messagesToProcess = messagesToProcess.filter(filter);
      }
      
      // 处理消息
      for (const queuedMessage of messagesToProcess) {
        try {
          // 处理消息，如果成功则从队列中移除
          const success = await processor(queuedMessage.message);
          
          if (success) {
            this.dequeue(queuedMessage.id);
          } else {
            // 处理失败，增加重试计数
            queuedMessage.retryCount++;
            
            // 触发重试事件
            this.emit('retry', {
              messageId: queuedMessage.id,
              retryCount: queuedMessage.retryCount
            });
          }
        } catch (error) {
          // 处理异常，增加重试计数
          queuedMessage.retryCount++;
          
          // 触发错误事件
          this.emit('error', {
            messageId: queuedMessage.id,
            error,
            retryCount: queuedMessage.retryCount
          });
        }
      }
    } finally {
      this.isProcessing = false;
      
      // 持久化队列
      this.persistQueue();
      
      // 触发处理完成事件
      this.emit('processComplete', {
        remainingCount: this.queue.length
      });
    }
  }
  
  /**
   * 清空队列
   */
  public clear(): void {
    const initialLength = this.queue.length;
    this.queue = [];
    
    if (initialLength > 0) {
      // 触发事件
      this.emit('clear', { 
        count: initialLength 
      });
      
      // 持久化队列
      this.persistQueue();
    }
  }
  
  /**
   * 获取队列长度
   */
  public size(): number {
    return this.queue.length;
  }
  
  /**
   * 判断队列是否为空
   */
  public isEmpty(): boolean {
    return this.queue.length === 0;
  }
  
  /**
   * 持久化队列到本地存储
   */
  private persistQueue(): void {
    if (!this.config.persistenceEnabled || typeof window === 'undefined') {
      return;
    }
    
    try {
      localStorage.setItem(
        this.config.storageKey,
        JSON.stringify(this.queue)
      );
    } catch (error) {
      console.error('持久化消息队列失败:', error);
    }
  }
  
  /**
   * 从本地存储加载持久化的消息
   */
  private loadPersistedMessages(): void {
    if (!this.config.persistenceEnabled || typeof window === 'undefined') {
      return;
    }
    
    try {
      const storedData = localStorage.getItem(this.config.storageKey);
      
      if (storedData) {
        const parsedData = JSON.parse(storedData);
        
        if (Array.isArray(parsedData)) {
          this.queue = parsedData;
          
          // 触发事件
          this.emit('loaded', { 
            count: this.queue.length 
          });
        }
      }
    } catch (error) {
      console.error('加载持久化消息队列失败:', error);
    }
  }
} 