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

export type SenderType = 'user' | 'consultant' | 'doctor' | 'ai' | 'system' | 'customer' | 'operator' | 'admin';

// 消息发送状态
export type MessageStatus = 'pending' | 'sent' | 'failed';

// 文件信息接口
export interface FileInfo {
  file_url: string;
  file_name: string;
  file_size: number;
  file_type: string; // image, document, audio, video, archive
  mime_type: string;
  object_name?: string;
}

export interface Message {
  id: string;
  conversationId: string; // 所属会话ID
  content: string;
  type: 'text' | 'image' | 'voice' | 'file';
  sender: {
    id: string;
    type: SenderType;
    name: string;
    avatar: string;
  };
  timestamp: string;
  isRead?: boolean;
  isImportant?: boolean;
  isSystemMessage?: boolean;
  // 文件消息相关
  file_info?: FileInfo; // 文件消息的文件信息
  // 新增字段：消息发送状态相关
  status?: MessageStatus; // 消息状态：pending | sent | failed
  localId?: string; // 本地临时ID，用于发送前的消息标识
  error?: string; // 发送失败时的错误信息
  canRetry?: boolean; // 是否可以重试
  canDelete?: boolean; // 是否可以删除
  canRecall?: boolean; // 是否可以撤销（1分钟内）
  createdAt?: string; // 本地创建时间，用于判断撤销时间
}

export interface Conversation {
  id: string;
  title?: string;
  user: User;
  lastMessage?: Message;
  unreadCount: number;
  updatedAt: string;
  status?: 'active' | 'inactive' | 'archived';
  consultationType?: string;
  summary?: string;
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
} 