'use client';

import { useState, useEffect, useRef, useCallback, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import AppLayout from '@/components/layout/AppLayout';
import ChatWindow from '@/components/chat/ChatWindow';
import CustomerProfile from '@/components/profile/CustomerProfile';
import ConversationHistoryList from '@/components/chat/ConversationHistoryList';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import { ErrorDisplay } from '@/components/ui/ErrorDisplay';
import { Input } from '@/components/ui/input';
// 新增面板组件
import { ChatSearchPanel } from '@/components/chat/ChatSearchPanel';
import { ImportantMessagesPanel } from '@/components/chat/ImportantMessagesPanel';
import { ConversationSettingsPanel } from '@/components/chat/ConversationSettingsPanel';
import { ConversationParticipantsPanel } from '@/components/chat/ConversationParticipantsPanel';
import { useRoleGuard } from '@/hooks/useRoleGuard';
import { useAuthContext } from '@/contexts/AuthContext';
// 自定义hooks
import { useConversationState } from '@/hooks/useConversationState';
import { useMessageState } from '@/hooks/useMessageState';
import { useWebSocket } from '@/contexts/WebSocketContext';
import { Message, SenderType } from '@/types/chat';

function SmartCommunicationContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user } = useAuthContext();
  
  // 使用全局 WebSocket 上下文（应用级单长连接）
  const websocketState = useWebSocket();
  
  // 使用公共的权限检查Hook，但不限制特定角色
  const { isAuthorized, error, loading } = useRoleGuard({
    requireAuth: true,
    redirectTo: '/login?redirect=/chat'
  });
  
  // 获取当前用户角色
  const currentRole = user?.currentRole;
  const isConsultant = currentRole === 'consultant';
  const isCustomer = currentRole === 'customer';
  
  // URL作为唯一状态源
  const selectedCustomerId = searchParams?.get('customerId');
  const selectedConversationId = searchParams?.get('conversationId');
  const selectedFriendId = searchParams?.get('friend');
  const sceneKeyFromUrl = searchParams?.get('scene_key') || '';
  const digitalHumanIdFromUrl = searchParams?.get('digital_human_id') || '';

  // 可治理任务中枢：场景Key（为空则不触发任务路由，避免影响现有聊天）
  const [sceneKeyDraft, setSceneKeyDraft] = useState(sceneKeyFromUrl);
  useEffect(() => {
    setSceneKeyDraft(sceneKeyFromUrl);
  }, [sceneKeyFromUrl]);

  const commitSceneKeyToUrl = useCallback((nextSceneKey: string) => {
    const next = nextSceneKey.trim();
    const params = new URLSearchParams(searchParams?.toString());
    if (next) params.set('scene_key', next);
    else params.delete('scene_key');
    // 保持其他参数不变
    const qs = params.toString();
    router.replace(`/chat${qs ? `?${qs}` : ''}`, { scroll: false });
  }, [router, searchParams]);
  
  // 使用自定义hooks管理状态
  const {
    conversations,
    loadingConversations,
    selectedConversation,
    getConversation,
    clearUnreadCount,
    updateUnreadCount,
    updateLastMessage,
    refreshConversations // 解构 refreshConversations
  } = useConversationState();

  const {
    messages,
    loadingMessages,
    loadMessages,
    saveMessage,
    toggleMessageImportant
  } = useMessageState(selectedConversationId);
  
  // 使用 ref 存储函数引用，避免依赖项变化导致重复执行
  const saveMessageRef = useRef(saveMessage);
  const updateUnreadCountRef = useRef(updateUnreadCount);
  const updateLastMessageRef = useRef(updateLastMessage);
  const loadMessagesRef = useRef(loadMessages);
  const refreshConversationsRef = useRef(refreshConversations);
  
  // 更新 ref 值
  useEffect(() => {
    saveMessageRef.current = saveMessage;
    updateUnreadCountRef.current = updateUnreadCount;
    updateLastMessageRef.current = updateLastMessage;
    loadMessagesRef.current = loadMessages;
    refreshConversationsRef.current = refreshConversations;
  }, [saveMessage, updateUnreadCount, updateLastMessage, loadMessages, refreshConversations]);
    
  // 跟踪已处理的消息ID，避免重复处理
  const processedMessageIdsRef = useRef<Set<string>>(new Set());
  
  // 处理WebSocket消息 - 接收新消息（即使当前未选中任何会话，也要更新未读和预览）
  useEffect(() => {
    if (!websocketState.lastMessage) return;
    
    const { action, data } = websocketState.lastMessage;
    
    // 检查是否是有效的新消息
    if (action !== 'new_message' || !data || !data.id) {
      return;
    }
    
    // 检查消息是否已处理过（避免重复处理）
    const messageId = data.id;
    if (processedMessageIdsRef.current.has(messageId)) {
      console.log('[page.tsx] 消息已处理过，跳过:', messageId);
      return;
    }
    
    // 标记消息已处理
    processedMessageIdsRef.current.add(messageId);
    
    // 限制已处理消息集合的大小，避免内存泄漏（保留最近1000条）
    if (processedMessageIdsRef.current.size > 1000) {
      const firstId = Array.from(processedMessageIdsRef.current)[0];
      processedMessageIdsRef.current.delete(firstId);
    }
    
    console.log('处理WebSocket消息:', { action, data, selectedConversationId, messageId });
    
    // 确保content是对象格式
    let messageContent = data.content;
    if (typeof messageContent === 'string') {
      messageContent = { text: messageContent };
    } else if (!messageContent || typeof messageContent !== 'object') {
      messageContent = { text: '' };
    }
    
    // 将后端消息格式转换为前端格式
    const newMessage: Message = {
      id: data.id,
      conversationId: data.conversation_id,
      content: messageContent,
      type: data.type || 'text',
      sender: {
        id: data.sender_id,
        // WebSocket 层统一使用 'user' | 'ai' | 'system'
        type: (data.sender_type as SenderType) || 'user',
        name: data.sender_name || '未知用户',
        avatar: data.sender_avatar || '/avatars/user.png'
      },
      timestamp: data.timestamp || new Date().toISOString(),
      status: 'sent',
      is_important: data.is_important || false
    };
    
    console.log('[page.tsx] 转换后的消息:', newMessage);
    
    // 检查消息是否属于当前会话
    if (selectedConversationId && data.conversation_id === selectedConversationId) {
      console.log('[page.tsx] 消息属于当前会话，准备添加到消息列表');
      
      // 添加到消息列表
      saveMessageRef.current(newMessage);
      
      // 更新会话列表中的最后一条消息
      updateLastMessageRef.current(data.conversation_id, newMessage);
    } else {
      console.log('[page.tsx] 消息不属于当前会话或当前未选中会话:', {
        messageConversationId: data.conversation_id,
        currentConversationId: selectedConversationId
      });
      
      // 增加未读消息计数（只增加一次）
      updateUnreadCountRef.current(data.conversation_id, 1);
      
      // 更新列表预览
      updateLastMessageRef.current(data.conversation_id, newMessage);
    }
  }, [websocketState.lastMessage, selectedConversationId]);
  
  // UI状态管理
  const [isSwitchingConversation, setIsSwitchingConversation] = useState(false);
  const [loadingFriendConversation, setLoadingFriendConversation] = useState(false);
  
  // 右侧面板状态管理 - 每次只显示一个面板
  type RightPanelType = 'customer' | 'search' | 'participants' | 'important' | 'settings' | null;
  const [activeRightPanel, setActiveRightPanel] = useState<RightPanelType>('customer');
  
  const prevConversationIdRef = useRef<string | null>(selectedConversationId);

  // 当会话ID变化时加载消息
  useEffect(() => {
    if (selectedConversationId) {
      loadMessages(false);
    }
  }, [selectedConversationId, loadMessages]);

  const createFriendConversation = async (friendId: string) => {
    setLoadingFriendConversation(true);
    try {
      const { startConversationWithFriend } = await import('@/service/contacts/chatIntegration');
      const conversation = await startConversationWithFriend(friendId);
      const url = `/chat?conversationId=${conversation.id}`;
      router.replace(url, { scroll: false });
    } catch (error) {
      console.error('创建好友会话失败:', error);
    } finally {
      setLoadingFriendConversation(false);
    }
  };
  

  // 处理好友会话创建
  useEffect(() => {
    if (selectedFriendId && !selectedConversationId) {
      createFriendConversation(selectedFriendId);
    }
  }, [selectedFriendId, selectedConversationId]);
  
  // 处理会话ID变化时的切换动画
  useEffect(() => {
    if (selectedConversationId !== prevConversationIdRef.current && prevConversationIdRef.current !== null) {
      setIsSwitchingConversation(true);
      
      const timer = setTimeout(() => {
        setIsSwitchingConversation(false);
        prevConversationIdRef.current = selectedConversationId;
      }, 300);
      
      return () => clearTimeout(timer);
    } else {
      prevConversationIdRef.current = selectedConversationId;
    }
  }, [selectedConversationId]);

  // 处理消息添加
  const handleMessageAdded = useCallback((message: Message) => {
    saveMessage(message);
  }, [saveMessage]);

  // 会话选择处理
  const handleConversationSelect = useCallback(async (conversationId: string) => {
    // 选中会话时，也可以尝试清除未读消息（可选，或者等用户点击输入框）
    // 这里先不清除，等待用户交互或者明确的"已读"信号
    // 但为了更好的体验，点进去通常就算读了
    clearUnreadCount(conversationId);

    const conversation = await getConversation(conversationId);
    if (!conversation) {
      console.error('获取会话详情失败');
      return;
    }
        
    if (isConsultant && conversation.tag === 'consultation') {
      const customerId = conversation.owner_id;
      const url = `/chat?customerId=${customerId}&conversationId=${conversationId}`;
      router.push(url, { scroll: false });
    } else {
      const url = `/chat?conversationId=${conversationId}`;
      router.push(url, { scroll: false });
    }
  }, [router, isConsultant, getConversation]);

  // 会话操作处理
  const handleConversationAction = useCallback((action: string, conversationId: string) => {
    console.log('会话操作:', action, conversationId);
  }, []);

  // 右侧面板切换处理
  const handleRightPanelToggle = useCallback((panelType: RightPanelType) => {
    setActiveRightPanel(current => current === panelType ? null : panelType);
  }, []);

  // 各面板的具体切换处理
  const handleCustomerProfileToggle = useCallback(() => {
    handleRightPanelToggle('customer');
  }, [handleRightPanelToggle]);

  const handleSearchToggle = useCallback(() => {
    handleRightPanelToggle('search');
  }, [handleRightPanelToggle]);

  const handleParticipantsToggle = useCallback(() => {
    handleRightPanelToggle('participants');
  }, [handleRightPanelToggle]);

  const handleImportantToggle = useCallback(() => {
    handleRightPanelToggle('important');
  }, [handleRightPanelToggle]);

  const handleSettingsToggle = useCallback(() => {
    handleRightPanelToggle('settings');
  }, [handleRightPanelToggle]);

  // 处理消息点击 - 滚动到指定消息
  const handleMessageClick = useCallback((messageId: string) => {
    setTimeout(() => {
      const messageElement = document.getElementById(`message-${messageId}`);
      const chatContainer = document.querySelector('[data-chat-container]');
      
      if (messageElement && chatContainer) {
        chatContainer.scrollTo({
          top: messageElement.offsetTop - 100,
          behavior: 'smooth'
        });
      }
    }, 100);
  }, []);

  // 处理输入框聚焦 - 清除未读消息
  const handleInputFocus = useCallback(() => {
    if (selectedConversationId) {
      console.log('输入框获得焦点，清除未读消息:', selectedConversationId);
      clearUnreadCount(selectedConversationId);
    }
  }, [selectedConversationId, clearUnreadCount]);

  // 权限检查未通过时显示错误
  if (!isAuthorized && error) {
    return <ErrorDisplay error={error} />;
  }

  // 加载状态
  if (loading) {
    return (
      <div className="flex h-full flex-col items-center justify-center bg-gray-50">
        <LoadingSpinner size="lg" />
        <p className="mt-4 text-gray-600">加载中...</p>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col bg-gray-50 overflow-hidden">
      {/* 聊天头部 */}
      <div className="border-b border-gray-200 bg-white p-4 shadow-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <div className="mr-3 rounded-full bg-orange-100 p-2">
              <svg className="h-6 w-6 text-orange-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
            </div>
            <div>
              <h2 className="text-lg font-medium text-gray-800">智能沟通</h2>
              <p className="text-sm text-gray-500">让我们快乐沟通</p>
            </div>
          </div>

          {/* M3：对话入口注入（最小版）——配置 scene_key 以启用任务路由 */}
          <div className="flex items-center gap-2">
            <div className="text-xs text-gray-500">scene_key</div>
            <Input
              value={sceneKeyDraft}
              onChange={(e) => setSceneKeyDraft(e.target.value)}
              onBlur={() => commitSceneKeyToUrl(sceneKeyDraft)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  commitSceneKeyToUrl(sceneKeyDraft);
                }
              }}
              placeholder="留空=不触发任务路由"
              className="h-8 w-56 text-sm"
            />
          </div>
        </div>
      </div>
      
      {/* 主要内容区域 */}
      <div className="flex-1 overflow-hidden flex">
        {/* 左侧：历史会话列表 */}
        <div className="w-80 flex-shrink-0 border-r border-gray-200 bg-white">
          <ConversationHistoryList 
            conversations={conversations}
            isLoading={loadingConversations}
            onConversationSelect={handleConversationSelect}
            selectedConversationId={selectedConversationId}
          />
        </div>
        
        {/* 中间：聊天窗口 */}
        <div className="flex-1 overflow-hidden relative">
          {loadingFriendConversation ? (
            <div className="flex h-full items-center justify-center bg-gray-50">
              <div className="text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
                <h3 className="text-lg font-medium text-gray-700 mb-2">正在创建会话...</h3>
                <p className="text-gray-500">请稍候，正在为您准备与好友的对话</p>
              </div>
            </div>
          ) : selectedConversationId && selectedConversation ? (
            <ChatWindow 
              key={selectedConversationId}
              conversation={selectedConversation}
              messages={messages}
              loadingMessages={loadingMessages}
              isConsultant={isConsultant}
              hasCustomerProfile={!!selectedCustomerId}
              sceneKey={sceneKeyFromUrl || undefined}
              digitalHumanId={digitalHumanIdFromUrl || undefined}
              onAction={handleConversationAction}
              onLoadMessages={loadMessages}
              onCustomerProfileToggle={handleCustomerProfileToggle}
              onSearchToggle={handleSearchToggle}
              onParticipantsToggle={handleParticipantsToggle}
              onImportantToggle={handleImportantToggle}
              onSettingsToggle={handleSettingsToggle}
              toggleMessageImportant={toggleMessageImportant}
              onMessageAdded={handleMessageAdded}
              onInputFocus={handleInputFocus}
            />
          ) : (
            <div className="flex h-full items-center justify-center bg-gray-50">
              <div className="text-center">
                <svg className="mx-auto h-16 w-16 text-gray-300 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
                <h3 className="text-lg font-medium text-gray-700 mb-2">每次沟通，都让人开心</h3>
              </div>
            </div>
          )}
          
          {/* 会话切换指示器 */}
          {isSwitchingConversation && (
            <div className="absolute inset-0 bg-gray-50 bg-opacity-50 flex items-center justify-center z-10">
              <div className="h-1 w-64 bg-gray-200 rounded overflow-hidden">
                <div className="h-full bg-orange-500 animate-loading-bar"></div>
              </div>
            </div>
          )}
        </div>

        {/* 右侧面板区域 - 每次只显示一个面板 */}
        {activeRightPanel && (
          <div className="w-80 flex-shrink-0 border-l border-gray-200 bg-white">
            {/* 客户资料面板 */}
            {activeRightPanel === 'customer' && selectedCustomerId && (
              <CustomerProfile 
                customerId={selectedCustomerId} 
                conversationId={selectedConversationId || undefined} 
              />
            )}
            
            {/* 搜索面板 */}
            {activeRightPanel === 'search' && selectedConversationId && (
              <ChatSearchPanel
                messages={messages}
                isOpen={true}
                onClose={() => setActiveRightPanel(null)}
                onMessageClick={handleMessageClick}
              />
            )}

            {/* 参与者面板 */}
            {activeRightPanel === 'participants' && selectedConversationId && selectedConversation && (
              <ConversationParticipantsPanel
                conversationId={selectedConversation.id}
                isOpen={true}
                onClose={() => setActiveRightPanel(null)}
              />
            )}
            
            {/* 重点消息面板 */}
            {activeRightPanel === 'important' && selectedConversationId && (
              <ImportantMessagesPanel
                messages={messages}
                isOpen={true}
                onClose={() => setActiveRightPanel(null)}
                onMessageClick={handleMessageClick}
                onToggleImportant={toggleMessageImportant}
              />
            )}
            
            {/* 会话设置面板 */}
            {activeRightPanel === 'settings' && selectedConversationId && selectedConversation && (
              <ConversationSettingsPanel
                conversationId={selectedConversation.id}
                isOpen={true}
                onClose={() => setActiveRightPanel(null)}
              />
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default function SmartCommunicationPage() {
  return (
    <AppLayout>
      <Suspense fallback={<LoadingSpinner fullScreen />}>
        <SmartCommunicationContent />
      </Suspense>
    </AppLayout>
  );
}
