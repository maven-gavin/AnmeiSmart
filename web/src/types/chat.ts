import type { TransferMethod } from './smart-brain-app'

export interface User {
  id: string;
  name: string;
  avatar: string;
  tags: string[];
}

export interface Customer {
  id: string;
  name: string;
  avatar: string;
  isOnline: boolean;
  lastMessage?: string;
  lastMessageTime?: string;
  unreadCount: number;
  lifeCycleStage?: string;
}

// 统一的发送者类型：用户 / AI 助手 / 系统
export type SenderType = 'user' | 'ai' | 'system';

// 消息发送状态
export type MessageStatus = 'pending' | 'sent' | 'failed';

// 文件信息接口
export interface FileInfo {
  file_id: string; // 文件ID（必需）
  file_name: string;
  file_size: number;
  file_type: string; // image, document, audio, video, archive
  mime_type: string;
  url?: string; // 派生字段，便于前端直接使用
}

// 新的媒体信息接口（统一消息模型）
export interface MediaInfo {
  file_id: string; // 文件ID（必需）
  name: string; // 媒体文件的原始文件名
  mime_type: string; // 媒体文件的MIME类型（如：image/jpeg, audio/mp3, video/mp4等）
  size_bytes: number; // 媒体文件的大小（字节）
  url?: string; // 可选：派生/本地预览字段（如 blob/data/http）。业务侧仍以 file_id 为准
  metadata?: { // 媒体文件的元数据信息
    width?: number; // 图片/视频的宽度（像素）
    height?: number; // 图片/视频的高度（像素）
    duration_seconds?: number; // 音频/视频的时长（秒）
    [key: string]: unknown; // 其他扩展的元数据字段
  };
}

// 文本消息内容结构
export interface TextMessageContent {
  text: string;
}

// 媒体消息内容结构
export interface MediaMessageContent {
  text?: string; // 可选的附带文字
  media_info: MediaInfo;
}

// 系统事件内容结构
export interface SystemEventContent {
  system_event_type: string; // 如："user_joined", "user_left", "takeover", "release"
  status?: string; // 事件状态
  participants?: string[]; // 参与者
  duration_seconds?: number; // 持续时间（如通话）
  call_id?: string; // 通话ID
  [key: string]: unknown; // 其他事件相关数据
}

// 通用卡片组件数据
export interface CardComponent {
  type: 'button' | 'text' | 'image' | 'divider';
  content?: unknown;
  action?: {
    type: 'cancel' | 'custom';
    data?: unknown;
  };
}

// 结构化消息内容（卡片式消息）
export interface StructuredMessageContent {
  card_type: 'service_recommendation' | 'consultation_summary' | 'custom';
  title: string;
  subtitle?: string;
  data: Record<string, unknown>; // 根据card_type确定具体数据结构
  components?: CardComponent[]; // 可选的交互组件
  actions?: {
    primary?: { text: string; action: string; data?: unknown };
    secondary?: { text: string; action: string; data?: unknown };
  };
}

// 统一的消息内容类型
export type MessageContent = 
  | TextMessageContent 
  | MediaMessageContent 
  | SystemEventContent 
  | StructuredMessageContent;

export interface Message {
  id: string;
  conversationId: string;
  
  // 统一的内容格式 - 四种主要类型
  content: MessageContent;
  type: 'text' | 'media' | 'system' | 'structured';
  
  sender: {
    id: string;
    type: SenderType;
    name: string;
    avatar: string;
  };
  timestamp: string;
  is_read?: boolean;
  is_important?: boolean;
  
  // 新功能字段
  reply_to_message_id?: string; // 回复的消息ID
  reactions?: { [emoji: string]: string[] }; // 反应数据 {"👍": ["user_id1", "user_id2"]}
  extra_metadata?: { [key: string]: unknown }; // 额外元数据
  
  // 数字人半接管确认机制
  requires_confirmation?: boolean; // 是否需要确认（半接管模式）
  is_confirmed?: boolean; // 是否已确认
  confirmed_by?: string; // 确认人ID
  confirmed_at?: string; // 确认时间
  
  // 消息发送状态相关
  status?: MessageStatus;
  localId?: string; // 本地临时ID，用于发送前的消息标识
  error?: string; // 发送失败时的错误信息
  canRetry?: boolean;
  canDelete?: boolean;
  canRecall?: boolean;
  createdAt?: string;
}

// 便利接口：用于创建不同类型的消息
export interface CreateTextMessageData {
  text: string;
  is_important?: boolean;
  reply_to_message_id?: string;
}

export interface CreateMediaMessageData {
  media_file_id: string; // 文件ID（必填）
  media_name: string;
  mime_type: string;
  size_bytes: number;
  text?: string;
  metadata?: { [key: string]: unknown };
  is_important?: boolean;
  reply_to_message_id?: string;
  upload_method?: string;
}

export interface CreateSystemEventData {
  event_type: string;
  status?: string;
  event_data?: { [key: string]: unknown };
}

export interface CreateStructuredMessageData {
  card_type: string;
  title: string;
  subtitle?: string;
  data: Record<string, unknown>;
  components?: CardComponent[];
  actions?: {
    primary?: { text: string; action: string; data?: unknown };
    secondary?: { text: string; action: string; data?: unknown };
  };
}

export interface Conversation {
  id: string;
  title: string;
  chat_mode: 'single' | 'group';  // 重构：type改为chat_mode
  tag: 'chat' | 'consultation';
  owner_id: string;
  owner?: User;
  first_participant_id?: string;  // 新增：第一个参与者ID
  first_participant?: User;       // 新增：第一个参与者信息
  lastMessage?: Message;
  unreadCount: number;
  messageCount: number;
  lastMessageAt?: string;
  updatedAt: string;
  createdAt: string;
  isActive: boolean;
  isArchived: boolean;
  is_pinned?: boolean;            // 新增：是否置顶
  pinned_at?: string;             // 新增：置顶时间
  extra_metadata?: { [key: string]: unknown };
}

export interface CustomerProfile {
  id: string;
  basicInfo: {
    name: string;
    age: number;
    gender: 'male' | 'female';
    phone: string;
  };
  riskNotes: {
    type: string;
    description: string;
    level: 'low' | 'medium' | 'high';
  }[];
}

export interface ConsultationHistoryItem {
  id: string;
  date: string;
  type: string;
  description: string;
  satisfaction_rating?: number;
  duration_minutes?: number;
  has_summary?: boolean;
}

// 消息工具函数类型
export interface MessageUtils {
  // 获取消息的文本内容
  getTextContent(message: Message): string | null;
  
  // 获取消息的媒体信息
  getMediaInfo(message: Message): MediaInfo | null;
  
  // 判断是否为特定类型的消息
  isTextMessage(message: Message): boolean;
  isMediaMessage(message: Message): boolean;
  isSystemMessage(message: Message): boolean;
  
  // 兼容性检查
  isLegacyMessage(message: Message): boolean;
} 


// -----------------------------下面是SmartBrain系统的Chat相关类的定义-----------------------------
export type AnnotationReply = {
  id: string
  task_id: string
  answer: string
  conversation_id: string
  annotation_id: string
  annotation_author_name: string
}

export type MessageEnd = {
  id: string
  metadata: Metadata
  files?: FileResponse[]
}

export type Metadata = {
  retriever_resources?: CitationItem[]
  annotation_reply: {
    id: string
    account: {
      id: string
      name: string
    }
  }
}

export type CitationItem = {
  content: string
  data_source_type: string
  dataset_name: string
  dataset_id: string
  document_id: string
  document_name: string
  hit_count: number
  index_node_hash: string
  segment_id: string
  segment_position: number
  score: number
  word_count: number
}

export type FileResponse = {
  related_id: string
  extension: string
  filename: string
  size: number
  mime_type: string
  transfer_method: TransferMethod
  type: string
  url: string
  upload_file_id: string
  remote_url: string
}
export type MessageReplace = {
  id: string
  task_id: string
  answer: string
  conversation_id: string
}
export type ThoughtItem = {
  id: string
  tool: string // plugin or dataset. May has multi.
  thought: string
  tool_input: string
  tool_labels?: { [key: string]: TypeWithI18N }
  message_id: string
  conversation_id: string
  observation: string
  position: number
  files?: string[]
  message_files?: FileEntity[]
}
export type TypeWithI18N<T = string> = {
  en_US: T
  zh_Hans: T
  [key: string]: T
}

export type FileEntity = {
  id: string
  name: string
  size: number
  type: string
  progress: number
  transferMethod: TransferMethod
  supportFileType: string
  originalFile?: File
  uploadedId?: string
  base64Url?: string
  url?: string
  isRemote?: boolean
}

// --------------------------------------------------------