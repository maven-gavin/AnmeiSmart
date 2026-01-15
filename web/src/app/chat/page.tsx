'use client';

import { useState, useEffect, useRef, useCallback, useMemo, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import AppLayout from '@/components/layout/AppLayout';
import ChatWindow from '@/components/chat/ChatWindow';
import CustomerProfile from '@/components/profile/CustomerProfile';
import EmployeeSummary from '@/components/profile/EmployeeSummary';
import ConversationHistoryList from '@/components/chat/ConversationHistoryList';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import { ErrorDisplay } from '@/components/ui/ErrorDisplay';
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
import { useMediaQuery } from '@/hooks/useMediaQuery';
import { Message, SenderType } from '@/types/chat';
import { ChevronLeft } from 'lucide-react';
import { getConversationParticipants } from '@/service/chatService';
import { userService } from '@/service/userService';

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
  
  // URL作为唯一状态源
  const selectedConversationId = searchParams?.get('conversationId');
  const selectedFriendId = searchParams?.get('friend');
  const digitalHumanIdFromUrl = searchParams?.get('digital_human_id') || '';
  
  // 使用自定义hooks管理状态
  const {
    conversations,
    loadingConversations,
    selectedConversation,
    getConversation,
    clearUnreadCount,
    updateUnreadCount,
    updateLastMessage,
    refreshConversations
  } = useConversationState();

  const {
    messages,
    loadingMessages,
    loadMessages,
    saveMessage,
    toggleMessageImportant
  } = useMessageState(selectedConversationId);

  const [peerUserId, setPeerUserId] = useState<string | null>(null);
  const [peerUserType, setPeerUserType] = useState<'customer' | 'staff' | null>(null);
  const [peerUserLoading, setPeerUserLoading] = useState(false);
  const [peerUserError, setPeerUserError] = useState<string | null>(null);
  
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

  // 获取对话对方信息（用于客户档案/员工简要信息）
  useEffect(() => {
    if (!selectedConversationId || !user?.id) {
      setPeerUserId(null);
      setPeerUserType(null);
      setPeerUserError(null);
      setPeerUserLoading(false);
      return;
    }

    let cancelled = false;

    const loadPeerUser = async () => {
      setPeerUserLoading(true);
      setPeerUserError(null);

      try {
        const participants = await getConversationParticipants(selectedConversationId);
        const candidate = participants.find(p => p.userId && p.userId !== user.id)
          || participants.find(p => p.userId);

        if (!candidate?.userId) {
          if (!cancelled) {
            setPeerUserId(null);
            setPeerUserType(null);
          }
          return;
        }

        const targetUserId = candidate.userId;
        if (!cancelled) {
          setPeerUserId(targetUserId);
        }

        const targetUser = await userService.getUser(targetUserId);
        if (cancelled) return;

        const roles = targetUser.roles || [];
        const staffRoles = new Set(['admin', 'administrator', 'operator']);
        const hasStaffRole = roles.some((role) => staffRoles.has(role));
        const isCustomerRole = roles.includes('customer') || targetUser.activeRole === 'customer';

        setPeerUserType(hasStaffRole ? 'staff' : (isCustomerRole ? 'customer' : 'staff'));
      } catch (err) {
        if (!cancelled) {
          setPeerUserError(err instanceof Error ? err.message : '获取对话对方信息失败');
          setPeerUserType(null);
        }
      } finally {
        if (!cancelled) {
          setPeerUserLoading(false);
        }
      }
    };

    loadPeerUser();

    return () => {
      cancelled = true;
    };
  }, [selectedConversationId, user?.id]);
    
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
      return;
    }
    
    // 标记消息已处理
    processedMessageIdsRef.current.add(messageId);
    
    // 限制已处理消息集合的大小，避免内存泄漏（保留最近1000条）
    if (processedMessageIdsRef.current.size > 1000) {
      const firstId = Array.from(processedMessageIdsRef.current)[0];
      processedMessageIdsRef.current.delete(firstId);
    }
    
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
    
    // 检查消息是否属于当前会话
    if (selectedConversationId && data.conversation_id === selectedConversationId) {
      // 添加到消息列表
      saveMessageRef.current(newMessage);
      
      // 更新会话列表中的最后一条消息
      updateLastMessageRef.current(data.conversation_id, newMessage);
    } else {
      // 增加未读消息计数（只增加一次）
      updateUnreadCountRef.current(data.conversation_id, 1);
      
      // 更新列表预览
      updateLastMessageRef.current(data.conversation_id, newMessage);
    }
  }, [websocketState.lastMessage, selectedConversationId]);
  
  // 移动端检测
  const isMobile = useMediaQuery(768);
  
  // UI状态管理
  const [isSwitchingConversation, setIsSwitchingConversation] = useState(false);
  const [loadingFriendConversation, setLoadingFriendConversation] = useState(false);
  const [isHistoryListCollapsed, setIsHistoryListCollapsed] = useState(false);
  
  // 移动端视图状态管理
  type MobileViewType = 'history' | 'chat' | 'panel';
  const [mobileView, setMobileView] = useState<MobileViewType>(() => {
    // 移动端：默认先展示会话列表；进入聊天由“点击会话”驱动，而不是由 selectedConversationId 驱动
    return 'history';
  });
  
  // 右侧面板状态管理 - 每次只显示一个面板
  type RightPanelType = 'customer' | 'search' | 'participants' | 'important' | 'settings' | null;
  const [activeRightPanel, setActiveRightPanel] = useState<RightPanelType>(null);
  
  const prevConversationIdRef = useRef<string | null>(selectedConversationId);

  // URL 刷新场景兜底：
  // - 列表可能已高亮（来自 URL），但 selectedConversation 仅在 getConversation() 后才会被填充
  // - 因此需要从列表中兜底找到会话，或主动拉取详情，避免移动端进入“无头空态”导致无法切换
  const conversationFromList = useMemo(() => {
    if (!selectedConversationId) return null;
    return conversations.find(c => c.id === selectedConversationId) || null;
  }, [conversations, selectedConversationId]);

  const effectiveConversation = selectedConversation || conversationFromList;

  // 当 URL 中有会话ID，但尚未拿到会话详情时，主动补齐 selectedConversation
  useEffect(() => {
    if (!selectedConversationId) return;
    if (selectedConversation?.id === selectedConversationId) return;
    if (conversationFromList) return; // 列表中已有足够信息可渲染

    // 仅在确实缺失时拉取详情
    getConversation(selectedConversationId).catch((e) => {
      console.error('刷新后补齐会话详情失败:', e);
    });
  }, [selectedConversationId, selectedConversation?.id, conversationFromList, getConversation]);

  // 当会话ID变化时加载消息
  useEffect(() => {
    if (selectedConversationId) {
      loadMessages(false);
    }
  }, [selectedConversationId, loadMessages]);

  // 移动端：根据会话/面板状态，保证视图与业务状态一致
  useEffect(() => {
    if (!isMobile) {
      return;
    }

    // 没有会话时，强制回到会话列表，并关闭面板（避免"空会话 + 面板"悬空）
    if (!selectedConversationId) {
      setActiveRightPanel(null);
      setMobileView('history');
      return;
    }

    // 有会话：仅当面板打开时切换到 panel
    // 其余情况尊重用户当前视图（history/chat），避免"返回列表"被强制跳回 chat
    if (activeRightPanel) {
      setMobileView('panel');
    }
  }, [isMobile, selectedConversationId, activeRightPanel, mobileView]);

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
    // 选中会话时清除未读消息
    clearUnreadCount(conversationId);

    // 移动端：立即切换到聊天窗口视图（在路由跳转前）
    if (isMobile) {
      setMobileView('chat');
    }

    const conversation = await getConversation(conversationId);
    if (!conversation) {
      return;
    }
        
    const url = `/chat?conversationId=${conversationId}`;
    router.push(url, { scroll: false });
  }, [router, getConversation, isMobile, clearUnreadCount]);

  // 会话操作处理
  const handleConversationAction = useCallback((action: string, conversationId: string) => {
    // 会话操作处理逻辑
  }, []);

  // 右侧面板切换处理
  const handleRightPanelToggle = useCallback((panelType: RightPanelType) => {
    if (isMobile) {
      // 移动端：切换面板时，如果打开面板则切换到 panel 视图，关闭则回到 chat 视图
      if (activeRightPanel === panelType) {
        // 关闭面板
        setActiveRightPanel(null);
        // 关闭面板后只回到聊天窗口（面板操作发生在聊天内）
        setMobileView('chat');
      } else {
        // 打开面板
        setActiveRightPanel(panelType);
        setMobileView('panel');
      }
    } else {
      // 桌面端：保持原有逻辑
      setActiveRightPanel(current => current === panelType ? null : panelType);
    }
  }, [isMobile, activeRightPanel, selectedConversationId]);

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
      clearUnreadCount(selectedConversationId);
    }
  }, [selectedConversationId, clearUnreadCount]);

  const closeMobilePanel = useCallback(() => {
    setActiveRightPanel(null);
    // 关闭面板后只回到聊天窗口
    setMobileView('chat');
  }, []);

  // 移动端：处理返回会话列表
  const handleBackToHistory = useCallback(() => {
    if (isMobile) {
      setMobileView('history');
    } else {
      setIsHistoryListCollapsed(false);
    }
  }, [isMobile]);

  // 抽取面板内容渲染函数，减少重复代码
  const renderRightPanelContent = useCallback((onClose: () => void) => {
    if (!activeRightPanel) return null;

    switch (activeRightPanel) {
      case 'customer':
        if (peerUserLoading) {
          return (
            <div className="flex h-full items-center justify-center p-6">
              <LoadingSpinner />
            </div>
          );
        }

        if (peerUserError) {
          return (
            <div className="am-card p-4">
              <div className="text-sm text-red-600">{peerUserError}</div>
            </div>
          );
        }

        if (!peerUserId) {
          return (
            <div className="am-card p-4">
              <div className="text-sm text-gray-500">未找到对方信息</div>
            </div>
          );
        }

        if (!peerUserType) {
          return (
            <div className="am-card p-4">
              <div className="text-sm text-gray-500">正在识别对方类型...</div>
            </div>
          );
        }

        return peerUserType === 'staff' ? (
          <EmployeeSummary userId={peerUserId} />
        ) : (
          <CustomerProfile 
            customerId={peerUserId} 
            conversationId={selectedConversationId || undefined} 
          />
        );
      
      case 'search':
        return selectedConversationId ? (
          <ChatSearchPanel
            messages={messages}
            isOpen={true}
            onClose={onClose}
            onMessageClick={handleMessageClick}
          />
        ) : null;
      
      case 'participants':
        return selectedConversationId && selectedConversation ? (
          <ConversationParticipantsPanel
            conversationId={selectedConversation.id}
            isOpen={true}
            onClose={onClose}
          />
        ) : null;
      
      case 'important':
        return selectedConversationId ? (
          <ImportantMessagesPanel
            messages={messages}
            isOpen={true}
            onClose={onClose}
            onMessageClick={handleMessageClick}
            onToggleImportant={toggleMessageImportant}
          />
        ) : null;
      
      case 'settings':
        return selectedConversationId && selectedConversation ? (
          <ConversationSettingsPanel
            conversationId={selectedConversation.id}
            isOpen={true}
            onClose={onClose}
          />
        ) : null;
      
      default:
        return null;
    }
  }, [
    activeRightPanel,
    peerUserId,
    peerUserType,
    peerUserLoading,
    peerUserError,
    selectedConversationId,
    selectedConversation,
    messages,
    handleMessageClick,
    toggleMessageImportant
  ]);

  // 获取面板标题
  const getPanelTitle = useCallback((panelType: RightPanelType): string => {
    switch (panelType) {
      case 'customer': return '对方信息';
      case 'search': return '搜索';
      case 'participants': return '参与者';
      case 'important': return '重点消息';
      case 'settings': return '会话设置';
      default: return '';
    }
  }, []);

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
        </div>
      </div>
      
      {/* 主要内容区域 */}
      <div className={isMobile ? "flex-1 overflow-hidden" : "flex-1 overflow-hidden flex"}>
        {/* 移动端：根据视图状态显示不同内容 */}
        {isMobile ? (
          <>
            {/* 会话列表视图 */}
            {mobileView === 'history' && (
              <div className="w-full h-full flex-shrink-0 bg-white">
                <ConversationHistoryList 
                  conversations={conversations}
                  isLoading={loadingConversations}
                  onConversationSelect={handleConversationSelect}
                  selectedConversationId={selectedConversationId}
                  onFilterChange={(unassignedOnly) => refreshConversations(false, unassignedOnly)}
                />
              </div>
            )}
            
            {/* 聊天窗口视图 */}
            {mobileView === 'chat' && (
              <div className="w-full h-full flex-shrink-0 overflow-hidden relative">
                {loadingFriendConversation ? (
                  <div className="flex h-full items-center justify-center bg-gray-50">
                    <div className="text-center">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
                      <h3 className="text-lg font-medium text-gray-700 mb-2">正在创建会话...</h3>
                      <p className="text-gray-500">请稍候，正在为您准备与好友的对话</p>
                    </div>
                  </div>
                ) : selectedConversationId && effectiveConversation ? (
                  <ChatWindow 
                    key={selectedConversationId}
                    conversation={effectiveConversation}
                    messages={messages}
                    loadingMessages={loadingMessages}
                    hasCustomerProfile={!!peerUserId}
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
                    isHistoryListCollapsed={true}
                    onToggleHistoryList={handleBackToHistory}
                    peerUserId={peerUserId}
                    peerUserType={peerUserType}
                  />
                ) : (
                  // 有会话ID但会话详情尚未补齐时，展示可返回的加载态，避免“无头空态”卡死
                  selectedConversationId ? (
                    <div className="flex h-full flex-col bg-gray-50">
                      <div className="flex-shrink-0 border-b border-gray-200 bg-white px-3 py-2 flex items-center gap-2">
                        <button
                          onClick={handleBackToHistory}
                          className="flex-shrink-0 p-1.5 rounded-md hover:bg-orange-50 transition-colors"
                          title="返回会话列表"
                        >
                          <ChevronLeft className="h-4 w-4 text-orange-500" />
                        </button>
                        <div className="text-sm font-medium text-gray-800 truncate">加载会话中...</div>
                      </div>
                      <div className="flex-1 flex items-center justify-center">
                        <div className="text-center">
                          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500 mx-auto mb-3"></div>
                          <div className="text-sm text-gray-500">正在加载消息历史</div>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="flex h-full items-center justify-center bg-gray-50">
                      <div className="text-center">
                        <svg className="mx-auto h-16 w-16 text-gray-300 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                        </svg>
                        <h3 className="text-lg font-medium text-gray-700 mb-2">每次沟通，都让人开心</h3>
                      </div>
                    </div>
                  )
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
            )}
            
            {/* 面板视图 */}
            {mobileView === 'panel' && activeRightPanel && (
              <div className="w-full h-full flex-shrink-0 bg-white flex flex-col">
                {/* 面板顶部栏：提供统一关闭入口（尤其是 customer 面板） */}
                <div className="flex-shrink-0 border-b border-gray-200 bg-white px-3 py-2 flex items-center gap-2">
                  <button
                    onClick={closeMobilePanel}
                    className="flex-shrink-0 p-1.5 rounded-md hover:bg-orange-50 transition-colors"
                    title="返回"
                  >
                    <ChevronLeft className="h-4 w-4 text-orange-500" />
                  </button>
                  <div className="text-sm font-medium text-gray-800 truncate">
                    {getPanelTitle(activeRightPanel)}
                  </div>
                </div>
                <div className="flex-1 min-h-0 overflow-hidden">
                  {renderRightPanelContent(closeMobilePanel)}
                </div>
              </div>
            )}
          </>
        ) : (
          <>
            {/* 桌面端：保持原有布局 */}
            {/* 左侧：历史会话列表 */}
            {!isHistoryListCollapsed && (
              <div className="w-80 flex-shrink-0 border-r border-gray-200 bg-white">
                <ConversationHistoryList 
                  conversations={conversations}
                  isLoading={loadingConversations}
                  onConversationSelect={handleConversationSelect}
                  selectedConversationId={selectedConversationId}
                  onFilterChange={(unassignedOnly) => refreshConversations(false, unassignedOnly)}
                  onToggleCollapse={() => setIsHistoryListCollapsed(true)}
                />
              </div>
            )}
            
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
              ) : selectedConversationId && effectiveConversation ? (
                <ChatWindow 
                  key={selectedConversationId}
                  conversation={effectiveConversation}
                  messages={messages}
                  loadingMessages={loadingMessages}
                  hasCustomerProfile={!!peerUserId}
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
                  isHistoryListCollapsed={isHistoryListCollapsed}
                  onToggleHistoryList={() => setIsHistoryListCollapsed(!isHistoryListCollapsed)}
                  peerUserId={peerUserId}
                  peerUserType={peerUserType}
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
                {renderRightPanelContent(() => setActiveRightPanel(null))}
              </div>
            )}
          </>
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
