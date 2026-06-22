/**
 * Agent 对话服务
 * 提供与后端 Agent API 的通信接口
 */

import { apiClient, ssePost } from './apiClient';
import type { 
  AgentMessage, 
  AgentConversation, 
  AgentThought,
  SSECallbacks
} from '@/types/agent-chat';

interface AgentConversationApiItem {
  id: string;
  agent_config_id?: string;
  agentConfigId?: string;
  title?: string;
  created_at?: string;
  createdAt?: string;
  updated_at?: string;
  updatedAt?: string;
  message_count?: number;
  messageCount?: number;
  last_message?: string;
  lastMessage?: string;
}

interface AgentConversationListResponse {
  data?: AgentConversationApiItem[];
}

interface AgentMessageApiItem {
  id: string;
  conversation_id: string;
  content: string;
  is_answer: boolean;
  timestamp: string;
  agent_thoughts?: unknown;
  files?: unknown;
  is_error?: boolean;
  feedback?: unknown;
}

interface AgentConversationApiResponse {
  id: string;
  agent_config_id?: string;
  agentConfigId?: string;
  title?: string;
  created_at?: string;
  createdAt?: string;
  updated_at?: string;
  updatedAt?: string;
  message_count?: number;
  messageCount?: number;
  last_message?: string;
  lastMessage?: string;
}

/**
 * 发送 Agent 消息（流式响应）
 */
export const sendAgentMessage = async (
  agentConfigId: string,
  conversationId: string | null,
  message: string,
  callbacks: SSECallbacks,
  inputs?: Record<string, unknown>
): Promise<void> => {
  return ssePost(
    `/agent/${agentConfigId}/chat`,
    {
      body: {
        message,
        conversation_id: conversationId,
        inputs: inputs || {},
        response_mode: 'streaming'
      }
    },
    callbacks
  );
};

/**
 * 获取 Agent 会话列表
 */
export const getAgentConversations = async (
  agentConfigId: string
): Promise<AgentConversation[]> => {
  const response = await apiClient.get<AgentConversationApiItem[]>(
    `/agent/${agentConfigId}/conversations`
  );
  
  // 处理可能的响应包装
  const rawData = response.data;
  const data: AgentConversationApiItem[] = Array.isArray(rawData)
    ? rawData
    : (rawData as AgentConversationListResponse).data || [];
  
  // 映射后端字段到前端类型
  return data.map((item) => ({
    id: item.id,
    agentConfigId: item.agent_config_id || item.agentConfigId || agentConfigId,
    title: item.title ?? '',
    createdAt: item.created_at || item.createdAt || '',
    updatedAt: item.updated_at || item.updatedAt || '',
    messageCount: item.message_count || item.messageCount || 0,
    lastMessage: item.last_message || item.lastMessage
  }));
};

/**
 * 获取会话消息历史
 */
export const getAgentMessages = async (
  agentConfigId: string,
  conversationId: string,
  limit: number = 50
): Promise<AgentMessage[]> => {
  const response = await apiClient.get<AgentMessageApiItem[]>(
    `/agent/${agentConfigId}/conversations/${conversationId}/messages`,
    { params: { limit } }
  );
  
  // 转换后端字段名到前端字段名
  return response.data.map(msg => ({
    id: msg.id,
    conversationId: msg.conversation_id,
    content: msg.content,
    isAnswer: msg.is_answer,  // 转换 is_answer -> isAnswer
    timestamp: msg.timestamp,
    agentThoughts: msg.agent_thoughts as AgentThought[] | undefined,
    files: msg.files as AgentMessage['files'],
    isError: msg.is_error,
    feedback: msg.feedback as AgentMessage['feedback'],
    // 历史消息不触发“加载建议问题...”
    shouldLoadSuggestedQuestions: false,
  }));
};

/**
 * 创建新会话
 */
export const createAgentConversation = async (
  agentConfigId: string,
  title?: string
): Promise<AgentConversation> => {
  const response = await apiClient.post<AgentConversationApiResponse>(
    `/agent/${agentConfigId}/conversations`,
    { body: { title } }
  );
  
  const item = response.data;
  
  // 映射后端字段到前端类型
  return {
    id: item.id,
    agentConfigId: item.agent_config_id || item.agentConfigId || agentConfigId,
    title: item.title ?? '',
    createdAt: item.created_at || item.createdAt || '',
    updatedAt: item.updated_at || item.updatedAt || '',
    messageCount: item.message_count || item.messageCount || 0,
    lastMessage: item.last_message || item.lastMessage
  };
};

/**
 * 删除会话
 */
export const deleteAgentConversation = async (
  agentConfigId: string,
  conversationId: string
): Promise<void> => {
  await apiClient.delete(`/agent/${agentConfigId}/conversations/${conversationId}`);
};

/**
 * 重命名会话
 */
export const renameAgentConversation = async (
  agentConfigId: string,
  conversationId: string,
  title: string
): Promise<void> => {
  await apiClient.put(
    `/agent/${agentConfigId}/conversations/${conversationId}`,
    { body: { title } }
  );
};

/**
 * 提交消息反馈
 */
export const submitMessageFeedback = async (
  agentConfigId: string,
  messageId: string,
  rating: 'like' | 'dislike'
): Promise<void> => {
  await apiClient.post(
    `/agent/${agentConfigId}/feedback`,
    { body: { message_id: messageId, rating } }
  );
};

/**
 * 获取建议问题
 */
export const getSuggestedQuestions = async (
  agentConfigId: string,
  messageId: string
): Promise<string[]> => {
  const response = await apiClient.get<{ questions: string[] }>(
    `/agent/${agentConfigId}/messages/${messageId}/suggested`
  );
  return response.data.questions;
};

/**
 * 停止消息生成
 */
export const stopMessageGeneration = async (
  agentConfigId: string,
  taskId: string
): Promise<void> => {
  await apiClient.post(
    `/agent/${agentConfigId}/stop`,
    { body: { task_id: taskId } }
  );
};

/**
 * 获取应用参数
 */
export const getApplicationParameters = async (
  agentConfigId: string
): Promise<Record<string, unknown>> => {
  const response = await apiClient.get<Record<string, unknown>>(
    `/agent/${agentConfigId}/parameters`
  );
  return response.data ?? {};
};

// 导出服务对象
const agentChatService = {
  sendAgentMessage,
  getAgentConversations,
  getAgentMessages,
  createAgentConversation,
  deleteAgentConversation,
  renameAgentConversation,
  submitMessageFeedback,
  getSuggestedQuestions,
  stopMessageGeneration,
  getApplicationParameters,
};

export default agentChatService;

