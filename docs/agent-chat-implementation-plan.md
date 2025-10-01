# Agent 对话功能完整实施方案

> 创建时间：2025-10-01  
> 预计工期：14-20 小时  
> 参考项目：webapp-conversation

---

## 📋 一、整体架构设计

### 1.1 技术栈选型

**前端**：
- **状态管理**：React Hooks（useState, useEffect, useRef）
- **API 通信**：基于现有的 `apiClient` 和 `ssePost`
- **实时通信**：SSE (Server-Sent Events) 用于流式响应
- **UI 组件**：shadcn/ui + Tailwind CSS
- **图标**：lucide-react

**后端**：
- **架构模式**：DDD 分层架构（复用现有 chat 模块结构）
- **流式响应**：FastAPI StreamingResponse
- **外部集成**：基于 dify-client SDK 与 Dify Agent 通信
- **数据存储**：复用现有的 Conversation 和 Message 模型
- **实时推送**：复用现有 WebSocket 基础设施

### 1.2 核心功能模块

```
Agent 对话功能
├── 实时流式对话（SSE）
├── 消息历史管理
├── 会话管理（创建、切换、删除）
├── Agent 思考过程展示
├── 错误处理和重试机制
└── 响应式 UI（适配移动端）
```

### 1.3 复用现有基础设施

- ✅ 复用 `api/app/chat` 的 Conversation 和 Message 模型
- ✅ 复用 `api/app/websocket` 的广播服务
- ✅ 复用前端的 `apiClient` 和认证机制
- ✅ 复用 shadcn/ui 组件库
- ✅ 复用现有的 WebSocket 连接管理

---

## 📁 二、目录结构规划

### 2.1 前端结构

```
web/src/
├── types/
│   └── agent-chat.ts              # Agent 对话类型定义
├── service/
│   └── agentChatService.ts        # Agent 对话 API 服务
├── hooks/
│   └── useAgentChat.ts            # Agent 对话状态管理 Hook
├── components/agents/
│   ├── AgentChatPanel.tsx         # 主面板（已存在）
│   ├── MessageList.tsx            # 消息列表
│   ├── MessageItem.tsx            # 单条消息（统一入口）
│   ├── UserMessage.tsx            # 用户消息组件
│   ├── AIMessage.tsx              # AI 消息组件
│   ├── AgentThinking.tsx          # Agent 思考过程
│   ├── MessageInput.tsx           # 消息输入框
│   └── EmptyState.tsx             # 空状态占位
└── lib/
    └── agent-chat-utils.ts        # 工具函数
```

### 2.2 后端结构

```
api/app/ai/
├── schemas/
│   └── agent_chat.py              # Agent 对话 Schema
├── endpoints/
│   └── agent_chat.py              # Agent 对话 API 端点
├── application/
│   └── agent_chat_service.py      # Agent 对话应用服务
├── domain/
│   ├── agent_chat_domain.py       # Agent 对话领域逻辑
│   └── entities/
│       └── agent_session.py       # Agent 会话实体
└── infrastructure/
    ├── dify_agent_client.py       # Dify Agent 客户端封装
    └── agent_conversation_repo.py # Agent 会话仓储
```

---

## 🔧 三、详细实施步骤

### 阶段一：前端基础架构（2-3小时）

#### 1.1 类型定义 `types/agent-chat.ts`

```typescript
// 消息类型
export interface AgentMessage {
  id: string;
  conversationId: string;
  content: string;
  isAnswer: boolean;              // true=AI回复, false=用户消息
  timestamp: string;
  
  // Agent 特有字段
  agentThoughts?: AgentThought[]; // 思考过程
  files?: MessageFile[];          // 附带文件
  isError?: boolean;              // 是否错误消息
  isStreaming?: boolean;          // 是否正在流式输出
}

// Agent 思考过程
export interface AgentThought {
  id: string;
  thought: string;               // 思考内容
  tool?: string;                 // 使用的工具
  toolInput?: any;               // 工具输入
  toolOutput?: any;              // 工具输出
  messageFiles?: MessageFile[];
  observation?: string;          // 观察结果
  position?: number;             // 思考步骤位置
}

// 消息文件
export interface MessageFile {
  id: string;
  type: 'image' | 'file';
  url: string;
  name?: string;
  size?: number;
}

// 会话
export interface AgentConversation {
  id: string;
  agentConfigId: string;         // 关联的 Agent 配置
  title: string;
  createdAt: string;
  updatedAt: string;
  messageCount: number;
  lastMessage?: string;
}

// SSE 事件类型
export type SSEEventType = 
  | 'message'           // 消息内容
  | 'agent_message'     // Agent 消息
  | 'agent_thought'     // Agent 思考
  | 'message_file'      // 消息文件
  | 'message_end'       // 消息结束
  | 'message_replace'   // 消息替换
  | 'error';            // 错误

// SSE 回调接口
export interface SSECallbacks {
  onData: (text: string, isFirst: boolean, meta: {
    conversationId?: string;
    messageId?: string;
    taskId?: string;
  }) => void;
  onThought?: (thought: AgentThought) => void;
  onFile?: (file: MessageFile) => void;
  onMessageEnd?: (data: any) => void;
  onMessageReplace?: (data: any) => void;
  onCompleted: (hasError?: boolean) => void;
  onError?: (error: string) => void;
  getAbortController?: (controller: AbortController) => void;
}
```

#### 1.2 服务层 `service/agentChatService.ts`

```typescript
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
  const response = await apiClient.get(
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
  const response = await apiClient.get(
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
  const response = await apiClient.post(
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
```

#### 1.3 自定义 Hook `hooks/useAgentChat.ts`

```typescript
import { useState, useCallback, useRef, useEffect } from 'react';
import { useGetState } from 'ahooks';
import produce from 'immer';
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
```

---

### 阶段二：前端 UI 组件（3-4小时）

#### 2.1 空状态组件 `components/agents/EmptyState.tsx`

```tsx
import { MessageCircle } from 'lucide-react';
import type { AgentConfig } from '@/service/agentConfigService';

interface EmptyStateProps {
  agentConfig: AgentConfig;
}

export function EmptyState({ agentConfig }: EmptyStateProps) {
  return (
    <div className="flex h-full items-center justify-center">
      <div className="text-center">
        <MessageCircle className="mx-auto h-16 w-16 text-gray-300" />
        <h3 className="mt-4 text-lg font-medium text-gray-900">
          与 {agentConfig.appName} 开始对话
        </h3>
        <p className="mt-2 text-sm text-gray-500">
          输入您的问题，AI 助手将为您提供帮助
        </p>
      </div>
    </div>
  );
}
```

#### 2.2 用户消息组件 `components/agents/UserMessage.tsx`

```tsx
import { User } from 'lucide-react';
import type { AgentMessage } from '@/types/agent-chat';

interface UserMessageProps {
  message: AgentMessage;
}

export function UserMessage({ message }: UserMessageProps) {
  return (
    <div className="flex items-start space-x-3">
      <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-blue-100">
        <User className="h-5 w-5 text-blue-600" />
      </div>
      <div className="flex-1">
        <div className="rounded-lg bg-blue-50 px-4 py-3">
          <p className="text-sm text-gray-900 whitespace-pre-wrap">{message.content}</p>
        </div>
        <p className="mt-1 text-xs text-gray-400">
          {new Date(message.timestamp).toLocaleTimeString()}
        </p>
      </div>
    </div>
  );
}
```

#### 2.3 AI 消息组件 `components/agents/AIMessage.tsx`

```tsx
import { Bot, Loader2 } from 'lucide-react';
import type { AgentMessage } from '@/types/agent-chat';
import { AgentThinking } from './AgentThinking';
import { cn } from '@/lib/utils';

interface AIMessageProps {
  message: AgentMessage;
}

export function AIMessage({ message }: AIMessageProps) {
  return (
    <div className="flex items-start space-x-3">
      <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-orange-100">
        <Bot className="h-5 w-5 text-orange-600" />
      </div>
      <div className="flex-1">
        {/* Agent 思考过程 */}
        {message.agentThoughts && message.agentThoughts.length > 0 && (
          <AgentThinking thoughts={message.agentThoughts} />
        )}
        
        {/* 消息内容 */}
        <div className={cn(
          "rounded-lg bg-white border border-gray-200 px-4 py-3",
          message.isError && "border-red-200 bg-red-50"
        )}>
          {message.isStreaming && !message.content && (
            <div className="flex items-center space-x-2 text-gray-500">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span className="text-sm">AI 正在思考...</span>
            </div>
          )}
          
          {message.content && (
            <div className="prose prose-sm max-w-none">
              <p className="text-sm text-gray-900 whitespace-pre-wrap">
                {message.content}
              </p>
            </div>
          )}
          
          {message.isError && (
            <p className="text-sm text-red-600">⚠️ 响应出错，请重试</p>
          )}
        </div>
        
        <p className="mt-1 text-xs text-gray-400">
          {new Date(message.timestamp).toLocaleTimeString()}
        </p>
      </div>
    </div>
  );
}
```

#### 2.4 思考过程组件 `components/agents/AgentThinking.tsx`

```tsx
import { ChevronDown, ChevronRight } from 'lucide-react';
import { useState } from 'react';
import type { AgentThought } from '@/types/agent-chat';

interface AgentThinkingProps {
  thoughts: AgentThought[];
}

export function AgentThinking({ thoughts }: AgentThinkingProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!thoughts || thoughts.length === 0) return null;

  return (
    <div className="mb-3 rounded-lg border border-purple-200 bg-purple-50">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex w-full items-center justify-between px-4 py-2 text-sm font-medium text-purple-900 hover:bg-purple-100"
      >
        <span>🧠 Agent 思考过程 ({thoughts.length} 步)</span>
        {isExpanded ? (
          <ChevronDown className="h-4 w-4" />
        ) : (
          <ChevronRight className="h-4 w-4" />
        )}
      </button>
      
      {isExpanded && (
        <div className="border-t border-purple-200 px-4 py-3 space-y-3">
          {thoughts.map((thought, index) => (
            <div key={thought.id} className="text-sm">
              <div className="flex items-start space-x-2">
                <span className="flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-purple-200 text-xs font-medium text-purple-900">
                  {index + 1}
                </span>
                <div className="flex-1">
                  {thought.tool && (
                    <p className="font-medium text-purple-900">
                      🔧 使用工具: {thought.tool}
                    </p>
                  )}
                  {thought.thought && (
                    <p className="mt-1 text-gray-700">{thought.thought}</p>
                  )}
                  {thought.observation && (
                    <p className="mt-1 text-gray-600">💡 {thought.observation}</p>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

#### 2.5 消息列表组件 `components/agents/MessageList.tsx`

```tsx
import { useEffect, useRef } from 'react';
import type { AgentMessage } from '@/types/agent-chat';
import { UserMessage } from './UserMessage';
import { AIMessage } from './AIMessage';

interface MessageListProps {
  messages: AgentMessage[];
  isLoading?: boolean;
}

export function MessageList({ messages, isLoading }: MessageListProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-orange-500 border-r-transparent"></div>
          <p className="mt-2 text-sm text-gray-600">加载中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      {messages.map((message) => (
        message.isAnswer ? (
          <AIMessage key={message.id} message={message} />
        ) : (
          <UserMessage key={message.id} message={message} />
        )
      ))}
      <div ref={messagesEndRef} />
    </div>
  );
}
```

#### 2.6 消息输入组件 `components/agents/MessageInput.tsx`

```tsx
import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Send, StopCircle } from 'lucide-react';

interface MessageInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  isResponding?: boolean;
  onStop?: () => void;
  placeholder?: string;
}

export function MessageInput({ 
  onSend, 
  disabled, 
  isResponding,
  onStop,
  placeholder = '输入消息...'
}: MessageInputProps) {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    const trimmed = input.trim();
    if (!trimmed || disabled) return;
    
    onSend(trimmed);
    setInput('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // 自动调整高度
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
    }
  }, [input]);

  return (
    <div className="border-t border-gray-200 bg-white p-4">
      <div className="flex items-end space-x-4">
        <div className="flex-1">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled}
            rows={1}
            className="w-full resize-none rounded-lg border border-gray-300 px-4 py-2 focus:border-orange-500 focus:outline-none focus:ring-1 focus:ring-orange-500 disabled:bg-gray-50 disabled:text-gray-500"
            style={{ maxHeight: '150px' }}
          />
          <div className="mt-1 flex items-center justify-between text-xs text-gray-500">
            <span>按 Enter 发送，Shift+Enter 换行</span>
            <span>{input.length} 字符</span>
          </div>
        </div>
        
        {isResponding ? (
          <Button
            onClick={onStop}
            variant="outline"
            className="flex items-center space-x-2"
          >
            <StopCircle className="h-4 w-4" />
            <span>停止</span>
          </Button>
        ) : (
          <Button
            onClick={handleSend}
            disabled={disabled || !input.trim()}
            className="bg-orange-500 hover:bg-orange-600 flex items-center space-x-2"
          >
            <Send className="h-4 w-4" />
            <span>发送</span>
          </Button>
        )}
      </div>
    </div>
  );
}
```

#### 2.7 更新主面板 `components/agents/AgentChatPanel.tsx`

```tsx
import { memo } from 'react';
import { Button } from '@/components/ui/button';
import { ArrowLeft, Bot } from 'lucide-react';
import type { AgentConfig } from '@/service/agentConfigService';
import { useAgentChat } from '@/hooks/useAgentChat';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';
import { EmptyState } from './EmptyState';

interface AgentChatPanelProps {
  selectedAgent: AgentConfig;
  onBack: () => void;
}

export const AgentChatPanel = memo<AgentChatPanelProps>(({ 
  selectedAgent, 
  onBack 
}) => {
  const {
    messages,
    isResponding,
    isLoading,
    sendMessage,
    stopResponding,
  } = useAgentChat({ 
    agentConfig: selectedAgent,
    onError: (error) => console.error('Chat error:', error)
  });

  return (
    <div className="container mx-auto px-4 py-6">
      {/* 头部导航 */}
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button
            variant="outline"
            size="sm"
            onClick={onBack}
            className="flex items-center space-x-2"
          >
            <ArrowLeft className="h-4 w-4" />
            <span>返回探索</span>
          </Button>
          <div className="flex items-center space-x-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-orange-100">
              <Bot className="h-5 w-5 text-orange-600" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-800">{selectedAgent.appName}</h1>
              <p className="text-sm text-gray-600">{selectedAgent.environment}</p>
            </div>
          </div>
        </div>
      </div>

      {/* 聊天面板 */}
      <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
        <div className="flex h-[calc(100vh-220px)] flex-col">
          {/* 消息列表区域 */}
          <div className="flex-1 overflow-y-auto">
            {messages.length === 0 && !isLoading ? (
              <EmptyState agentConfig={selectedAgent} />
            ) : (
              <MessageList messages={messages} isLoading={isLoading} />
            )}
          </div>

          {/* 输入区域 */}
          <MessageInput
            onSend={sendMessage}
            disabled={isResponding}
            isResponding={isResponding}
            onStop={stopResponding}
            placeholder={`向 ${selectedAgent.appName} 提问...`}
          />
        </div>
      </div>
    </div>
  );
});

AgentChatPanel.displayName = 'AgentChatPanel';
```

---

### 阶段三：后端 API 层（2-3小时）

#### 3.1 Schema 定义 `api/app/ai/schemas/agent_chat.py`

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class AgentChatRequest(BaseModel):
    """Agent 对话请求"""
    message: str = Field(..., description="用户消息", min_length=1)
    conversation_id: Optional[str] = Field(None, description="会话ID，为空则创建新会话")
    response_mode: str = Field("streaming", description="响应模式：streaming/blocking")
    inputs: Dict[str, Any] = Field(default_factory=dict, description="额外输入参数")

class AgentConversationCreate(BaseModel):
    """创建会话请求"""
    title: Optional[str] = Field(None, description="会话标题")

class AgentConversationUpdate(BaseModel):
    """更新会话请求"""
    title: str = Field(..., description="会话标题")

class AgentMessageResponse(BaseModel):
    """消息响应"""
    id: str
    conversation_id: str
    content: str
    is_answer: bool
    timestamp: str
    agent_thoughts: Optional[List[Dict[str, Any]]] = None
    files: Optional[List[Dict[str, Any]]] = None

class AgentConversationResponse(BaseModel):
    """会话响应"""
    id: str
    agent_config_id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int
    last_message: Optional[str] = None

class AgentThoughtData(BaseModel):
    """Agent 思考数据"""
    id: str
    thought: str
    tool: Optional[str] = None
    tool_input: Optional[Dict[str, Any]] = None
    tool_output: Optional[Any] = None
    observation: Optional[str] = None
    position: int
```

#### 3.2 API 端点 `api/app/ai/endpoints/agent_chat.py`

```python
"""
Agent 对话 API 端点
"""
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.common.infrastructure.db.base import get_db
from app.identity_access.deps import get_current_user
from app.identity_access.infrastructure.db.user import User
from app.ai.schemas.agent_chat import (
    AgentChatRequest,
    AgentConversationCreate,
    AgentConversationUpdate,
    AgentMessageResponse,
    AgentConversationResponse
)
from app.ai.application.agent_chat_service import AgentChatApplicationService
from app.ai.deps import get_agent_chat_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/{agent_config_id}/chat")
async def agent_chat(
    agent_config_id: str,
    request: AgentChatRequest,
    current_user: User = Depends(get_current_user),
    service: AgentChatApplicationService = Depends(get_agent_chat_service),
    db: Session = Depends(get_db)
):
    """
    Agent 流式对话
    
    支持流式响应，返回 SSE 格式数据
    """
    try:
        return StreamingResponse(
            service.stream_chat(
                agent_config_id=agent_config_id,
                user_id=str(current_user.id),
                message=request.message,
                conversation_id=request.conversation_id,
                inputs=request.inputs
            ),
            media_type="text/event-stream"
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Agent 对话失败: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="对话处理失败")


@router.get("/{agent_config_id}/conversations", response_model=List[AgentConversationResponse])
async def get_agent_conversations(
    agent_config_id: str,
    current_user: User = Depends(get_current_user),
    service: AgentChatApplicationService = Depends(get_agent_chat_service)
):
    """获取 Agent 会话列表"""
    try:
        return await service.get_conversations(
            agent_config_id=agent_config_id,
            user_id=str(current_user.id)
        )
    except Exception as e:
        logger.error(f"获取会话列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取会话列表失败")


@router.post("/{agent_config_id}/conversations", response_model=AgentConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_agent_conversation(
    agent_config_id: str,
    request: AgentConversationCreate,
    current_user: User = Depends(get_current_user),
    service: AgentChatApplicationService = Depends(get_agent_chat_service)
):
    """创建新会话"""
    try:
        return await service.create_conversation(
            agent_config_id=agent_config_id,
            user_id=str(current_user.id),
            title=request.title
        )
    except Exception as e:
        logger.error(f"创建会话失败: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建会话失败")


@router.get("/conversations/{conversation_id}/messages", response_model=List[AgentMessageResponse])
async def get_conversation_messages(
    conversation_id: str,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    service: AgentChatApplicationService = Depends(get_agent_chat_service)
):
    """获取会话消息历史"""
    try:
        return await service.get_messages(
            conversation_id=conversation_id,
            user_id=str(current_user.id),
            limit=limit
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"获取消息历史失败: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取消息历史失败")


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    service: AgentChatApplicationService = Depends(get_agent_chat_service)
):
    """删除会话"""
    try:
        await service.delete_conversation(
            conversation_id=conversation_id,
            user_id=str(current_user.id)
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"删除会话失败: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="删除会话失败")


@router.put("/conversations/{conversation_id}", response_model=AgentConversationResponse)
async def update_conversation(
    conversation_id: str,
    request: AgentConversationUpdate,
    current_user: User = Depends(get_current_user),
    service: AgentChatApplicationService = Depends(get_agent_chat_service)
):
    """更新会话"""
    try:
        return await service.update_conversation(
            conversation_id=conversation_id,
            user_id=str(current_user.id),
            title=request.title
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"更新会话失败: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新会话失败")
```

---

### 阶段四：后端应用服务层（3-4小时）

详见后续实现...

### 阶段五：后端基础设施层（2-3小时）

详见后续实现...

### 阶段六：测试和优化（2-3小时）

详见后续实现...

---

## 📊 四、开发时间估算

| 阶段 | 任务 | 预计时间 |
|------|------|---------|
| 阶段一 | 前端基础架构（类型、服务、Hook） | 2-3h |
| 阶段二 | 前端 UI 组件开发 | 3-4h |
| 阶段三 | 后端 API 层开发 | 2-3h |
| 阶段四 | 后端应用服务层 | 3-4h |
| 阶段五 | 后端基础设施层 | 2-3h |
| 阶段六 | 测试和优化 | 2-3h |
| **总计** | | **14-20h** |

---

## ✅ 五、验收标准

### 5.1 功能验收
- ✅ 能够发送消息并接收 Agent 流式响应
- ✅ 显示 Agent 思考过程
- ✅ 支持会话创建、切换、删除
- ✅ 消息历史正确加载和显示
- ✅ 错误处理和用户提示友好
- ✅ 响应式布局适配移动端

### 5.2 性能验收
- ✅ 流式响应延迟 < 1s
- ✅ 消息列表滚动流畅
- ✅ 大量消息时性能稳定

### 5.3 代码质量
- ✅ 遵循 DDD 分层架构
- ✅ TypeScript 类型完整无错误
- ✅ 代码注释清晰
- ✅ 无 Linter 错误

---

## 📝 六、后续优化方向

1. **功能增强**
   - 支持文件上传
   - 支持语音输入
   - 消息收藏和标记
   - 会话搜索

2. **用户体验**
   - 消息重新生成
   - 打字效果动画
   - 代码高亮显示
   - Markdown 渲染

3. **性能优化**
   - 虚拟滚动
   - 消息懒加载
   - 离线消息队列

---

## 📚 七、参考资料

- webapp-conversation 项目源码
- Dify SDK 文档
- FastAPI StreamingResponse 文档
- React Hooks 最佳实践

---

**文档维护**: 请在实施过程中及时更新本文档

