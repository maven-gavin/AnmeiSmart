/**
 * Agent 对话管理 Hook
 * 管理聊天状态、消息发送、会话切换等核心逻辑
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import { useGetState } from 'ahooks';
import { produce } from 'immer';
import type { AgentConfig } from '@/service/agentConfigService';
import type { AgentMessage, AgentConversation, AgentThought } from '@/types/agent-chat';
import agentChatService from '@/service/agentChatService';
import { toast } from 'react-hot-toast';

export interface UseAgentChatOptions {
  agentConfig: AgentConfig;
  onError?: (error: string) => void;
}

export const useAgentChat = ({ agentConfig, onError }: UseAgentChatOptions) => {
  // 状态管理
  const [messages, setMessages, getMessages] = useGetState<AgentMessage[]>([]);
  const [conversations, setConversations] = useState<AgentConversation[]>([]);
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
  const [isResponding, setIsResponding] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  
  const abortControllerRef = useRef<AbortController | null>(null);

  // 加载会话列表
  const loadConversations = useCallback(async () => {
    try {
      const list = await agentChatService.getAgentConversations(agentConfig.id);
      setConversations(list);
    } catch (error) {
      console.error('加载会话列表失败:', error);
      toast.error('加载会话列表失败');
    }
  }, [agentConfig.id]);

  // 加载消息历史
  const loadMessages = useCallback(async (conversationId: string) => {
    if (!conversationId) return;
    
    setIsLoading(true);
    try {
      const history = await agentChatService.getAgentMessages(conversationId);
      setMessages(history);
    } catch (error) {
      console.error('加载消息历史失败:', error);
      toast.error('加载消息历史失败');
    } finally {
      setIsLoading(false);
    }
  }, [setMessages]);

  // 发送消息
  const sendMessage = useCallback(async (text: string) => {
    if (!text.trim() || isResponding) return;

    const questionId = `question-${Date.now()}`;
    const userMessage: AgentMessage = {
      id: questionId,
      conversationId: currentConversationId || '',
      content: text,
      isAnswer: false,
      timestamp: new Date().toISOString(),
    };

    // 添加用户消息
    setMessages([...getMessages(), userMessage]);

    // 创建占位 AI 消息
    const placeholderAnswerId = `answer-placeholder-${Date.now()}`;
    const placeholderMessage: AgentMessage = {
      id: placeholderAnswerId,
      conversationId: currentConversationId || '',
      content: '',
      isAnswer: true,
      timestamp: new Date().toISOString(),
      isStreaming: true,
    };
    setMessages([...getMessages(), userMessage, placeholderMessage]);

    setIsResponding(true);

    // AI 响应消息
    const aiMessage: AgentMessage = {
      id: '',
      conversationId: currentConversationId || '',
      content: '',
      isAnswer: true,
      timestamp: new Date().toISOString(),
      agentThoughts: [],
    };

    try {
      await agentChatService.sendAgentMessage(
        agentConfig.id,
        currentConversationId,
        text,
        {
          getAbortController: (controller) => {
            abortControllerRef.current = controller;
          },
          onData: (chunk, isFirst, meta) => {
            // 更新消息 ID
            if (meta.messageId && !aiMessage.id) {
              aiMessage.id = meta.messageId;
            }
            if (meta.conversationId && !currentConversationId) {
              setCurrentConversationId(meta.conversationId);
              aiMessage.conversationId = meta.conversationId;
            }

            // 追加内容
            aiMessage.content += chunk;

            // 更新消息列表
            setMessages(
              produce(getMessages(), (draft) => {
                const idx = draft.findIndex(m => m.id === placeholderAnswerId);
                if (idx !== -1) {
                  draft[idx] = { ...aiMessage, isStreaming: true };
                }
              })
            );
          },
          onThought: (thought) => {
            if (!aiMessage.agentThoughts) {
              aiMessage.agentThoughts = [];
            }
            
            // 查找或添加思考过程
            const existingIdx = aiMessage.agentThoughts.findIndex(t => t.id === thought.id);
            if (existingIdx >= 0) {
              aiMessage.agentThoughts[existingIdx] = thought;
            } else {
              aiMessage.agentThoughts.push(thought);
            }

            // 更新消息列表
            setMessages(
              produce(getMessages(), (draft) => {
                const idx = draft.findIndex(m => m.id === placeholderAnswerId);
                if (idx !== -1) {
                  draft[idx] = { ...aiMessage, isStreaming: true };
                }
              })
            );
          },
          onFile: (file) => {
            if (!aiMessage.files) {
              aiMessage.files = [];
            }
            aiMessage.files.push(file);
          },
          onCompleted: (hasError) => {
            setIsResponding(false);
            
            // 标记流式结束
            setMessages(
              produce(getMessages(), (draft) => {
                const idx = draft.findIndex(m => m.id === placeholderAnswerId || m.id === aiMessage.id);
                if (idx !== -1) {
                  draft[idx] = { ...aiMessage, isStreaming: false, isError: hasError };
                }
              })
            );

            // 刷新会话列表
            if (!hasError) {
              loadConversations();
            }
          },
          onError: (error) => {
            setIsResponding(false);
            toast.error(error || '发送消息失败');
            onError?.(error);

            // 移除占位消息
            setMessages(getMessages().filter(m => m.id !== placeholderAnswerId));
          },
        }
      );
    } catch (error) {
      setIsResponding(false);
      console.error('发送消息失败:', error);
      toast.error('发送消息失败');
      
      // 移除占位消息
      setMessages(getMessages().filter(m => m.id !== placeholderAnswerId));
    }
  }, [
    agentConfig.id,
    currentConversationId,
    isResponding,
    getMessages,
    setMessages,
    loadConversations,
    onError,
  ]);

  // 切换会话
  const switchConversation = useCallback((conversationId: string | null) => {
    setCurrentConversationId(conversationId);
    if (conversationId) {
      loadMessages(conversationId);
    } else {
      setMessages([]);
    }
  }, [loadMessages, setMessages]);

  // 创建新会话
  const createNewConversation = useCallback(async () => {
    try {
      const newConv = await agentChatService.createAgentConversation(agentConfig.id);
      setConversations([newConv, ...conversations]);
      switchConversation(newConv.id);
      toast.success('创建新会话成功');
    } catch (error) {
      console.error('创建会话失败:', error);
      toast.error('创建会话失败');
    }
  }, [agentConfig.id, conversations, switchConversation]);

  // 删除会话
  const deleteConversation = useCallback(async (conversationId: string) => {
    try {
      await agentChatService.deleteAgentConversation(conversationId);
      setConversations(conversations.filter(c => c.id !== conversationId));
      
      if (currentConversationId === conversationId) {
        setCurrentConversationId(null);
        setMessages([]);
      }
      
      toast.success('删除会话成功');
    } catch (error) {
      console.error('删除会话失败:', error);
      toast.error('删除会话失败');
    }
  }, [conversations, currentConversationId, setMessages]);

  // 停止响应
  const stopResponding = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setIsResponding(false);
    }
  }, []);

  // 初始化
  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  return {
    // 状态
    messages,
    conversations,
    currentConversationId,
    isResponding,
    isLoading,
    
    // 方法
    sendMessage,
    loadMessages,
    loadConversations,
    switchConversation,
    createNewConversation,
    deleteConversation,
    stopResponding,
  };
};

