/**
 * WebSocket连接状态枚举
 */
export enum ConnectionStatus {
  DISCONNECTED = 'DISCONNECTED', // 未连接
  CONNECTING = 'CONNECTING',     // 连接中
  CONNECTED = 'CONNECTED',       // 已连接
  ERROR = 'ERROR'                // 连接错误
}

/**
 * WebSocket消息类型
 */
export enum MessageType {
  TEXT = 'text',           // 文本消息
  IMAGE = 'image',         // 图片消息
  VOICE = 'voice',         // 语音消息
  SYSTEM = 'system',       // 系统消息
  CONNECT = 'connect',     // 连接消息
  HEARTBEAT = 'heartbeat', // 心跳消息
  COMMAND = 'command'      // 命令消息
}

/**
 * 发送者类型
 */
export enum SenderType {
  USER = 'user',           // 普通用户
  CUSTOMER = 'customer',   // 顾客
  CONSULTANT = 'consultant', // 顾问
  DOCTOR = 'doctor',       // 医生
  AI = 'ai',               // AI助手
  SYSTEM = 'system'        // 系统
}

/**
 * 消息数据接口
 */
export interface MessageData {
  id: string;                // 消息ID
  conversation_id: string;   // 会话ID
  content: any;              // 消息内容
  type: MessageType;         // 消息类型
  sender: {
    id: string;              // 发送者ID
    type: SenderType;        // 发送者类型
    name?: string;           // 发送者名称
    avatar?: string;         // 发送者头像
  };
  timestamp: string;         // 消息时间戳
  is_important?: boolean;    // 是否标记为重要
  isSystemMessage?: boolean; // 是否为系统消息
  metadata?: Record<string, any>; // 额外元数据
}

/**
 * WebSocket事件处理器接口
 */
export interface WebSocketEventHandler {
  (data: any): void;
}

/**
 * WebSocket配置接口
 */
export interface WebSocketConfig {
  url: string;                // WebSocket服务URL
  reconnectAttempts?: number; // 最大重连尝试次数
  reconnectInterval?: number; // 重连间隔(毫秒)
  heartbeatInterval?: number; // 心跳间隔(毫秒)
  connectionTimeout?: number; // 连接超时(毫秒)
  debug?: boolean;            // 是否启用调试模式
}

/**
 * 消息处理器接口
 */
export interface MessageHandler {
  canHandle(message: MessageData): boolean;  // 判断是否能处理该消息
  handle(message: MessageData): void;        // 处理消息
}

/**
 * 连接参数接口
 */
export interface ConnectionParams {
  userId?: string;            // 用户ID
  conversationId?: string;    // 会话ID
  token?: string;             // 认证令牌
  userType?: SenderType;      // 用户类型
  [key: string]: any;         // 其他参数
} 