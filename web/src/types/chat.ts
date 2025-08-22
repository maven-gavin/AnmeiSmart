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
  tags?: string[];
  priority?: 'low' | 'medium' | 'high';
}

export type SenderType = 'user' | 'consultant' | 'doctor' | 'ai' | 'system' | 'customer' | 'operator' | 'admin' | 'digital_human';

// 消息发送状态
export type MessageStatus = 'pending' | 'sent' | 'failed';

// 文件信息接口（保持向后兼容）
export interface FileInfo {
  file_url: string;
  file_name: string;
  file_size: number;
  file_type: string; // image, document, audio, video, archive
  mime_type: string;
  object_name?: string;
}

// 新的媒体信息接口（统一消息模型）
export interface MediaInfo {
  url: string;
  name: string;
  mime_type: string;
  size_bytes: number;
  metadata?: {
    width?: number;
    height?: number;
    duration_seconds?: number;
    [key: string]: any;
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
  [key: string]: any; // 其他事件相关数据
}

// 预约确认卡片数据结构
export interface AppointmentCardData {
  appointment_id: string;
  service_name: string; // 服务名称：如"面部深层清洁护理"
  consultant_name: string; // 顾问姓名
  consultant_avatar?: string; // 顾问头像
  scheduled_time: string; // 预约时间 ISO string
  duration_minutes: number; // 服务时长（分钟）
  price: number; // 价格
  location: string; // 地点
  status: 'pending' | 'confirmed' | 'cancelled'; // 预约状态
  notes?: string; // 备注
}

// 通用卡片组件数据
export interface CardComponent {
  type: 'button' | 'text' | 'image' | 'divider';
  content?: any;
  action?: {
    type: 'confirm_appointment' | 'reschedule' | 'cancel' | 'custom';
    data?: any;
  };
}

// 结构化消息内容（卡片式消息）
export interface StructuredMessageContent {
  card_type: 'appointment_confirmation' | 'service_recommendation' | 'consultation_summary' | 'custom';
  title: string;
  subtitle?: string;
  data: AppointmentCardData | any; // 根据card_type确定具体数据结构
  components?: CardComponent[]; // 可选的交互组件
  actions?: {
    primary?: { text: string; action: string; data?: any };
    secondary?: { text: string; action: string; data?: any };
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
  extra_metadata?: { [key: string]: any }; // 额外元数据
  
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
  media_url: string;
  media_name: string;
  mime_type: string;
  size_bytes: number;
  text?: string;
  metadata?: { [key: string]: any };
  is_important?: boolean;
  reply_to_message_id?: string;
  upload_method?: string;
}

export interface CreateSystemEventData {
  event_type: string;
  status?: string;
  event_data?: { [key: string]: any };
}

export interface CreateStructuredMessageData {
  card_type: string;
  title: string;
  subtitle?: string;
  data: any;
  components?: CardComponent[];
  actions?: {
    primary?: { text: string; action: string; data?: any };
    secondary?: { text: string; action: string; data?: any };
  };
}

export interface Conversation {
  id: string;
  title: string;
  chat_mode: 'single' | 'group';  // 重构：type改为chat_mode
  tag: 'chat' | 'consultation';   // 重构：新增tag字段区分会话类型
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