export interface User {
  id: string;
  name: string;
  avatar: string;
  tags: string[];
}

export interface Message {
  id: string;
  content: string;
  type: 'text' | 'image' | 'voice';
  sender: {
    id: string;
    type: 'user' | 'consultant' | 'ai' | 'system';
    name: string;
    avatar: string;
  };
  timestamp: string;
  isImportant?: boolean;
  isSystemMessage?: boolean;
}

export interface Conversation {
  id: string;
  user: User;
  lastMessage: Message;
  unreadCount: number;
  updatedAt: string;
}

export interface CustomerProfile {
  id: string;
  basicInfo: {
    name: string;
    age: number;
    gender: 'male' | 'female';
    phone: string;
  };
  consultationHistory: {
    date: string;
    type: string;
    description: string;
  }[];
  riskNotes: {
    type: string;
    description: string;
    level: 'low' | 'medium' | 'high';
  }[];
} 