import { MessageData, MessageType } from '../types';

/**
 * WebSocket消息序列化/反序列化
 * 负责对消息进行编码和解码，支持JSON和二进制格式
 */
export class WebSocketSerializer {
  private validateMessages: boolean = true;
  private useBinaryFormat: boolean = false;
  private textEncoder: TextEncoder;
  private textDecoder: TextDecoder;

  /**
   * 构造函数
   * @param options 序列化选项
   */
  constructor(options?: {
    validateMessages?: boolean;
    useBinaryFormat?: boolean;
  }) {
    if (options) {
      if (typeof options.validateMessages === 'boolean') {
        this.validateMessages = options.validateMessages;
      }
      
      if (typeof options.useBinaryFormat === 'boolean') {
        this.useBinaryFormat = options.useBinaryFormat;
      }
    }
    
    // 初始化编码器和解码器
    this.textEncoder = new TextEncoder();
    this.textDecoder = new TextDecoder('utf-8');
  }

  /**
   * 序列化消息
   * @param message 要序列化的消息对象
   * @returns 序列化后的数据，字符串或二进制
   */
  public serialize(message: MessageData | Record<string, any>): string | ArrayBuffer {
    // 如果启用了验证，先验证消息格式
    if (this.validateMessages) {
      this.validateMessage(message);
    }
    
    // 序列化为JSON字符串
    const jsonString = JSON.stringify(message);
    
    // 如果使用二进制格式，则转换为ArrayBuffer
    if (this.useBinaryFormat) {
      // 使用serializeToBinary方法确保返回正确的ArrayBuffer类型
      return this.serializeToBinary(message);
    }
    
    // 否则返回JSON字符串
    return jsonString;
  }

  /**
   * 反序列化消息
   * @param data 要反序列化的数据
   * @returns 反序列化后的消息对象
   */
  public deserialize(data: string | ArrayBuffer | Blob): MessageData | Record<string, any> {
    try {
      let jsonString: string;
      
      // 根据数据类型进行处理
      if (typeof data === 'string') {
        jsonString = data;
      } else if (data instanceof ArrayBuffer) {
        jsonString = this.textDecoder.decode(data);
      } else if (data instanceof Blob) {
        // 对于Blob，需要异步处理，这里返回一个Promise
        throw new Error('不支持直接反序列化Blob，请使用deserializeAsync');
      } else {
        throw new Error('不支持的数据类型');
      }
      
      // 解析JSON
      const message = JSON.parse(jsonString);
      
      // 如果启用了验证，先验证消息格式
      if (this.validateMessages) {
        this.validateMessage(message);
      }
      
      return message;
    } catch (error) {
      throw new Error(`反序列化失败: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  /**
   * 异步反序列化消息
   * @param data 要反序列化的数据
   * @returns Promise，解析为反序列化后的消息对象
   */
  public async deserializeAsync(data: string | ArrayBuffer | Blob): Promise<MessageData | Record<string, any>> {
    try {
      let jsonString: string;
      
      // 根据数据类型进行处理
      if (typeof data === 'string') {
        jsonString = data;
      } else if (data instanceof ArrayBuffer) {
        jsonString = this.textDecoder.decode(data);
      } else if (data instanceof Blob) {
        // 对于Blob，需要读取为文本
        jsonString = await this.readBlobAsText(data);
      } else {
        throw new Error('不支持的数据类型');
      }
      
      // 解析JSON
      const message = JSON.parse(jsonString);
      
      // 如果启用了验证，先验证消息格式
      if (this.validateMessages) {
        this.validateMessage(message);
      }
      
      return message;
    } catch (error) {
      throw new Error(`反序列化失败: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  /**
   * 读取Blob为文本
   * @param blob Blob对象
   * @returns Promise，解析为文本内容
   */
  private readBlobAsText(blob: Blob): Promise<string> {
    return new Promise<string>((resolve, reject) => {
      const reader = new FileReader();
      
      reader.onload = () => {
        if (typeof reader.result === 'string') {
          resolve(reader.result);
        } else {
          reject(new Error('读取Blob失败：结果不是字符串'));
        }
      };
      
      reader.onerror = () => {
        reject(new Error('读取Blob失败'));
      };
      
      reader.readAsText(blob);
    });
  }

  /**
   * 验证消息格式
   * @param message 要验证的消息对象
   * @throws 如果消息格式无效则抛出错误
   */
  private validateMessage(message: any): void {
    // 基本检查
    if (!message || typeof message !== 'object') {
      throw new Error('无效的消息：不是对象');
    }
    
    // 检查是否为完整的MessageData
    if ('id' in message && 'conversation_id' in message && 'type' in message && 'sender' in message) {
      // 验证MessageData格式
      if (!message.id || typeof message.id !== 'string') {
        throw new Error('无效的消息：缺少有效的id');
      }
      
      if (!message.conversation_id || typeof message.conversation_id !== 'string') {
        throw new Error('无效的消息：缺少有效的conversation_id');
      }
      
      if (!message.type || !Object.values(MessageType).includes(message.type)) {
        throw new Error(`无效的消息：类型 ${message.type} 不受支持`);
      }
      
      if (!message.sender || typeof message.sender !== 'object' || !message.sender.id) {
        throw new Error('无效的消息：缺少有效的sender信息');
      }
      
      if (!message.timestamp) {
        throw new Error('无效的消息：缺少timestamp');
      }
    }
    
    // 允许基本的命令消息通过（不完全符合MessageData格式）
    if (message.type === 'heartbeat' || message.type === 'command') {
      return;
    }
  }

  /**
   * 设置是否验证消息
   * @param validate 是否验证消息
   */
  public setValidateMessages(validate: boolean): void {
    this.validateMessages = validate;
  }

  /**
   * 设置是否使用二进制格式
   * @param useBinary 是否使用二进制格式
   */
  public setUseBinaryFormat(useBinary: boolean): void {
    this.useBinaryFormat = useBinary;
  }

  /**
   * 获取当前配置
   */
  public getConfig(): {
    validateMessages: boolean;
    useBinaryFormat: boolean;
  } {
    return {
      validateMessages: this.validateMessages,
      useBinaryFormat: this.useBinaryFormat
    };
  }

  /**
   * 将JavaScript对象序列化为二进制数据
   * @param data 要序列化的数据
   * @returns ArrayBuffer
   */
  serializeToBinary(data: any): ArrayBuffer {
    try {
      const jsonString = JSON.stringify(data);
      // 将纯文本转换为二进制，并确保返回的是ArrayBuffer类型
      const buffer = this.textEncoder.encode(jsonString).buffer;
      return buffer as ArrayBuffer;
    } catch (error) {
      console.error('序列化为二进制失败:', error);
      // 返回空的ArrayBuffer
      return new ArrayBuffer(0);
    }
  }
} 