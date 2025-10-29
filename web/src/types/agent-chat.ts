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

// 文件上传响应（Dify）
export interface FileUploadResult {
  id: string;           // Dify的upload_file_id
  name: string;         // 文件名
  size: number;         // 文件大小（字节）
  mime_type: string;    // MIME类型
  created_at: string;   // 创建时间
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

// 用户输入表单字段
export interface UserInputFormField {
  variable: string;              // 变量名
  label: string;                 // 显示标签
  type: 'text-input' | 'paragraph' | 'number' | 'select' | 'file' | 'file-list';
  required: boolean;             // 是否必填
  max_length?: number;           // 最大长度
  default?: string | number;     // 默认值
  options?: string[];            // select 类型的选项
  hide?: boolean;                // 是否隐藏
  description?: string;          // 字段描述
  allowed_file_upload_methods?: ('local_file' | 'remote_url')[];  // 文件上传方式
  allowed_file_types?: string[]; // 允许的文件类型
  allowed_file_extensions?: string[];  // 允许的文件扩展名
}

// 应用参数配置
export interface ApplicationParameters {
  opening_statement?: string;              // 开场白
  suggested_questions?: string[];          // 建议问题
  user_input_form?: UserInputFormField[];  // 对话前表单
  speech_to_text?: {
    enabled: boolean;
  };
  file_upload?: {
    enabled: boolean;
    allowed_file_types?: string[];         // 允许的文件类型
    allowed_file_upload_methods?: string[]; // 上传方式
    number_limits?: number;                // 数量限制
  };
  text_to_speech?: {
    enabled: boolean;
    voice?: string;
    language?: string;
  };
  retriever_resource?: {
    enabled: boolean;
  };
  annotation_reply?: {
    enabled: boolean;
  };
  suggested_questions_after_answer?: {
    enabled: boolean;
  };
  [key: string]: any;
}

