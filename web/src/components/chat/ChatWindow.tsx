'use client';

import { useRef, useEffect, useCallback, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import { Conversation, type Message } from '@/types/chat'
import ChatMessage from '@/components/chat/message/ChatMessage'
import MessageInput from '@/components/chat/MessageInput'
import { saveMessage } from '@/service/chatService'
import { useAuthContext } from '@/contexts/AuthContext'
import { useConversationTitleEditor } from '@/hooks/useConversationTitleEditor'
// 新的菜单系统组件
import { ChatActionsMenu } from '@/components/chat/ChatActionsMenu'
// 工具函数
import { getDisplayTitle, groupMessagesByDate } from '@/utils/conversationUtils'
import toast from 'react-hot-toast'
import { taskGovernanceService } from '@/service/taskGovernanceService'
import { MessageUtils } from '@/utils/messageUtils'
import { useWebSocket } from '@/contexts/WebSocketContext'

interface ChatWindowProps {
  conversation: Conversation;
  messages: Message[];
  loadingMessages: boolean;
  isConsultant?: boolean;
  hasCustomerProfile?: boolean;
  digitalHumanId?: string;
  onAction: (action: string, conversationId: string) => void;
  onLoadMessages: (forceRefresh?: boolean) => Promise<void>;
  onCustomerProfileToggle?: () => void;
  onSearchToggle?: () => void;
  onParticipantsToggle?: () => void;
  onImportantToggle?: () => void;
  onSettingsToggle?: () => void;
  toggleMessageImportant?: (messageId: string, currentStatus: boolean) => Promise<void>;
  onMessageAdded?: (message: Message) => void;
  onInputFocus?: () => void; // 新增
}

export default function ChatWindow({ 
  conversation, 
  messages, 
  loadingMessages,
  isConsultant = false,
  hasCustomerProfile = false,
  digitalHumanId,
  onAction,
  onLoadMessages,
  onCustomerProfileToggle,
  onSearchToggle,
  onParticipantsToggle,
  onImportantToggle,
  onSettingsToggle,
  toggleMessageImportant,
  onMessageAdded,
  onInputFocus
}: ChatWindowProps) {
  const { user } = useAuthContext();
  const router = useRouter()
  const websocketState = useWebSocket()

  // 聊天容器引用
  const chatContainerRef = useRef<HTMLDivElement>(null)
  // 跟踪上一次的消息数量，用于判断是否有新消息
  const prevMessageCountRef = useRef<number>(0)
  // 跟踪是否应该自动滚动（用户手动滚动后设为false）
  const shouldAutoScrollRef = useRef<boolean>(true)

  // 使用标题编辑hook
  const {
    editingTitleId,
    editingTitle,
    editInputRef,
    setEditingTitle,
    startEditTitle,
    saveTitle,
    handleKeyDown
  } = useConversationTitleEditor();



  // 滚动到底部
  const scrollToBottom = useCallback(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight
    }
  }, [])

  // 检查用户是否在底部附近（距离底部100px以内）
  const isNearBottom = useCallback(() => {
    if (!chatContainerRef.current) return true
    const { scrollTop, scrollHeight, clientHeight } = chatContainerRef.current
    return scrollHeight - scrollTop - clientHeight < 100
  }, [])

  // 新消息自动滚动 - 优化：只在有新消息且用户在底部附近时滚动
  useEffect(() => {
    const currentMessageCount = messages.length
    const prevMessageCount = prevMessageCountRef.current
    
    // 如果有新消息（消息数量增加）
    if (currentMessageCount > prevMessageCount) {
      // 如果用户在底部附近，自动滚动
      if (shouldAutoScrollRef.current && isNearBottom()) {
        // 使用 requestAnimationFrame 确保 DOM 更新后再滚动
        requestAnimationFrame(() => {
          scrollToBottom()
        })
      }
    }
    
    // 更新消息数量引用
    prevMessageCountRef.current = currentMessageCount
  }, [messages.length, scrollToBottom, isNearBottom])

  // 监听滚动事件，当用户手动滚动时，如果不在底部附近，禁用自动滚动
  useEffect(() => {
    const container = chatContainerRef.current
    if (!container) return

    const handleScroll = () => {
      shouldAutoScrollRef.current = isNearBottom()
    }

    container.addEventListener('scroll', handleScroll, { passive: true })
    return () => {
      container.removeEventListener('scroll', handleScroll)
    }
  }, [isNearBottom])

  // 处理发送消息
  const handleSendMessage = useCallback(async (message: Message) => {
    try {
      message.conversationId = conversation.id;
      
      // 立即添加到本地状态以提供即时反馈
      if (onMessageAdded) {
        onMessageAdded(message);
      }
      setTimeout(scrollToBottom, 100);
      
      // 异步保存到后端
      try {
        const savedMessage = await saveMessage(message);
        message.status = 'sent';
        message.id = savedMessage.id;
        if (onMessageAdded) {
          onMessageAdded(message);
        }

        // M3：Copilot 静默监听（无 scene_key）
        // - 每条可提取文本都尝试路由
        // - 不阻断现有发送流程：路由失败仅记录，不影响发送
        try {
          const routeText = MessageUtils.getTextContent(message)?.trim()
          if (routeText) {
            await taskGovernanceService.route({
              text: routeText,
              digital_human_id: digitalHumanId || undefined,
              conversation_id: conversation.id,
              message_id: savedMessage.id,
              create_fallback_task: false,
            })
          }
        } catch (routeError) {
          // 路由失败不影响发送
          console.warn('任务路由执行失败（已忽略）:', routeError)
        }
      } catch (saveError) {
        message.status = 'failed';
        message.error = saveError instanceof Error ? saveError.message : '发送失败';
        // 更新失败状态
        if (onMessageAdded) {
          onMessageAdded(message);
        }
      }
    } catch (error) {
      message.status = 'failed';
      message.error = error instanceof Error ? error.message : '发送失败';
      // 更新失败状态
      if (onMessageAdded) {
        onMessageAdded(message);
      }
    }
  }, [conversation.id, digitalHumanId, onMessageAdded, scrollToBottom])

  // Copilot 提示：通过 WebSocket system_notification 触发 toast（避免默默生成任务）
  useEffect(() => {
    const msg = websocketState.lastMessage
    if (!msg || msg.action !== 'system_notification') return

    const data = msg.data as any
    const title = typeof data?.title === 'string' ? data.title : 'AI 副驾驶'
    const messageText = typeof data?.message === 'string' ? data.message : ''

    toast((t) => (
      <div className="flex items-center gap-3">
        <div className="text-sm text-gray-800">
          <span className="font-medium">{title}</span>
          {messageText ? `：${messageText}` : ''}
        </div>
        <button
          className="text-sm text-orange-600 hover:text-orange-700"
          onClick={() => {
            toast.dismiss(t.id)
            router.push('/tasks')
          }}
        >
          去处理
        </button>
      </div>
    ))
  }, [router, websocketState.lastMessage])

  // 消息操作回调函数
  const handleToggleImportant = useCallback(async (messageId: string) => {
    try {
      const message = messages.find(msg => msg.id === messageId);
      if (message && toggleMessageImportant) {
        await toggleMessageImportant(messageId, message.is_important || false);
      }
    } catch (error) {
      //DODO： Toast 告知用户标记重点消息失败
    }
  }, [messages, toggleMessageImportant]);

  const handleReaction = useCallback(async (messageId: string, emoji: string) => {
    //DODO： Toast 告知用户添加响应
  }, []);

  const handleReply = useCallback((message: Message) => {
    //DODO： Toast 告知用户回复消息
  }, []);

  const handleDelete = useCallback(async (messageId: string) => {
    //DODO： Toast 告知用户删除消息
  }, []);

  const handleRetry = useCallback(async (message: Message) => {
    try {
      message.status = 'pending';
      message.error = undefined;
      
      const savedMessage = await saveMessage(message);
      message.status = 'sent';
      message.id = savedMessage.id;
    } catch (error) {
      message.status = 'failed';
      message.error = error instanceof Error ? error.message : '重试发送失败';
      //DODO： Toast 告知用户重试发送失败
    }
  }, []);

  const handleCardAction = useCallback((action: string, data: any) => {
    console.log('卡片操作:', action, data);
  }, []);



  // 按日期分组消息
  const messageGroups = useMemo(() => {
    return groupMessagesByDate(messages);
  }, [messages]);

  // 渲染标题编辑区域
  const renderTitleSection = () => (
    <div className="flex items-center justify-between mb-1">
      {editingTitleId === conversation.id ? (
        <input
          ref={editInputRef}
          type="text"
          value={editingTitle}
          onChange={(e) => setEditingTitle(e.target.value)}
          onBlur={() => saveTitle(conversation.id)}
          onKeyDown={(e) => handleKeyDown(e, conversation.id)}
          className="flex-1 text-sm font-medium bg-white border border-orange-300 rounded px-2 py-1 focus:outline-none focus:border-orange-500"
          onClick={(e) => e.stopPropagation()}
        />
      ) : (
        <h4 
          className="text-sm font-medium text-gray-800 truncate cursor-pointer hover:text-orange-600"
          onClick={(e) => startEditTitle(conversation, e)}
          title="点击编辑标题"
        >
          {getDisplayTitle(conversation)}
        </h4>
      )}
    </div>
  );

  // 渲染消息列表
  const renderMessageList = () => (
    <>
      {messageGroups.map((group) => (
        <div key={group.date} className="space-y-4">
          {/* 日期分隔符 */}
          <div className="flex items-center justify-center my-4">
            <div className="h-px flex-grow bg-gray-200" />
            <div className="mx-4 text-xs text-gray-500">{group.date}</div>
            <div className="h-px flex-grow bg-gray-200" />
          </div>
          
          {/* 消息列表 */}
          {group.messages.map(msg => (
            <ChatMessage
              key={msg.localId || msg.id}
              message={msg}
              isSelected={false}
              searchTerm={''}
              onToggleImportant={handleToggleImportant}
              onReaction={handleReaction}
              onReply={handleReply}
              onDelete={handleDelete}
              onRetry={handleRetry}
              onCardAction={handleCardAction}
            />
          ))}
        </div>
      ))}
    </>
  );

  // 渲染空状态
  const renderEmptyState = () => {
    if (messages.length === 0) {
      return (
        <div className="flex flex-col items-center justify-center h-64 text-gray-500">
          <svg className="h-16 w-16 mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
          <h3 className="text-lg font-medium text-gray-700 mb-2">开始对话</h3>
        </div>
      );
    }

    return null;
  };

    return (
    <div className="flex h-full flex-col overflow-hidden">
      {/* 消息列表顶部按钮 */}
      <div className="flex-shrink-0 border-b border-gray-200 bg-white p-2 shadow-sm flex justify-between">
        {renderTitleSection()}
        {/* 更多操作菜单 */}
        <ChatActionsMenu
          conversationId={conversation.id}
          isConsultant={isConsultant}
          hasCustomerProfile={hasCustomerProfile}
          onSearchToggle={onSearchToggle || (() => {})}
          onParticipantsToggle={onParticipantsToggle || (() => {})}
          onImportantMessagesToggle={onImportantToggle || (() => {})}
          onCustomerProfileToggle={onCustomerProfileToggle || (() => {})}
          onConversationSettings={onSettingsToggle || (() => {})}
        />
      </div>
      
      {/* 聊天记录 */}
      <div 
        ref={chatContainerRef}
        data-chat-container
        className="flex-1 overflow-y-auto p-4 space-y-4 min-h-0"
      >
        {/* 加载状态 */}
        {loadingMessages && (
          <div className="flex items-center justify-center h-32">
            <div className="text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500 mx-auto mb-2"></div>
              <p className="text-sm text-gray-500">加载消息中...</p>
            </div>
          </div>
        )}
        
        {/* 只有在不加载时才显示内容 */}
        {!loadingMessages && (
          <>
            {renderMessageList()}
            {renderEmptyState()}
          </>
        )}
      </div>
      
      {/* 消息输入组件 */}
      <div className="flex-shrink-0">
        <MessageInput
          conversationId={conversation.id}
          onSendMessage={handleSendMessage}
          onUpdateMessages={() => {}}
          messages={messages}
          onInputFocus={onInputFocus}
          onMessageAdded={onMessageAdded}
        />
      </div>
    </div>
  )
} 