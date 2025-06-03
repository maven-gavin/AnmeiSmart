'use client';

import { useState, useRef, useEffect, useCallback, useMemo } from 'react'
import { Button } from '@/components/ui/button'
import { type Message, type Conversation } from '@/types/chat'
import ChatMessage from '@/components/chat/ChatMessage'
import { 
  sendTextMessage, 
  sendImageMessage, 
  sendVoiceMessage,
  getAIResponse,
  getConversationMessages,
  markMessageAsImportant,
  takeoverConversation,
  switchBackToAI,
  isConsultantMode,
  initializeWebSocket,
  closeWebSocketConnection,
  addMessageCallback,
  removeMessageCallback,
  getConnectionStatus,
  addWsConnectionStatusListener,
  removeWsConnectionStatusListener,
  getConversations,
  getOrCreateConversation,
  syncConsultantTakeoverStatus
} from '@/service/chatService'
import { ConnectionStatus } from '@/service/websocket'
import { useAuthContext } from '@/contexts/AuthContext'
import { useSearchParams, useRouter } from 'next/navigation'
import FAQSection, { type FAQ } from './FAQSection'

interface ChatWindowProps {
  conversationId?: string;
}

export default function ChatWindow({ conversationId }: ChatWindowProps) {
  // 使用路由导航
  const router = useRouter();
  
  // 获取URL参数
  const searchParams = useSearchParams()
  
  // 当前对话ID - 优先使用props传入的conversationId，其次是URL参数
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(
    conversationId || searchParams?.get('conversationId') || null
  )
  
  // 监听props/searchParams中的conversationId变化
  useEffect(() => {
    if (conversationId) {
      console.log(`ChatWindow props中的conversationId变化: ${conversationId}`);
      setCurrentConversationId(conversationId);
    } else {
      // 如果props中的conversationId为undefined，尝试从URL获取
      const urlConversationId = searchParams?.get('conversationId');
      if (urlConversationId && urlConversationId !== currentConversationId) {
        console.log(`ChatWindow URL中的conversationId变化: ${urlConversationId}`);
        setCurrentConversationId(urlConversationId);
      }
    }
  }, [conversationId, searchParams]);
  
  // 获取身份验证上下文
  const { user } = useAuthContext();
  
  // 基本状态
  const [message, setMessage] = useState('')
  const [showFAQ, setShowFAQ] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [messages, setMessages] = useState<Message[]>([])
  
  // 用户角色状态
  const isConsultant = user?.currentRole === 'consultant'
  
  // 搜索功能状态
  const [showSearch, setShowSearch] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [searchResults, setSearchResults] = useState<Message[]>([])
  const [selectedMessageId, setSelectedMessageId] = useState<string | null>(null)
  
  // 标记重点功能状态
  const [showImportantOnly, setShowImportantOnly] = useState(false)
  const [importantMessages, setImportantMessages] = useState<Message[]>([])
  
  // 顾问接管状态
  const [isConsultantTakeover, setIsConsultantTakeover] = useState(false)
  
  // 媒体状态
  const [imagePreview, setImagePreview] = useState<string | null>(null)
  const [uploadingImage, setUploadingImage] = useState(false)
  const [audioPreview, setAudioPreview] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  
  // 录音状态
  const [isRecording, setIsRecording] = useState(false)
  const [recordingTime, setRecordingTime] = useState(0)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const recordingTimerRef = useRef<NodeJS.Timeout | null>(null)
  
  // 聊天区域引用
  const chatContainerRef = useRef<HTMLDivElement>(null)
  
  // FAQ状态 - 只保留searchQuery
  const [searchQuery, setSearchQuery] = useState('')
  
  // WebSocket连接状态
  const [wsStatus, setWsStatus] = useState<ConnectionStatus>(ConnectionStatus.DISCONNECTED);
  
  // 使用ref追踪组件是否已挂载
  const mounted = useRef(false);
  
  // 添加消息发送状态，与通用的isLoading分开
  const [isSending, setIsSending] = useState(false);
  

  // 修改挂载状态跟踪
  useEffect(() => {
    // 设置挂载状态为true
    mounted.current = true;
    
    console.log('ChatWindow: 组件实际挂载, mounted=true');
    
    // 组件卸载时清理
    return () => {
      mounted.current = false;
      console.log('ChatWindow: 组件实际卸载, mounted=false');
      
      // 关闭WebSocket连接
      closeWebSocketConnection();
    };
  }, []); // 空依赖数组确保只在挂载和卸载时执行
  
  // 静默更新消息的方法
  const silentlyUpdateMessages = useCallback(async () => {
    if (!currentConversationId) return;
    
    try {
      const currentMessagesList = [...messages]; // Use current state directly
      const lastMessageId = currentMessagesList.length > 0 ? currentMessagesList[currentMessagesList.length - 1].id : null;
      
      const newMessages = await getConversationMessages(currentConversationId, true); // Force refresh
      
      if (!mounted.current) return;
      
      if (newMessages.length > currentMessagesList.length || JSON.stringify(newMessages) !== JSON.stringify(currentMessagesList)) {
        console.log('ChatWindow:静默更新，消息有变化，更新UI');
        setMessages(newMessages);
        if (showImportantOnly) {
          const important = newMessages.filter(msg => msg.isImportant);
          setImportantMessages(important);
        }
        const newLastMessageId = newMessages.length > 0 ? newMessages[newMessages.length - 1].id : null;
        if (lastMessageId !== newLastMessageId) {
          setTimeout(scrollToBottom, 100);
        }
      } else {
        console.log('ChatWindow:静默更新，消息无变化');
      }

      try {
        const isConsultantModeActive = await syncConsultantTakeoverStatus(currentConversationId);
        if (isConsultantModeActive !== isConsultantTakeover) {
          setIsConsultantTakeover(isConsultantModeActive);
        }
      } catch (error) {
        console.error('ChatWindow:同步顾问状态失败(静默更新中):', error);
      }
    } catch (error) {
      console.error('ChatWindow:静默获取消息出错:', error);
    }
  }, [currentConversationId, showImportantOnly, isConsultantTakeover, messages, mounted]); // messages dependency is important here


  // 重新连接WebSocket的函数
  const reconnectWebSocket = useCallback(() => {
    console.log('[ChatWindow] reconnectWebSocket called. User:', !!user, 'CurrentConversationId:', currentConversationId, 'Current wsStatus:', wsStatus);
    if (!mounted.current) {
      console.log('[ChatWindow] 组件未挂载，忽略WebSocket重连请求');
      return;
    }
    
    if (user && currentConversationId) {
      console.log(`[ChatWindow] Attempting to reconnect WebSocket for conv ${currentConversationId} with user ${user.id}`);
      
      // 先关闭任何现有连接
      closeWebSocketConnection(); 
      
      // 立即设置状态为连接中
      setWsStatus(ConnectionStatus.CONNECTING);
      
      // 短暂延迟后初始化连接
      setTimeout(() => {
        if (mounted.current) {
          console.log(`[ChatWindow] Calling initializeWebSocket for ${currentConversationId}`);
          initializeWebSocket(user.id, currentConversationId);
        } else {
          console.log('[ChatWindow] reconnectWebSocket: Component unmounted, aborting init.');
        }
      }, 100);
    } else {
      console.warn('[ChatWindow] reconnectWebSocket: Aborted. User or CurrentConversationId is missing.', { userId: user?.id, currentConversationId });
    }
  }, [user, currentConversationId, wsStatus]);
  
  // 添加一个函数来根据时间戳格式化日期，以便分组显示
  const formatMessageDate = (timestamp: string): string => {
    const date = new Date(timestamp);
    const today = new Date();
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    
    // 格式化日期: 今天/昨天/具体日期
    if (date.toDateString() === today.toDateString()) {
      return '今天';
    } else if (date.toDateString() === yesterday.toDateString()) {
      return '昨天';
    } else {
      return `${date.getFullYear()}年${date.getMonth() + 1}月${date.getDate()}日`;
    }
  };
  
  // 统一的会话和WebSocket初始化逻辑
  useEffect(() => {
    // 设置挂载状态
    mounted.current = true;
    
    // 监听页面可见性变化
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        console.log('ChatWindow: 页面变为可见，检查WebSocket连接');
        if (user && currentConversationId && wsStatus !== ConnectionStatus.CONNECTED) {
          console.log(`ChatWindow: 页面可见，WS状态为 ${wsStatus}，尝试重新连接 for ${currentConversationId}`);
          reconnectWebSocket();
        }
      }
    };
    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    // 监听窗口焦点变化
    const handleFocus = () => {
      console.log('ChatWindow: 窗口获得焦点，检查WebSocket连接');
      if (user && currentConversationId && wsStatus !== ConnectionStatus.CONNECTED && document.visibilityState === 'visible') {
        console.log(`ChatWindow: 窗口获得焦点，WS状态为 ${wsStatus}，尝试重新连接 for ${currentConversationId}`);
        reconnectWebSocket();
      }
    };
    window.addEventListener('focus', handleFocus);
    
    // 组件卸载时清理
    return () => {
      console.log('ChatWindow组件卸载，关闭WebSocket连接');
      mounted.current = false;
      closeWebSocketConnection();
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('focus', handleFocus);
    };
  }, [currentConversationId, user, router, reconnectWebSocket, wsStatus]);  // 添加必要的依赖
  
  // 监听会话ID变化，重新加载消息和初始化WebSocket
  useEffect(() => {
    if (!mounted.current || !user || !currentConversationId) return;
    
    console.log(`ChatWindow: 会话ID变化为 ${currentConversationId}，重新加载数据和WebSocket`);
    const abortController = new AbortController();
    
    setIsLoading(true);
    setMessages([]);
    setImportantMessages([]);
    
    // 设置WebSocket状态为连接中
    setWsStatus(ConnectionStatus.CONNECTING);
    
    const loadMessagesAndInitWS = async () => {
      try {
        const messagesData = await getConversationMessages(currentConversationId, true);
        
        if (abortController.signal.aborted || !mounted.current) return;
        
        if (messagesData && messagesData.length > 0) {
          setMessages(messagesData);
          const important = messagesData.filter(msg => msg.isImportant);
          setImportantMessages(important);
          setTimeout(scrollToBottom, 100);
        }
        
        const isConsultantModeActive = isConsultantMode(currentConversationId);
        setIsConsultantTakeover(isConsultantModeActive);
        
        // 确保组件仍然挂载，再初始化WebSocket
        if (mounted.current && !abortController.signal.aborted) {
          // 先关闭现有连接
          closeWebSocketConnection();
          
          // 初始化新连接
          initializeWebSocket(user.id, currentConversationId);
        }
      } catch (error) {
        console.error('加载消息或初始化WebSocket失败:', error);
      } finally {
        if (mounted.current && !abortController.signal.aborted) {
          setIsLoading(false);
        }
      }
    };
    
    loadMessagesAndInitWS();
    
    return () => {
      abortController.abort();
    };
  }, [currentConversationId, user]);  // 依赖于会话ID和用户的变化

  // 监听WebSocket状态 - 改为事件驱动
  useEffect(() => {
    const handleStatusChange = (event: any) => {
      console.log('ChatWindow收到WebSocket状态变化事件:', event);
      if (event && event.newStatus) {
        setWsStatus(event.newStatus);
        
        if (event.newStatus === ConnectionStatus.CONNECTED && currentConversationId) {
          console.log(`WebSocket通过事件连接成功，静默刷新消息，会话ID: ${currentConversationId}`);
          silentlyUpdateMessages();
        }
      }
    };

    addWsConnectionStatusListener(handleStatusChange);

    return () => {
      removeWsConnectionStatusListener(handleStatusChange);
    };
  }, [currentConversationId, silentlyUpdateMessages]); 
  
  // 监听窗口焦点变化
  useEffect(() => {
    const handleFocus = () => {
      console.log('ChatWindow: 窗口获得焦点，检查WebSocket连接');
      if (user && currentConversationId && wsStatus !== ConnectionStatus.CONNECTED && document.visibilityState === 'visible') {
        console.log(`ChatWindow: 窗口获得焦点，WS状态为 ${wsStatus}，尝试重新连接 for ${currentConversationId}`);
        reconnectWebSocket();
      }
    };
    
    window.addEventListener('focus', handleFocus);
    
    return () => {
      window.removeEventListener('focus', handleFocus);
    };
  }, [user, currentConversationId, wsStatus, reconnectWebSocket]); // Added wsStatus and reconnectWebSocket
  
  // 监听WebSocket消息 - 依赖于currentConversationId
  useEffect(() => {
    if (!user || !currentConversationId) return;
    
    console.log(`设置WebSocket消息监听: 用户ID=${user.id}, 会话ID=${currentConversationId}`);
    
    // 创建AbortController用于取消操作
    const abortController = new AbortController();
    
    // 监听WebSocket消息
    const handleMessage = async (data: any) => {
      // 如果已取消，不处理消息
      if (abortController.signal.aborted) return;
    
      // 确保只处理当前会话的消息
      if (!data.conversation_id || data.conversation_id !== currentConversationId) {
        console.log(`忽略非当前会话的消息: ${data.conversation_id} vs ${currentConversationId}`);
        return;
      }
      
      console.log(`ChatWindow收到当前会话的WebSocket消息:`, data);
      
      // 收到消息后静默刷新消息列表，不显示加载状态
      try {
        // 如果已取消，不继续处理
        if (abortController.signal.aborted) return;
        
        const messages = await getConversationMessages(currentConversationId);
        
        // 再次检查是否取消，避免设置过时状态
        if (abortController.signal.aborted) return;
        
        setMessages(messages);
        
        // 如果显示重点消息，也更新重点消息列表
        if (showImportantOnly) {
          const important = messages.filter(msg => msg.isImportant);
          setImportantMessages(important);
        }
        
        // 滚动到底部
        setTimeout(() => {
          scrollToBottom();
        }, 100);
      } catch (error) {
        // 如果已取消，不处理错误
        if (abortController.signal.aborted) return;
        
        console.error('更新消息失败:', error);
      }
    };
    
    // 添加消息回调
    addMessageCallback('message', handleMessage);
    addMessageCallback('system', handleMessage);
    addMessageCallback('connect', handleMessage);
    
    // 组件卸载或会话ID变化时移除回调
    return () => {
      console.log(`移除WebSocket消息回调, 会话ID: ${currentConversationId}`);
      abortController.abort();
      removeMessageCallback('message', handleMessage);
      removeMessageCallback('system', handleMessage);
      removeMessageCallback('connect', handleMessage);
    };
  }, [currentConversationId, user, showImportantOnly]);
  
  // 获取当前会话消息 - 更新以支持可能为null的会话ID
  const fetchMessages = async () => {
    try {
      if (!currentConversationId) return;
      
      setIsLoading(true);
      
      // 获取消息
      try {
        const messages = await getConversationMessages(currentConversationId, true); // 使用强制刷新
        setMessages(messages);
      } catch (error) {
        console.error('获取消息出错:', error);
      }
    
      // 检查顾问接管状态
      try {
        // 使用新的同步函数
        const isConsultantModeActive = await syncConsultantTakeoverStatus(currentConversationId);
        setIsConsultantTakeover(isConsultantModeActive);
        console.log(`会话 ${currentConversationId} 顾问接管状态: ${isConsultantModeActive}`);
      } catch (error) {
        console.error('同步顾问状态失败:', error);
      }
      
    } catch (error) {
      console.error('获取数据出错:', error);
    } finally {
      setIsLoading(false);
    }
  };
  
  // 插入FAQ内容
  const insertFAQ = (faq: FAQ) => {
    setMessage(faq.question)
    setShowFAQ(false)
  }
  
  // 滚动到指定消息
  const scrollToMessage = (messageId: string) => {
    setTimeout(() => {
      const messageElement = document.getElementById(`message-${messageId}`)
      if (messageElement && chatContainerRef.current) {
        chatContainerRef.current.scrollTo({
          top: messageElement.offsetTop - 100, // 偏移量，确保消息在可视区域
          behavior: 'smooth'
        })
      }
    }, 100)
  }
  
  // 切换到下一个搜索结果
  const goToNextSearchResult = () => {
    if (searchResults.length === 0 || !selectedMessageId) return
    
    const currentIndex = searchResults.findIndex(msg => msg.id === selectedMessageId)
    const nextIndex = (currentIndex + 1) % searchResults.length
    
    setSelectedMessageId(searchResults[nextIndex].id)
    scrollToMessage(searchResults[nextIndex].id)
  }
  
  // 切换到上一个搜索结果
  const goToPreviousSearchResult = () => {
    if (searchResults.length === 0 || !selectedMessageId) return
    
    const currentIndex = searchResults.findIndex(msg => msg.id === selectedMessageId)
    const prevIndex = currentIndex === 0 ? searchResults.length - 1 : currentIndex - 1
    
    setSelectedMessageId(searchResults[prevIndex].id)
    scrollToMessage(searchResults[prevIndex].id)
  }
  
  // 关闭搜索
  const closeSearch = () => {
    setShowSearch(false)
    setSearchTerm('')
    setSearchResults([])
    setSelectedMessageId(null)
  }
  
  // 切换消息重点标记
  const toggleMessageImportant = (messageId: string, currentStatus: boolean = false) => {
    if (!currentConversationId) return null;
    
    // 更新重点状态
    markMessageAsImportant(currentConversationId, messageId, !currentStatus)
      .then(updatedMsg => {
        if (updatedMsg) {
          // 刷新消息和重点消息列表
          fetchMessages();
        }
      })
      .catch(error => {
        console.error('标记重点消息失败:', error);
      });
  }
  
  // 切换是否只显示重点消息
  const toggleShowImportantOnly = () => {
    if (!currentConversationId) return;
    
    setShowImportantOnly(!showImportantOnly);
    
    if (!showImportantOnly) {
      // 显示重点消息
      fetchMessages();
    } else {
      // 恢复显示所有消息
      fetchMessages();
    }
  }
  
  // 更新handleSendTextMessage函数，使用isSending代替isLoading
  const handleSendTextMessage = async () => {
    if (!message.trim() || isSending) return;
    
    // 如果没有会话ID，创建一个新会话
    if (!currentConversationId) {
      try {
        setIsSending(true);
        const conversation = await getOrCreateConversation();
        setCurrentConversationId(conversation.id);
        
        // 使用replace代替push避免创建历史记录
        router.replace(`?conversationId=${conversation.id}`, { scroll: false });
        
        // 关闭可能存在的旧连接
        closeWebSocketConnection();
        
        // 初始化WebSocket连接
        if (user) {
          console.log(`为新创建的会话初始化WebSocket连接: ${conversation.id}`);
          initializeWebSocket(user.id, conversation.id);
          
          // 等待连接建立
          await new Promise(resolve => setTimeout(resolve, 500));
        }
        
        // 延迟发送消息，确保WebSocket连接已建立
        setTimeout(async () => {
          await sendMessageWithId(conversation.id);
        }, 800);
      } catch (error) {
        console.error('创建会话失败:', error);
        setIsSending(false);
      }
    } else {
      await sendMessageWithId(currentConversationId);
    }
  };
  
  // 修改sendMessageWithId函数，使用isSending代替isLoading
  const sendMessageWithId = async (conversationId: string) => {
    try {
      setIsSending(true);
      
      // 检查WebSocket连接状态
      const wsCurrentStatus = getConnectionStatus();
      if (wsCurrentStatus !== ConnectionStatus.CONNECTED) {
        console.log(`WebSocket未连接，尝试重新连接：当前状态=${wsCurrentStatus}`);
        
        // 如果未连接，尝试初始化连接
        if (user) {
          // 关闭可能存在的旧连接
          closeWebSocketConnection();
          
          // 初始化新连接
          initializeWebSocket(user.id, conversationId);
          
          // 等待连接建立
          await new Promise(resolve => setTimeout(resolve, 300));
        }
      }
      
      // 发送用户消息
      const userMessage = await sendTextMessage(conversationId, message);
      
      // 更新本地消息列表
      setMessages(prev => [...prev, userMessage]);
      
      // 清空输入框
      setMessage('');
      
      // 滚动到底部
      scrollToBottom();
      
      // 在顾问未接管的情况下获取AI回复
      if (!isConsultantTakeover) {
        // 获取AI回复前不重置发送状态
        
        try {
          // 获取AI回复，增加超时处理
          const aiResponsePromise = getAIResponse(conversationId, userMessage);
          const timeoutPromise = new Promise<null>((_, reject) => 
            setTimeout(() => reject(new Error('获取AI回复超时')), 15000)
          );
          
          const aiResponse = await Promise.race([aiResponsePromise, timeoutPromise]);
          
          if (aiResponse) {
            // 更新本地消息列表
            setMessages(prev => [...prev, aiResponse]);
          
            // 滚动到底部
            scrollToBottom();
          }
        } catch (error) {
          console.error('获取AI回复失败:', error);
          // 可以在这里添加失败提示
        } finally {
          setIsSending(false);
        }
      } else {
        // 顾问模式下立即重置发送状态
        setIsSending(false);
      }
    } catch (error) {
      console.error('发送消息失败:', error);
      setIsSending(false);
      
      // 显示错误提示
      // 这里可以添加错误处理，如显示错误消息等
    }
  };
  
  // 修改handleSendImageMessage和handleSendVoiceMessage函数，使用isSending
  const handleSendImageMessage = async () => {
    if (!imagePreview || !currentConversationId || isSending) return;
    
    setIsSending(true);
    try {
      // 发送图片消息
      await sendImageMessage(currentConversationId, imagePreview);
      
      // 清除图片预览
      setImagePreview(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      
      // 更新消息列表，使用静默加载模式
      silentlyUpdateMessages();
    } catch (error) {
      console.error('发送图片失败:', error);
    } finally {
      setIsSending(false);
    }
  };
  
  // 修改handleSendVoiceMessage函数
  const handleSendVoiceMessage = async () => {
    if (!audioPreview || !currentConversationId || isSending) return;
    
    setIsSending(true);
    try {
      // 发送语音消息
      await sendVoiceMessage(currentConversationId, audioPreview);
      
      // 清除语音预览
      setAudioPreview(null);
      
      // 更新消息列表，使用静默加载模式
      silentlyUpdateMessages();
    } catch (error) {
      console.error('发送语音失败:', error);
    } finally {
      setIsSending(false);
    }
  };
  
  // 滚动到底部
  const scrollToBottom = () => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  };
  
  // 新消息自动滚动到底部
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight
    }
  }, [showImportantOnly ? importantMessages : messages])
  
  // 处理图片上传
  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    const reader = new FileReader()
    reader.onloadstart = () => {
      setUploadingImage(true)
    }
    reader.onload = (event) => {
      setImagePreview(event.target?.result as string)
      setUploadingImage(false)
    }
    reader.onerror = () => {
      setUploadingImage(false)
      alert('图片上传失败，请重试')
    }
    reader.readAsDataURL(file)
  }

  // 取消图片预览
  const cancelImagePreview = () => {
    setImagePreview(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }
  
  // 清理函数
  const cleanupRecording = () => {
    if (recordingTimerRef.current) {
      clearInterval(recordingTimerRef.current)
      recordingTimerRef.current = null
    }
    setIsRecording(false)
    setRecordingTime(0)
    audioChunksRef.current = []
  }
  
  // 开始录音
  const startRecording = async () => {
    try {
      // 清理之前的音频预览
      setAudioPreview(null)
      
      // 请求麦克风权限
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream)
      mediaRecorderRef.current = mediaRecorder
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data)
        }
      }
      
      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' })
        const audioUrl = URL.createObjectURL(audioBlob)
        setAudioPreview(audioUrl)
        cleanupRecording()
        
        // 停止所有音轨
        stream.getTracks().forEach(track => track.stop())
      }
      
      // 开始录制
      mediaRecorder.start()
      setIsRecording(true)
      
      // 开始计时
      recordingTimerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1)
      }, 1000)
      
    } catch (error) {
      console.error('录音失败:', error)
      alert('无法访问麦克风，请确保已授予麦克风权限')
      cleanupRecording()
    }
  }
  
  // 停止录音
  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
    }
  }
  
  // 取消录音
  const cancelRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      setAudioPreview(null)
    }
  }
  
  // 取消音频预览
  const cancelAudioPreview = () => {
    setAudioPreview(null)
  }
  
  // 格式化录音时间
  const formatRecordingTime = (seconds: number) => {
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = seconds % 60
    return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`
  }
  

  // 清理效果
  useEffect(() => {
    return () => {
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current)
      }
      
      // 如果组件卸载时还在录音，则停止录音
      if (mediaRecorderRef.current && isRecording) {
        mediaRecorderRef.current.stop()
      }
    }
  }, [isRecording])
  
  // 切换顾问接管状态
  const toggleConsultantMode = () => {
    if (!currentConversationId) return;
    
    try {
      // 切换顾问模式
      if (isConsultantTakeover) {
        // 切回AI模式
        switchBackToAI(currentConversationId)
          .then(success => {
            if (success) {
              setIsConsultantTakeover(false);
            }
            // 刷新消息
            fetchMessages();
          })
          .catch(error => {
            console.error('切回AI模式失败:', error);
          });
      } else {
        // 启用顾问模式
        takeoverConversation(currentConversationId)
          .then(success => {
            if (success) {
              setIsConsultantTakeover(true);
            }
            // 刷新消息
            fetchMessages();
          })
          .catch(error => {
            console.error('接管会话失败:', error);
          });
      }
    } catch (error) {
      console.error('切换顾问模式失败:', error);
    }
  }

  // 在组件顶部添加：
  useEffect(() => {
    // 只在首次挂载且组件确实挂载完成时兜底一次
    if (mounted.current && wsStatus == null) {
      try {
        const status = getConnectionStatus();
        setWsStatus(status);
      } catch (e) {
        setWsStatus(ConnectionStatus.DISCONNECTED);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // 在render部分中使用分组后的消息
  const messageGroups = useMemo(() => {
    const messagesToGroup = showImportantOnly ? importantMessages : messages;
    const groups: { date: string; messages: Message[] }[] = [];
    
    // 按日期分组，但不做去重处理
    messagesToGroup.forEach((msg: Message) => {
      const dateStr = formatMessageDate(msg.timestamp);
      
      // 查找或创建日期组
      let group = groups.find(g => g.date === dateStr);
      if (!group) {
        group = { date: dateStr, messages: [] };
        groups.push(group);
      }
      
      group.messages.push(msg);
    });
    
    return groups;
  }, [showImportantOnly, importantMessages, messages, formatMessageDate]);
  
  // 优化搜索功能，使用防抖处理
  const debouncedSearchChatMessages = useCallback(
    debounce((term: string) => {
      if (!term.trim() || !currentConversationId) {
        setSearchResults([]);
        setSelectedMessageId(null);
        return;
      }
      
      const normalizedTerm = term.toLowerCase();
      const results = messages.filter(msg => 
        typeof msg.content === 'string' && 
        msg.content.toLowerCase().includes(normalizedTerm) &&
        msg.type === 'text' // 只搜索文本消息
      );
      
      setSearchResults(results);
      
      // 如果有结果，选中第一条
      if (results.length > 0) {
        setSelectedMessageId(results[0].id);
        scrollToMessage(results[0].id);
      } else {
        setSelectedMessageId(null);
      }
    }, 300),
    [currentConversationId, messages]
  );
  
  // 更新搜索函数调用
  const searchChatMessages = useCallback((term: string) => {
    debouncedSearchChatMessages(term);
  }, [debouncedSearchChatMessages]);
  
  // 使用优化版的消息发送函数，删除其他同名函数
  const handleSendMessage = useCallback(async () => {
    // 防止重复发送
    if (isSending) {
      console.log('消息正在发送中，请稍候...');
      return;
    }
    
    // 根据消息类型调用相应的发送函数
    if (imagePreview) {
      await handleSendImageMessage();
    } else if (audioPreview) {
      await handleSendVoiceMessage();
    } else {
      await handleSendTextMessage();
    }
  }, [isSending, imagePreview, audioPreview, handleSendImageMessage, handleSendVoiceMessage, handleSendTextMessage]);

  // 添加防抖函数实现
  function debounce<T extends (...args: any[]) => any>(
    func: T,
    wait: number
  ): (...args: Parameters<T>) => void {
    let timeout: NodeJS.Timeout | null = null;
    
    return function(this: any, ...args: Parameters<T>) {
      const later = () => {
        timeout = null;
        func.apply(this, args);
      };
      
      if (timeout !== null) {
        clearTimeout(timeout);
      }
      timeout = setTimeout(later, wait);
    };
  }

  return (
    <div className="flex h-full flex-col">
      {/* 搜索栏 */}
      {showSearch && (
        <div className="border-b border-gray-200 bg-white p-2 shadow-sm">
          <div className="flex items-center">
            <div className="relative flex-1">
              <input
                type="text"
                value={searchTerm}
                onChange={e => {
                  setSearchTerm(e.target.value)
                  searchChatMessages(e.target.value)
                }}
                placeholder="搜索聊天记录..."
                className="w-full rounded-lg border border-gray-200 pl-10 pr-4 py-2 text-sm focus:border-orange-500 focus:outline-none"
                autoFocus
              />
              <svg
                className="absolute left-3 top-2.5 h-4 w-4 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
              {searchTerm && (
                <button
                  className="absolute right-10 top-2.5 text-gray-400 hover:text-gray-600"
                  onClick={() => {
                    setSearchTerm('')
                    setSearchResults([])
                    setSelectedMessageId(null)
                  }}
                >
                  <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              )}
            </div>
            
            <div className="ml-2 flex space-x-1">
              <div className="flex items-center ml-2 text-xs text-gray-500">
                {searchResults.length > 0 && selectedMessageId && (
                  <span>
                    {searchResults.findIndex(m => m.id === selectedMessageId) + 1}/{searchResults.length}
                  </span>
                )}
              </div>
              
              <button
                className="p-1.5 text-gray-500 hover:text-gray-700 rounded-md hover:bg-gray-100 disabled:opacity-50"
                disabled={searchResults.length === 0}
                onClick={goToPreviousSearchResult}
                title="上一个结果"
              >
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              
              <button
                className="p-1.5 text-gray-500 hover:text-gray-700 rounded-md hover:bg-gray-100 disabled:opacity-50"
                disabled={searchResults.length === 0}
                onClick={goToNextSearchResult}
                title="下一个结果"
              >
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </button>
              
              <button
                className="p-1.5 text-gray-500 hover:text-gray-700 rounded-md hover:bg-gray-100"
                onClick={closeSearch}
                title="关闭搜索"
              >
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* WebSocket连接状态指示器 */}
      {wsStatus !== ConnectionStatus.CONNECTED && (
        <div className={`px-4 py-2 text-sm text-center ${
          wsStatus === ConnectionStatus.CONNECTING ? 'bg-yellow-50 text-yellow-700' :
          wsStatus === ConnectionStatus.ERROR ? 'bg-red-50 text-red-700' :
          'bg-gray-50 text-gray-700'
        }`}>
          {wsStatus === ConnectionStatus.CONNECTING ? (
            <span className="flex items-center justify-center">
              <svg className="animate-spin -ml-1 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              正在连接服务器...
            </span>
          ) : wsStatus === ConnectionStatus.ERROR ? (
            <div className="flex items-center justify-center">
              <span>连接服务器失败</span>
              <button 
                onClick={reconnectWebSocket}
                className="ml-2 text-sm text-red-600 hover:text-red-800 underline"
              >
                重新连接
              </button>
            </div>
          ) : (
            <div className="flex items-center justify-center">
              <span>未连接到服务器</span>
              <button 
                onClick={reconnectWebSocket}
                className="ml-2 text-sm text-gray-600 hover:text-gray-800 underline"
              >
                连接
              </button>
            </div>
          )}
        </div>
      )}
      
      {/* 聊天记录 */}
      <div 
        ref={chatContainerRef}
        className="flex-1 overflow-y-auto p-4 space-y-4"
      >
        {/* 仅显示重点标记按钮 */}
        {importantMessages.length > 0 && (
          <div className="sticky top-0 z-10 mb-2 flex justify-end">
            <button
              className={`rounded-full px-3 py-1 text-xs font-medium flex items-center space-x-1 ${
                showImportantOnly 
                ? 'bg-orange-100 text-orange-700 border border-orange-300' 
                : 'bg-gray-100 text-gray-600 border border-gray-200 hover:bg-gray-200'
              }`}
              onClick={toggleShowImportantOnly}
            >
              <svg 
                className={`h-4 w-4 ${showImportantOnly ? 'text-orange-500' : 'text-gray-500'}`} 
                fill="currentColor" 
                viewBox="0 0 20 20"
              >
                <path 
                  fillRule="evenodd" 
                  d="M3.172 5.172a4 4 0 015.656 0L10 6.343l1.172-1.171a4 4 0 115.656 5.656L10 17.657l-6.828-6.829a4 4 0 010-5.656z" 
                  clipRule="evenodd" 
                />
              </svg>
              <span>{showImportantOnly ? '查看全部消息' : '仅显示重点标记'}</span>
            </button>
          </div>
        )}

        {/* 显示分组后的消息列表 */}
        {messageGroups.map((group, groupIndex) => (
          <div key={group.date} className="space-y-4">
            {/* 日期分隔符 */}
            <div className="flex items-center justify-center my-4">
              <div className="h-px flex-grow bg-gray-200"></div>
              <div className="mx-4 text-xs text-gray-500">{group.date}</div>
              <div className="h-px flex-grow bg-gray-200"></div>
            </div>
            
            {/* 当前日期组的消息 */}
            {group.messages.map(msg => (
              <ChatMessage
                key={msg.id}
                message={msg}
                isSelected={selectedMessageId === msg.id}
                searchTerm={showSearch ? searchTerm : ''}
                onToggleImportant={toggleMessageImportant}
              />
            ))}
          </div>
        ))}
        
        {showImportantOnly && importantMessages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-32 text-gray-500">
            <svg className="h-12 w-12 mb-2 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
            </svg>
            <p className="text-sm">暂无标记的重点消息</p>
            <button 
              className="mt-2 text-sm text-orange-500 hover:underline"
              onClick={() => setShowImportantOnly(false)}
            >
              返回全部消息
            </button>
          </div>
        )}
      </div>
      
      {/* FAQ快捷入口 - 替换为FAQSection组件 */}
      {showFAQ && (
        <FAQSection 
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
          insertFAQ={insertFAQ}
          closeFAQ={() => setShowFAQ(false)}
          messages={messages}
        />
      )}
      
      {/* 录音状态 */}
      {isRecording && (
        <div className="border-t border-gray-200 bg-gray-50 p-3">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-2">
              <span className="inline-block w-3 h-3 rounded-full bg-red-500 animate-pulse"></span>
              <span className="text-sm font-medium text-gray-700">正在录音 {formatRecordingTime(recordingTime)}</span>
            </div>
            <div className="flex space-x-2">
              <button 
                onClick={cancelRecording}
                className="rounded-full p-1 text-gray-500 hover:bg-gray-200"
                title="取消录音"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
              <button 
                onClick={stopRecording}
                className="rounded-full p-1 text-orange-500 hover:bg-orange-100"
                title="停止录音"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <rect x="6" y="6" width="12" height="12" rx="1" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* 音频预览 */}
      {audioPreview && !isRecording && (
        <div className="border-t border-gray-200 bg-gray-50 p-3">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-gray-700">语音预览</span>
            <button 
              onClick={cancelAudioPreview}
              className="text-gray-500 hover:text-gray-700"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <audio src={audioPreview} controls className="w-full" />
        </div>
      )}
      
      {/* 图片预览 */}
      {imagePreview && (
        <div className="border-t border-gray-200 bg-gray-50 p-3">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-gray-700">图片预览</span>
            <button 
              onClick={cancelImagePreview}
              className="text-gray-500 hover:text-gray-700"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <div className="relative">
            <img 
              src={imagePreview} 
              alt="预览图片" 
              className="max-h-40 max-w-full rounded-lg object-contain"
            />
          </div>
        </div>
      )}
      
      {/* 隐藏的文件输入 */}
      <input
        type="file"
        ref={fileInputRef}
        className="hidden"
        accept="image/*"
        onChange={handleImageUpload}
      />
      
      {/* 输入区域 */}
      <div className="border-t border-gray-200 bg-white p-4">
        <div className="flex space-x-4">
          <button 
            className={`flex-shrink-0 ${showFAQ ? 'text-orange-500' : 'text-gray-500 hover:text-gray-700'}`}
            onClick={() => setShowFAQ(!showFAQ)}
            title="常见问题"
          >
            <svg
              className="h-6 w-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </button>
          
          <button 
            className={`flex-shrink-0 ${showSearch ? 'text-orange-500' : 'text-gray-500 hover:text-gray-700'}`}
            onClick={() => setShowSearch(!showSearch)}
            title="搜索聊天记录"
          >
            <svg
              className="h-6 w-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          </button>
          
          {/* 顾问接管按钮 - 只对顾问角色显示 */}
          {isConsultant && (
            <button 
              className={`flex-shrink-0 ${isConsultantTakeover ? 'text-green-500' : 'text-gray-500 hover:text-gray-700'}`}
              onClick={toggleConsultantMode}
              title={isConsultantTakeover ? "切换回AI助手" : "顾问接管"}
            >
              <svg
                className="h-6 w-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d={isConsultantTakeover 
                    ? "M13 10V3L4 14h7v7l9-11h-7z" // 闪电图标，表示切换回AI
                    : "M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" // 用户图标，表示顾问接管
                  }
                />
              </svg>
            </button>
          )}
                    
          <button className="flex-shrink-0 text-gray-500 hover:text-gray-700" title="表情">
            <svg
              className="h-6 w-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </button>
          <button 
            className="flex-shrink-0 text-gray-500 hover:text-gray-700" 
            title="图片"
            onClick={() => fileInputRef.current?.click()}
          >
            <svg
              className="h-6 w-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
            {uploadingImage && (
              <span className="absolute w-3 h-3 rounded-full bg-orange-500 animate-ping"></span>
            )}
          </button>
          <button 
            className={`flex-shrink-0 ${isRecording ? 'text-red-500' : 'text-gray-500 hover:text-gray-700'}`}
            title="语音"
            onClick={isRecording ? stopRecording : startRecording}
          >
            <svg
              className="h-6 w-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 016 0v6a3 3 0 01-3 3z"
              />
            </svg>
          </button>
          
          <div className="flex flex-1 items-center space-x-2">
            <input
              type="text"
              value={message}
              onChange={e => setMessage(e.target.value)}
              placeholder="输入消息..."
              className="flex-1 rounded-lg border border-gray-200 px-4 py-2 focus:border-orange-500 focus:outline-none"
              disabled={isRecording || isSending}
              onKeyPress={e => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
            />
            <Button
              onClick={handleSendMessage}
              disabled={isRecording || isSending || (!message.trim() && !imagePreview && !audioPreview)}
              className={isSending ? 'opacity-70 cursor-not-allowed' : ''}
            >
              {isSending ? (
                <span className="flex items-center">
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  发送中
                </span>
              ) : '发送'}
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
} 