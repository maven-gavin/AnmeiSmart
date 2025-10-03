/**
 * Agent 对话相关类型定义
 */

// 消息文件
export interface MessageFile {
  id: string;
  type: 'image' | 'file';
  url: string;
  name?: string;
  size?: number;
}

// Agent 思考过程
export interface AgentThought {
  id: string;
  thought: string;               // 思考内容
  tool?: string;                 // 使用的工具
  toolInput?: any;               // 工具输入
  toolOutput?: any;              // 工具输出
  messageFiles?: MessageFile[];
  observation?: string;          // 观察结果
  position?: number;             // 思考步骤位置
}

// 消息反馈类型
export type FeedbackRating = 'like' | 'dislike' | null;

export interface MessageFeedback {
  rating: FeedbackRating;
  submittedAt?: string;
}

// 消息类型
export interface AgentMessage {
  id: string;
  conversationId: string;
  content: string;
  isAnswer: boolean;              // true=AI回复, false=用户消息
  timestamp: string;
  
  // Agent 特有字段
  agentThoughts?: AgentThought[]; // 思考过程
  files?: MessageFile[];          // 附带文件
  isError?: boolean;              // 是否错误消息
  isStreaming?: boolean;          // 是否正在流式输出
  
  // 新增：反馈和建议
  feedback?: MessageFeedback;     // 消息反馈
  suggestedQuestions?: string[];  // 建议问题（仅 AI 消息）
}

// 会话
export interface AgentConversation {
  id: string;
  agentConfigId: string;         // 关联的 Agent 配置
  title: string;
  createdAt: string;
  updatedAt: string;
  messageCount: number;
  lastMessage?: string;
}

// SSE 事件类型
export type SSEEventType = 
  | 'message'           // 消息内容
  | 'agent_message'     // Agent 消息
  | 'agent_thought'     // Agent 思考
  | 'message_file'      // 消息文件
  | 'message_end'       // 消息结束
  | 'message_replace'   // 消息替换
  | 'error';            // 错误

// SSE 回调接口
export interface SSECallbacks {
  onData: (text: string, isFirst: boolean, meta: {
    conversationId?: string;
    messageId?: string;
    taskId?: string;
    errorMessage?: string;
    errorCode?: string;
  }) => void;
  onThought?: (thought: AgentThought) => void;
  onFile?: (file: MessageFile) => void;
  onMessageEnd?: (data: any) => void;
  onMessageReplace?: (data: any) => void;
  onCompleted: (hasError?: boolean) => void;
  onError?: (error: string) => void;
  getAbortController?: (controller: AbortController) => void;
}

// API 响应包装
export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
}

