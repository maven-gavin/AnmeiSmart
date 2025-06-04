/**
 * 聊天状态管理模块
 * 统一管理聊天相关的本地状态和缓存
 */

import type { 
  Message, 
  Conversation, 
  ChatStateData 
} from './types';
import { CACHE_TIME } from './types';

/**
 * 聊天状态管理器
 * 使用单例模式管理聊天应用的全局状态
 */
export class ChatStateManager {
  private static instance: ChatStateManager;
  
  private state: ChatStateData = {
    chatMessages: {},
    conversations: [],
    consultantTakeover: {},
    messageQueue: [],
    lastConnectedConversationId: null,
    connectionDebounceTimer: null,
    messageCallbacks: {},
    processedMessageIds: new Set<string>(),
    isRequestingMessages: {},
    lastMessagesRequestTime: {},
    isRequestingConversations: false,
    lastConversationsRequestTime: 0,
  };
  
  private constructor() {}
  
  public static getInstance(): ChatStateManager {
    if (!ChatStateManager.instance) {
      ChatStateManager.instance = new ChatStateManager();
    }
    return ChatStateManager.instance;
  }
  
  // ===== 消息管理 =====
  
  public getChatMessages(conversationId: string): Message[] {
    return this.state.chatMessages[conversationId] || [];
  }
  
  public setChatMessages(conversationId: string, messages: Message[]): void {
    this.state.chatMessages[conversationId] = messages;
  }
  
  public addMessage(conversationId: string, message: Message): void {
    if (!this.state.chatMessages[conversationId]) {
      this.state.chatMessages[conversationId] = [];
    }
    
    const messages = this.state.chatMessages[conversationId];
    if (!messages.some(m => m.id === message.id)) {
      messages.push(message);
      this.updateConversationLastMessage(conversationId, message);
    }
  }
  
  public updateConversationLastMessage(conversationId: string, message: Message): void {
    const conversationIndex = this.state.conversations.findIndex(conv => conv.id === conversationId);
    if (conversationIndex >= 0) {
      this.state.conversations[conversationIndex] = {
        ...this.state.conversations[conversationIndex],
        lastMessage: message,
        updatedAt: message.timestamp,
      };
    }
  }
  
  // ===== 会话管理 =====
  
  public getConversations(): Conversation[] {
    return this.state.conversations;
  }
  
  public setConversations(conversations: Conversation[]): void {
    this.state.conversations = conversations;
  }
  
  public updateConversationTitle(conversationId: string, title: string): void {
    const conversationIndex = this.state.conversations.findIndex(conv => conv.id === conversationId);
    if (conversationIndex >= 0) {
      this.state.conversations[conversationIndex] = {
        ...this.state.conversations[conversationIndex],
        title: title.trim()
      };
    }
  }
  
  // ===== 顾问接管状态 =====
  
  public isConsultantTakeover(conversationId: string): boolean {
    return !!this.state.consultantTakeover[conversationId];
  }
  
  public setConsultantTakeover(conversationId: string, value: boolean): void {
    this.state.consultantTakeover[conversationId] = value;
  }
  
  // ===== 消息队列管理 =====
  
  public getMessageQueue(): any[] {
    return this.state.messageQueue;
  }
  
  public addToMessageQueue(message: any): void {
    this.state.messageQueue.push(message);
  }
  
  public clearMessageQueue(): void {
    this.state.messageQueue.length = 0;
  }
  
  // ===== WebSocket连接状态 =====
  
  public getLastConnectedConversationId(): string | null {
    return this.state.lastConnectedConversationId;
  }
  
  public setLastConnectedConversationId(id: string | null): void {
    this.state.lastConnectedConversationId = id;
  }
  
  public getConnectionDebounceTimer(): NodeJS.Timeout | null {
    return this.state.connectionDebounceTimer;
  }
  
  public setConnectionDebounceTimer(timer: NodeJS.Timeout | null): void {
    this.state.connectionDebounceTimer = timer;
  }
  
  // ===== 消息回调管理 =====
  
  public addMessageCallback(action: string, callback: (message: any) => void): void {
    if (!this.state.messageCallbacks[action]) {
      this.state.messageCallbacks[action] = [];
    }
    this.state.messageCallbacks[action].push(callback);
  }
  
  public removeMessageCallback(action: string, callback: (message: any) => void): void {
    if (this.state.messageCallbacks[action]) {
      this.state.messageCallbacks[action] = this.state.messageCallbacks[action].filter(cb => cb !== callback);
    }
  }
  
  public getMessageCallbacks(action: string): ((message: any) => void)[] {
    return this.state.messageCallbacks[action] || [];
  }
  
  // ===== 请求状态管理 =====
  
  public setRequestingMessages(conversationId: string, value: boolean): void {
    this.state.isRequestingMessages[conversationId] = value;
  }
  
  public isRequestingMessagesForConversation(conversationId: string): boolean {
    return !!this.state.isRequestingMessages[conversationId];
  }
  
  public updateMessagesRequestTime(conversationId: string): void {
    this.state.lastMessagesRequestTime[conversationId] = Date.now();
  }
  
  public getMessagesRequestTime(conversationId: string): number {
    return this.state.lastMessagesRequestTime[conversationId] || 0;
  }
  
  public isMessagesCacheValid(conversationId: string): boolean {
    const lastRequestTime = this.getMessagesRequestTime(conversationId);
    const now = Date.now();
    return (now - lastRequestTime) < CACHE_TIME.MESSAGES;
  }
  
  public setRequestingConversations(value: boolean): void {
    this.state.isRequestingConversations = value;
  }
  
  public isRequestingConversationsState(): boolean {
    return this.state.isRequestingConversations;
  }
  
  public updateConversationsRequestTime(): void {
    this.state.lastConversationsRequestTime = Date.now();
  }
  
  public getConversationsRequestTime(): number {
    return this.state.lastConversationsRequestTime;
  }
  
  public isConversationsCacheValid(): boolean {
    const lastRequestTime = this.getConversationsRequestTime();
    const now = Date.now();
    return (now - lastRequestTime) < CACHE_TIME.CONVERSATIONS;
  }
  
  // ===== 清理方法 =====
  
  public clear(): void {
    if (this.state.connectionDebounceTimer) {
      clearTimeout(this.state.connectionDebounceTimer);
    }
    
    this.state = {
      chatMessages: {},
      conversations: [],
      consultantTakeover: {},
      messageQueue: [],
      lastConnectedConversationId: null,
      connectionDebounceTimer: null,
      messageCallbacks: {},
      processedMessageIds: new Set<string>(),
      isRequestingMessages: {},
      lastMessagesRequestTime: {},
      isRequestingConversations: false,
      lastConversationsRequestTime: 0,
    };
  }
}

/**
 * 导出状态管理器单例
 */
export const chatState = ChatStateManager.getInstance(); 