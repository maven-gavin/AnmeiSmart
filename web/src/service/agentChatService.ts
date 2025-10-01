/**
 * Agent 对话服务
 * 提供与后端 Agent API 的通信接口
 */

import { apiClient, ssePost } from './apiClient';
import type { 
  AgentMessage, 
  AgentConversation, 
  SSECallbacks,
  ApiResponse 
} from '@/types/agent-chat';

/**
 * 发送 Agent 消息（流式响应）
 */
export const sendAgentMessage = async (
  agentConfigId: string,
  conversationId: string | null,
  message: string,
  callbacks: SSECallbacks
): Promise<void> => {
  return ssePost(
    `/agent/${agentConfigId}/chat`,
    {
      body: {
        message,
        conversation_id: conversationId,
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
  const response = await apiClient.get<AgentMessage[]>(
    `/agent/conversations/${conversationId}/messages`,
    { params: { limit } }
  );
  return response.data;
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

// 导出服务对象
const agentChatService = {
  sendAgentMessage,
  getAgentConversations,
  getAgentMessages,
  createAgentConversation,
  deleteAgentConversation,
  renameAgentConversation,
};

export default agentChatService;

