/**
 * Agent 对话服务
 * 提供与后端 Agent API 的通信接口
 */

import { apiClient, ssePost } from './apiClient';
import type { 
  AgentMessage, 
  AgentConversation, 
  SSECallbacks
} from '@/types/agent-chat';

/**
 * 发送 Agent 消息（流式响应）
 */
export const sendAgentMessage = async (
  agentConfigId: string,
  conversationId: string | null,
  message: string,
  callbacks: SSECallbacks,
  inputs?: Record<string, any>
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
  const response = await apiClient.get<AgentConversation[]>(
    `/agent/${agentConfigId}/conversations`
  );
  return response.data;
};

/**
 * 获取会话消息历史
 */
export const getAgentMessages = async (
  conversationId: string,
  limit: number = 50
): Promise<AgentMessage[]> => {
  const response = await apiClient.get<any[]>(
    `/agent/conversations/${conversationId}/messages`,
    { params: { limit } }
  );
  
  // 转换后端字段名到前端字段名
  return response.data.map(msg => ({
    id: msg.id,
    conversationId: msg.conversation_id,
    content: msg.content,
    isAnswer: msg.is_answer,  // 转换 is_answer -> isAnswer
    timestamp: msg.timestamp,
    agentThoughts: msg.agent_thoughts,
    files: msg.files,
    isError: msg.is_error,
    feedback: msg.feedback
  }));
};

/**
 * 创建新会话
 */
export const createAgentConversation = async (
  agentConfigId: string,
  title?: string
): Promise<AgentConversation> => {
  const response = await apiClient.post<AgentConversation>(
    `/agent/${agentConfigId}/conversations`,
    { body: { title } }
  );
  return response.data;
};

/**
 * 删除会话
 */
export const deleteAgentConversation = async (
  conversationId: string
): Promise<void> => {
  await apiClient.delete(`/agent/conversations/${conversationId}`);
};

/**
 * 重命名会话
 */
export const renameAgentConversation = async (
  conversationId: string,
  title: string
): Promise<void> => {
  await apiClient.put(
    `/agent/conversations/${conversationId}`,
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
): Promise<any> => {
  const response = await apiClient.get(
    `/agent/${agentConfigId}/parameters`
  );
  return response.data;
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

