/**
 * Agent 对话管理 Hook
 * 管理聊天状态、消息发送、会话切换等核心逻辑
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import { useGetState } from 'ahooks';
import { produce } from 'immer';
import type { AgentConfig } from '@/service/agentConfigService';
import type { AgentMessage, AgentConversation, AgentThought, ApplicationParameters } from '@/types/agent-chat';
import agentChatService, { getApplicationParameters } from '@/service/agentChatService';
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
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);
  const [appConfig, setAppConfig] = useState<ApplicationParameters | null>(null);
  
  const abortControllerRef = useRef<AbortController | null>(null);

  // 检查 agentConfig 是否有效
  const isValidAgent = agentConfig && agentConfig.id && agentConfig.id.trim() !== '';

  // 加载应用配置
  const loadAppConfig = useCallback(async () => {
    if (!isValidAgent) {
      setAppConfig(null);
      return;
    }
    
    try {
      const config = await getApplicationParameters(agentConfig.id);
      setAppConfig(config);
    } catch (error) {
      console.error('获取应用配置失败:', error);
      setAppConfig(null);
    }
  }, [agentConfig.id, isValidAgent]);

  // 加载会话列表
  const loadConversations = useCallback(async () => {
    if (!isValidAgent) return;
    
    try {
      const list = await agentChatService.getAgentConversations(agentConfig.id);
      setConversations(list);
    } catch (error) {
      console.error('加载会话列表失败:', error);
      toast.error('加载会话列表失败');
    }
  }, [agentConfig.id, isValidAgent]);

  // 加载消息历史
  const loadMessages = useCallback(async (conversationId: string) => {
    if (!conversationId || !isValidAgent) return;
    
    setIsLoading(true);
    try {
      const history = await agentChatService.getAgentMessages(agentConfig.id, conversationId);
      setMessages(history);
    } catch (error) {
      console.error('加载消息历史失败:', error);
      toast.error('加载消息历史失败');
    } finally {
      setIsLoading(false);
    }
  }, [agentConfig.id, isValidAgent, setMessages]);

  // 发送消息
  const sendMessage = useCallback(async (text: string, inputs?: Record<string, any>) => {
    if (!text.trim() || isResponding || !isValidAgent) return;

    const questionId = `question-${Date.now()}`;
    const userMessage: AgentMessage = {
      id: questionId,
      conversationId: currentConversationId || '',
      content: text,
      isAnswer: false,
      timestamp: new Date().toISOString(),
    };

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
    
    // 一次性添加用户消息和占位消息，避免重复添加
    setMessages((prev) => [...prev, userMessage, placeholderMessage]);
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

    // 打字机效果：用于处理大块文本的分块显示
    let typewriterTimer: NodeJS.Timeout | null = null;
    let pendingContent = '';
    let displayedLength = 0;
    const TYPEWRITER_CHUNK_SIZE = 10; // 每次显示的字符数
    const TYPEWRITER_DELAY = 20; // 每次显示的延迟（毫秒）

    const flushTypewriter = () => {
      if (typewriterTimer) {
        clearInterval(typewriterTimer);
        typewriterTimer = null;
      }
      
      if (pendingContent.length > displayedLength) {
        // 每次显示一小块
        const chunk = pendingContent.substring(displayedLength, displayedLength + TYPEWRITER_CHUNK_SIZE);
        displayedLength += chunk.length;
        aiMessage.content = pendingContent.substring(0, displayedLength);
        
        // 更新消息列表
        setMessages(
          produce((draft) => {
            const idx = draft.findIndex(m => m.id === placeholderAnswerId || m.id === aiMessage.id);
            if (idx !== -1) {
              draft[idx] = { ...aiMessage, isStreaming: true };
            }
          })
        );
        
        // 如果还有内容，继续显示
        if (displayedLength < pendingContent.length) {
          typewriterTimer = setTimeout(flushTypewriter, TYPEWRITER_DELAY);
        } else {
          // 显示完成
          typewriterTimer = null;
        }
      }
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
              // 更新占位消息的ID
              setMessages(
                produce((draft) => {
                  const idx = draft.findIndex(m => m.id === placeholderAnswerId);
                  if (idx !== -1) {
                    draft[idx].id = aiMessage.id;
                  }
                })
              );
            }
            if (meta.conversationId && !currentConversationId) {
              setCurrentConversationId(meta.conversationId);
              aiMessage.conversationId = meta.conversationId;
            }
            // 保存 taskId 用于停止生成
            if (meta.taskId) {
              setCurrentTaskId(meta.taskId);
            }

            // 更新待显示内容
            pendingContent = aiMessage.content + chunk;
            
            // 如果chunk很大（一次性返回完整答案），使用打字机效果
            if (chunk.length > 100) {
              // 大块文本：使用打字机效果
              // 如果打字机没有运行，启动它
              if (!typewriterTimer) {
                flushTypewriter();
              }
            } else {
              // 小块文本：直接显示（真正的流式输出）
              aiMessage.content = pendingContent;
              displayedLength = pendingContent.length;
              
              // 更新消息列表
              setMessages(
                produce((draft) => {
                  const idx = draft.findIndex(m => m.id === placeholderAnswerId || m.id === aiMessage.id);
                  if (idx !== -1) {
                    draft[idx] = { ...aiMessage, isStreaming: true };
                  }
                })
              );
            }
          },
          onTextChunk: (textChunk) => {
            // 处理 workflow 的 text_chunk 事件（流式文本输出）
            const text = textChunk.data?.text || '';
            if (text) {
              // 追加内容
              aiMessage.content += text;
              
              // 更新消息列表
              setMessages(
                produce(getMessages(), (draft) => {
                  const idx = draft.findIndex(m => m.id === placeholderAnswerId);
                  if (idx !== -1) {
                    draft[idx] = { ...aiMessage, isStreaming: true };
                  }
                })
              );
            }
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
          onMessageEnd: (messageEndData) => {
            // message_end事件表示流式输出结束
            // 如果此时还没有内容，可能需要从其他地方获取
            console.log('[useAgentChat] message_end事件:', messageEndData);
            
            // 检查是否有metadata中包含完整答案
            if (!aiMessage.content && messageEndData?.metadata) {
              // 某些情况下，完整答案可能在metadata中
              const metadata = messageEndData.metadata;
              if (metadata.answer && typeof metadata.answer === 'string') {
                aiMessage.content = metadata.answer;
                setMessages(
                  produce(getMessages(), (draft) => {
                    const idx = draft.findIndex(m => m.id === placeholderAnswerId);
                    if (idx !== -1) {
                      draft[idx] = { ...aiMessage, isStreaming: true };
                    }
                  })
                );
              }
            }
          },
          onWorkflowFinished: (workflowData) => {
            // 处理 workflow_finished 事件，可能包含最终输出
            // 如果还没有收到任何内容，尝试从outputs中提取
            if (!aiMessage.content && workflowData.data?.outputs) {
              // 尝试从outputs中提取文本内容
              const outputs = workflowData.data.outputs;
              if (typeof outputs === 'string') {
                aiMessage.content = outputs;
              } else if (outputs && typeof outputs === 'object') {
                // 尝试找到文本字段
                const textFields = ['text', 'answer', 'output', 'result', 'content'];
                for (const field of textFields) {
                  if (outputs[field] && typeof outputs[field] === 'string') {
                    aiMessage.content = outputs[field];
                    break;
                  }
                }
              }
              
              // 如果有内容，更新消息列表
              if (aiMessage.content) {
                setMessages(
                  produce(getMessages(), (draft) => {
                    const idx = draft.findIndex(m => m.id === placeholderAnswerId);
                    if (idx !== -1) {
                      draft[idx] = { ...aiMessage, isStreaming: true };
                    }
                  })
                );
              }
            }
          },
          onCompleted: (hasError) => {
            // 清理打字机定时器
            if (typewriterTimer) {
              clearTimeout(typewriterTimer);
              typewriterTimer = null;
            }
            
            // 确保所有内容都已显示
            if (pendingContent && displayedLength < pendingContent.length) {
              aiMessage.content = pendingContent;
              displayedLength = pendingContent.length;
            }
            
            setIsResponding(false);
            setCurrentTaskId(null);
            
            // 标记流式结束
            setMessages(
              produce((draft) => {
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
            
            // 检查是否是用户主动停止（AbortError）
            // 支持多种格式：字符串 "AbortError"、"AbortError: The user aborted a request."
            // 或 Error 对象 { name: "AbortError" }
            const errorStr = typeof error === 'string' ? error : (error?.toString?.() || '');
            const isAborted = 
              errorStr.includes('AbortError') || 
              (error && typeof error === 'object' && 'name' in error && (error as any).name === 'AbortError') ||
              errorStr.includes('aborted');
            
            if (!isAborted) {
              toast.error(error || '发送消息失败');
              onError?.(error);
            } else {
              // 用户主动停止，静默处理，不显示错误提示
              console.log('[useAgentChat] 用户主动停止生成');
            }

            // 移除占位消息
            setMessages(getMessages().filter(m => m.id !== placeholderAnswerId));
          },
        },
        inputs
      );
    } catch (error) {
      setIsResponding(false);
      
      // 检查是否是用户主动停止（AbortError）
      const isAborted = error instanceof Error && error.name === 'AbortError';
      
      if (!isAborted) {
        console.error('发送消息失败:', error);
        toast.error('发送消息失败');
      }
      
      // 移除占位消息
      setMessages(getMessages().filter(m => m.id !== placeholderAnswerId));
    }
  }, [
    agentConfig.id,
    currentConversationId,
    isResponding,
    isValidAgent,
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
    if (!isValidAgent) return;
    
    try {
      const newConv = await agentChatService.createAgentConversation(agentConfig.id);
      setConversations([newConv, ...conversations]);
      switchConversation(newConv.id);
      toast.success('创建新会话成功');
    } catch (error) {
      console.error('创建会话失败:', error);
      toast.error('创建会话失败');
    }
  }, [agentConfig.id, isValidAgent, conversations, switchConversation]);

  // 删除会话
  const deleteConversation = useCallback(async (conversationId: string) => {
    if (!isValidAgent) return;
    
    try {
      await agentChatService.deleteAgentConversation(agentConfig.id, conversationId);
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
  }, [agentConfig.id, isValidAgent, conversations, currentConversationId, setMessages]);

  // 停止响应
  const stopResponding = useCallback(async () => {
    // 方式1: 使用 AbortController（客户端中止）
    if (abortControllerRef.current) {
      try {
        abortControllerRef.current.abort();
      } catch (error) {
        console.log('请求已中止');
      }
      abortControllerRef.current = null;
    }
    
    // 方式2: 调用后端 API（服务端停止）
    if (currentTaskId && isValidAgent) {
      try {
        const { stopMessageGeneration } = await import('@/service/agentChatService');
        await stopMessageGeneration(agentConfig.id, currentTaskId);
        toast.success('已停止生成');
      } catch (error) {
        console.error('停止生成失败:', error);
        // 不显示错误提示，因为客户端已经中止了
      }
    }
    
    setIsResponding(false);
    setCurrentTaskId(null);
  }, [currentTaskId, agentConfig.id, isValidAgent]);

  // 智能体切换时重置状态
  useEffect(() => {
    // 清空当前消息列表
    setMessages([]);
    // 重置当前会话ID
    setCurrentConversationId(null);
    // 重置响应状态
    setIsResponding(false);
    setCurrentTaskId(null);
    // 重置应用配置
    setAppConfig(null);
    // 中止当前请求
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
  }, [agentConfig.id, setMessages]);

  // 初始化
  useEffect(() => {
    if (isValidAgent) {
      loadConversations();
      loadAppConfig();
    }
  }, [loadConversations, loadAppConfig, isValidAgent]);

  return {
    // 状态
    messages,
    conversations,
    currentConversationId,
    isResponding,
    isLoading,
    currentTaskId,
    appConfig,
    
    // 方法
    sendMessage,
    loadMessages,
    loadConversations,
    loadAppConfig,
    switchConversation,
    createNewConversation,
    deleteConversation,
    stopResponding,
  };
};

