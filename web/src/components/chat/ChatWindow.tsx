'use client';

import { useState, useRef, useEffect, useCallback, useMemo } from 'react'
import { Button } from '@/components/ui/button'
import { type Message, type Conversation } from '@/types/chat'
import { 
  sendTextMessage, 
  sendImageMessage, 
  sendVoiceMessage,
  getAIResponse,
  getConversationMessages,
  markMessageAsImportant,
  getImportantMessages,
  takeoverConversation,
  switchBackToAI,
  isConsultantMode,
  initializeWebSocket,
  closeWebSocketConnection,
  addMessageCallback,
  removeMessageCallback,
  getConnectionStatus,
  getConversations,
  getOrCreateConversation,
  syncConsultantTakeoverStatus
} from '@/service/chatService'
// 从新的WebSocket架构导入ConnectionStatus
import { ConnectionStatus } from '@/service/websocket'
import { useAuth } from '@/contexts/AuthContext'
import { useSearchParams, useRouter } from 'next/navigation'

// 模拟完整的FAQ数据
const allFAQs = [
  { id: 'faq1', question: '双眼皮手术恢复时间?', answer: '一般1-2周基本恢复，完全恢复需1-3个月。', tags: ['双眼皮', '恢复', '手术'] },
  { id: 'faq2', question: '医美项目价格咨询', answer: '我们提供多种套餐，价格从XX起，可根据您的需求定制。', tags: ['价格', '套餐', '咨询'] },
  { id: 'faq3', question: '术后护理注意事项', answer: '术后需避免剧烈运动，保持伤口清洁，按医嘱服药。', tags: ['术后', '护理', '注意事项'] },
  { id: 'faq4', question: '玻尿酸能维持多久?', answer: '根据注射部位和产品不同，一般可维持6-18个月。', tags: ['玻尿酸', '持续时间', '效果'] },
  { id: 'faq5', question: '肉毒素注射有副作用吗?', answer: '常见副作用包括注射部位疼痛、轻微肿胀，通常数天内消退。', tags: ['肉毒素', '副作用', '注射'] },
  { id: 'faq6', question: '医美手术前需要准备什么?', answer: '术前需进行相关检查，避免服用影响凝血的药物，遵医嘱调整饮食。', tags: ['术前', '准备', '检查'] },
  { id: 'faq7', question: '哪些人不适合做医美手术?', answer: '孕妇、有严重疾病、自身免疫性疾病患者等不适合。具体需医生评估。', tags: ['禁忌', '不适合', '评估'] },
  { id: 'faq8', question: '光子嫩肤后多久可以化妆?', answer: '一般建议术后24小时内不化妆，48小时后可轻微化妆。', tags: ['光子嫩肤', '化妆', '术后'] },
];

interface ChatWindowProps {
  conversationId?: string;
}

export default function ChatWindow({ conversationId }: ChatWindowProps) {
  // 使用路由导航
  const router = useRouter();
  
  // 获取URL参数
  const searchParams = useSearchParams()
  
  // 当前对话ID - 从props或URL参数获取，如果不存在则为null
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(
    conversationId || searchParams?.get('conversationId') || null
  )
  
  // 获取身份验证上下文
  const { user } = useAuth();
  
  // 基本状态
  const [message, setMessage] = useState('')
  const [showFAQ, setShowFAQ] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [messages, setMessages] = useState<Message[]>([])
  
  // 会话数据
  const [conversations, setConversations] = useState<Conversation[]>([])
  
  // 用户角色状态
  const isCustomer = user?.currentRole === 'customer'
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
  
  // FAQ推荐状态
  const [recommendedFAQs, setRecommendedFAQs] = useState(allFAQs.slice(0, 3))
  const [searchQuery, setSearchQuery] = useState('')
  
  // WebSocket连接状态
  const [wsStatus, setWsStatus] = useState<ConnectionStatus>(ConnectionStatus.DISCONNECTED);
  
  // 添加网络错误状态
  const [networkError, setNetworkError] = useState<string | null>(null);
  
  // 使用ref追踪组件是否已挂载
  const mounted = useRef(true);
  
  // 添加消息发送状态，与通用的isLoading分开
  const [isSending, setIsSending] = useState(false);
  
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
  
  // 监听会话ID变化，重新初始化聊天和WebSocket连接
  useEffect(() => {
    // 防止首次渲染或无用户时执行
    if (!user || !currentConversationId) return;
    
    console.log(`会话ID变化，重新初始化聊天: ${currentConversationId}`);
    
    // 创建AbortController用于取消操作
    const abortController = new AbortController();
    
    // 立即设置加载状态
    setIsLoading(true);
    
    // 清空当前消息，避免显示上一个会话的消息
    setMessages([]);
    setImportantMessages([]);
    
    // 获取新会话的消息
    const loadMessages = async () => {
      try {
        // 如果已取消，不继续加载
        if (abortController.signal.aborted) return;
        
        // 先获取消息，然后再初始化WebSocket连接
        const messages = await getConversationMessages(currentConversationId);
        
        // 再次检查是否取消，避免在长时间请求后设置过时状态
        if (abortController.signal.aborted) return;
        
        // 设置消息
        setMessages(messages);
        
        // 获取重点消息
        const important = messages.filter(msg => msg.isImportant);
        setImportantMessages(important);
        
        // 检查顾问接管状态
        const isConsultantModeActive = isConsultantMode(currentConversationId);
        setIsConsultantTakeover(isConsultantModeActive);
        console.log(`会话 ${currentConversationId} 顾问接管状态: ${isConsultantModeActive}`);
        
        // 获取最新会话列表以更新上下文 (移除此处，避免重复请求)
        
        // 消息加载完成后滚动到底部
        setTimeout(() => {
          scrollToBottom();
        }, 100);

        // 仅在消息加载完成后，关闭之前的WebSocket连接并初始化新的连接
        closeWebSocketConnection();
        initializeWebSocket(user.id, currentConversationId);
      } catch (error) {
        // 如果已取消，不处理错误
        if (abortController.signal.aborted) return;
        
        if (error instanceof Error && error.message.includes('超时')) {
          console.error('获取消息超时:', error);
        } else {
          console.error('获取消息出错:', error);
        }
        setMessages([]);
      } finally {
        // 如果已取消，不设置加载状态
        if (!abortController.signal.aborted) {
          setIsLoading(false);
        }
      }
    };
    
    loadMessages();
  
    // 组件卸载或会话ID变化时关闭WebSocket连接并取消进行中的请求
    return () => {
      console.log(`会话ID变化或组件卸载，关闭WebSocket连接: ${currentConversationId}`);
      abortController.abort();
      closeWebSocketConnection();
    };
  }, [currentConversationId, user]);
  
  // 初始化聊天 - 仅在组件首次挂载时执行一次
  useEffect(() => {
    const initializeChat = async () => {
      try {
        if (!user) return;
        
        console.log('ChatWindow初始化开始...');
        
        // 从URL获取会话ID
        const conversationId = searchParams?.get('conversationId');
        
        if (conversationId) {
          // 如果URL中有会话ID，直接使用
          console.log(`使用URL中的会话ID: ${conversationId}`);
          setCurrentConversationId(conversationId);
          // 不在这里获取消息和初始化WebSocket，由会话ID监听effect处理
        } else {
          console.log('URL中未找到会话ID，获取或创建会话');
          setIsLoading(true);
          
          // 添加超时和重试处理
          const createConversationWithRetry = async (maxRetries = 3) => {
            let lastError = null;
            
            for (let attempt = 1; attempt <= maxRetries; attempt++) {
              try {
                console.log(`尝试获取或创建会话 (尝试 ${attempt}/${maxRetries})...`);
                
                // Promise.race 确保超时后不再等待
                const timeoutPromise = new Promise<Conversation>((_, reject) => {
                  setTimeout(() => reject(new Error('创建会话超时')), 10000); // 10秒超时
                });
                
                const conversation = await Promise.race<Conversation>([
                  getOrCreateConversation(),
                  timeoutPromise
                ]);
                
                console.log('成功获取或创建会话:', conversation);
                
                // 检查组件是否仍然挂载
                if (!mounted.current) {
                  console.log('组件已卸载，不更新状态');
                  return;
                }
                
                // 更新当前会话ID
                setCurrentConversationId(conversation.id);
                
                // 使用新会话ID更新URL (使用replace避免在历史记录中创建新条目)
                router.replace(`?conversationId=${conversation.id}`, { scroll: false });
                
                // 请求成功，跳出重试循环
                return;
              } catch (error: any) {
                lastError = error;
                console.error(`创建会话失败 (尝试 ${attempt}/${maxRetries}):`, error);
                
                // 如果不是最后一次尝试，则等待一段时间后重试
                if (attempt < maxRetries) {
                  const retryDelay = 1000 * attempt; // 递增延迟
                  console.log(`将在 ${retryDelay}ms 后重试...`);
                  await new Promise(resolve => setTimeout(resolve, retryDelay));
                }
              }
            }
            
            // 如果所有尝试都失败，显示错误状态
            console.error(`已重试 ${maxRetries} 次，无法创建会话`, lastError);
            
            if (mounted.current) {
              setIsLoading(false);
              setNetworkError('无法创建会话，请刷新页面重试');
            }
          };
          
          await createConversationWithRetry();
        }
      } catch (error) {
        console.error('初始化聊天时出错:', error);
        if (mounted.current) {
          setIsLoading(false);
          setNetworkError('聊天初始化失败，请刷新页面重试');
        }
      }
    };
  
    // 只在组件挂载时执行一次初始化
    initializeChat();
    
    // 组件卸载时关闭WebSocket连接
    return () => {
      console.log('ChatWindow组件卸载，关闭WebSocket连接');
      mounted.current = false;
      closeWebSocketConnection();
    };
  }, [router, searchParams, user]); // 更新依赖数组
  
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
      setNetworkError(null); // 清除之前的错误
      
      // 获取消息
      try {
        const messages = await getConversationMessages(currentConversationId);
        setMessages(messages);
        await fetchImportantMessages();
      } catch (error) {
        console.error('获取消息出错:', error);
        setNetworkError('加载消息失败，请重试');
        // 继续执行，尝试同步其他状态
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
      
      // 获取会话列表
      try {
        const convs = await getConversations();
        setConversations(convs);
      } catch (error) {
        console.error('获取会话列表出错:', error);
      }
    } catch (error) {
      console.error('获取数据出错:', error);
    } finally {
      setIsLoading(false);
    }
  };
  
  // 获取重点消息 - 更新以支持可能为null的会话ID
  const fetchImportantMessages = async () => {
    try {
      if (!currentConversationId) return;
      
      const allMessages = await getConversationMessages(currentConversationId);
      const important = allMessages.filter(msg => msg.isImportant);
      setImportantMessages(important);
    } catch (error) {
      console.error('获取重点消息出错:', error);
    }
  };
  
  // 插入FAQ内容
  const insertFAQ = (faq: { question: string, answer: string }) => {
    setMessage(faq.question)
    setShowFAQ(false)
  }
  
  // 搜索聊天记录
  const searchChatMessages = (term: string) => {
    if (!term.trim() || !currentConversationId) {
      setSearchResults([])
      setSelectedMessageId(null)
      return
    }
    
    const normalizedTerm = term.toLowerCase()
    const results = messages.filter(msg => 
      typeof msg.content === 'string' && 
      msg.content.toLowerCase().includes(normalizedTerm) &&
      msg.type === 'text' // 只搜索文本消息
    )
    
    setSearchResults(results)
    
    // 如果有结果，选中第一条
    if (results.length > 0) {
      setSelectedMessageId(results[0].id)
      scrollToMessage(results[0].id)
    } else {
      setSelectedMessageId(null)
    }
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
  
  // 高亮搜索文本
  const highlightText = (text: string, searchTerm: string) => {
    if (!searchTerm.trim() || !text) return text
    
    const parts = text.split(new RegExp(`(${searchTerm})`, 'gi'))
    
    return (
      <>
        {parts.map((part, index) => 
          part.toLowerCase() === searchTerm.toLowerCase() 
            ? <span key={index} className="bg-yellow-200 text-gray-900">{part}</span> 
            : part
        )}
      </>
    )
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
    const updatedMessage = markMessageAsImportant(currentConversationId, messageId, !currentStatus);
    
    if (updatedMessage) {
      // 刷新消息和重点消息列表
      fetchMessages();
      fetchImportantMessages();
    }
  }
  
  // 切换是否只显示重点消息
  const toggleShowImportantOnly = () => {
    if (!currentConversationId) return;
    
    setShowImportantOnly(!showImportantOnly);
    
    if (!showImportantOnly) {
      // 显示重点消息
      fetchImportantMessages();
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
      silentFetchMessages();
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
      silentFetchMessages();
    } catch (error) {
      console.error('发送语音失败:', error);
    } finally {
      setIsSending(false);
    }
  };
  
  // 修改handleSendMessage函数
  const handleSendMessage = async () => {
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
  };
  
  // 滚动到底部
  const scrollToBottom = () => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  };
  
  // 监听WebSocket状态
  useEffect(() => {
    // 检查连接状态
    const checkConnectionStatus = () => {
      const status = getConnectionStatus();
      const previousStatus = wsStatus;
      setWsStatus(status);
      
      // 如果WebSocket从断开到已连接，主动刷新消息，但不显示加载状态
      if (status === ConnectionStatus.CONNECTED && previousStatus !== ConnectionStatus.CONNECTED) {
        console.log(`WebSocket重新连接成功，自动刷新消息，会话ID: ${currentConversationId}`);
        if (currentConversationId) {
          // 使用静默加载方式，不设置加载状态
          silentFetchMessages();
        }
      }
    };
    
    const statusInterval = setInterval(checkConnectionStatus, 3000);
    checkConnectionStatus(); // 立即检查一次
    
    // 组件卸载时清理
    return () => {
      clearInterval(statusInterval);
    };
  }, [currentConversationId]); // 依赖项中不包含wsStatus，避免循环依赖
  
  // 静默获取消息函数，不设置加载状态
  const silentFetchMessages = async () => {
    try {
      if (!currentConversationId) return;
      
      // 不设置加载状态，避免显示"发送中"
      
      // 获取消息
      try {
        const messages = await getConversationMessages(currentConversationId);
        setMessages(messages);
        
        // 获取重点消息
        const important = messages.filter(msg => msg.isImportant);
        setImportantMessages(important);
        
        // 也尝试同步顾问接管状态，但忽略错误
        try {
          const isConsultantModeActive = await syncConsultantTakeoverStatus(currentConversationId);
          setIsConsultantTakeover(isConsultantModeActive);
        } catch (error) {
          console.error('同步顾问状态失败:', error);
        }
      } catch (error) {
        console.error('静默获取消息出错:', error);
      }
    } catch (error) {
      console.error('静默获取数据出错:', error);
    }
  };
  
  // 重新连接WebSocket的函数 - 为了在组件其他部分访问
  const reconnectWebSocket = useCallback(() => {
    if (user && currentConversationId) {
      console.log(`手动重新连接WebSocket: 用户ID=${user.id}, 会话ID=${currentConversationId}`);
      initializeWebSocket(user.id, currentConversationId);
    }
  }, [user, currentConversationId]);
  
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
  
  // 搜索FAQ
  const searchFAQs = (query: string) => {
    if (!query.trim()) {
      // 如果搜索词为空，则基于最近的对话内容智能推荐
      recommendFAQsBasedOnChat()
      return
    }
    
    // 根据关键词过滤FAQ
    const normalizedQuery = query.toLowerCase()
    const filtered = allFAQs.filter(faq => 
      faq.question.toLowerCase().includes(normalizedQuery) || 
      faq.answer.toLowerCase().includes(normalizedQuery) ||
      faq.tags.some(tag => tag.toLowerCase().includes(normalizedQuery))
    )
    
    setRecommendedFAQs(filtered.length > 0 ? filtered : allFAQs.slice(0, 3))
  }
  
  // 基于聊天记录推荐FAQ
  const recommendFAQsBasedOnChat = () => {
    if (messages.length === 0) {
      setRecommendedFAQs(allFAQs.slice(0, 3))
      return
    }
    
    // 获取最近的5条消息用于分析
    const recentMessages = messages
      .slice(-5)
      .map(msg => msg.content)
      .join(' ')
      .toLowerCase()
    
    // 分析消息内容，匹配关键词与FAQ
    const scoredFAQs = allFAQs.map(faq => {
      let score = 0
      
      // 检查问题是否匹配
      if (recentMessages.includes(faq.question.toLowerCase())) {
        score += 5
      }
      
      // 检查标签是否匹配
      faq.tags.forEach(tag => {
        if (recentMessages.includes(tag.toLowerCase())) {
          score += 3
        }
      })
      
      // 内容匹配度
      const answerWords = faq.answer.toLowerCase().split(/\s+/)
      answerWords.forEach(word => {
        if (word.length > 3 && recentMessages.includes(word)) {
          score += 1
        }
      })
      
      return { ...faq, score }
    })
    
    // 按匹配分数排序，选择前3个
    const topFAQs = scoredFAQs
      .sort((a, b) => b.score - a.score)
      .slice(0, 5)
      .map(({ id, question, answer, tags }) => ({ id, question, answer, tags }))
    
    setRecommendedFAQs(topFAQs.length > 0 ? topFAQs : allFAQs.slice(0, 3))
  }
  
  // 渲染消息内容
  const renderMessageContent = (msg: Message) => {
    // 系统消息展示
    if (msg.isSystemMessage) {
      return (
        <div className="text-center py-1 px-2 bg-gray-100 rounded-full text-xs text-gray-500">
          {msg.content}
        </div>
      )
    }
    
    // 图片消息展示
    if (msg.type === 'image' && typeof msg.content === 'string') {
      return (
        <img 
          src={msg.content} 
          alt="聊天图片" 
          className="max-w-full max-h-60 rounded-md"
          onClick={() => window.open(msg.content, '_blank')}
        />
      )
    // 语音消息展示  
    } else if (msg.type === 'voice' && typeof msg.content === 'string') {
      return (
        <div className="flex items-center space-x-2">
          <audio src={msg.content} controls className="max-w-full" controlsList="nodownload" />
          <span className="text-xs opacity-70">语音消息</span>
        </div>
      )
    }
    
    // 文本消息处理，支持高亮搜索词
    return (
      <p className="break-words whitespace-pre-line">
        {showSearch && searchTerm.trim() && typeof msg.content === 'string'
          ? highlightText(msg.content, searchTerm)
          : msg.content}
      </p>
    )
  }
  
  // 获取发送者名称和头像
  const getSenderInfo = (msg: Message) => {
    // 根据消息类型设置默认值
    let name = msg.sender.name || '未知用户';
    let avatar = msg.sender.avatar || '/avatars/default.png';
    let isSelf = false;
    
    // 首先检查是否是当前用户发送的消息，不管角色是什么
    if (user && msg.sender.id === user.id) {
      name = '我';
      isSelf = true;
      avatar = user.avatar || '/avatars/user.png';
      return { name, avatar, isSelf };
    }
    
    // 如果不是当前用户，再根据角色类型处理
    if (msg.sender.type === 'ai') {
      name = 'AI助手';
      avatar = '/avatars/ai.png';
    } else if (msg.sender.type === 'consultant') {
      name = msg.sender.name || '顾问';
      avatar = msg.sender.avatar || '/avatars/consultant1.png';
    } else if (msg.sender.type === 'doctor') {
      name = msg.sender.name || '医生';
      avatar = msg.sender.avatar || '/avatars/doctor1.png';
    } else if (msg.sender.type === 'customer' || msg.sender.type === 'user') {
      // 处理客户/用户消息
      const conversation = conversations.find(c => c.id === currentConversationId);
      
      if (isCustomer) {
        // 顾客视角 - 这里已经在上面处理过自己发送的消息了，所以这里处理的是其他顾客
        name = msg.sender.name || conversation?.user.name || '未知用户';
        avatar = msg.sender.avatar || conversation?.user.avatar || '/avatars/user.png';
      } else if (conversation) {
        // 顾问视角 - 优先使用消息中的发送者名称，再使用会话中的用户名称
        name = msg.sender.name || conversation.user.name || '未知用户';
        avatar = msg.sender.avatar || conversation.user.avatar || '/avatars/user.png';
      }
    }
    
    return { name, avatar, isSelf };
  }
  
  // 监听消息变化，自动推荐FAQ
  useEffect(() => {
    if (message.trim().length > 3) {
      searchFAQs(message)
    }
  }, [message])
  
  // 初始化时基于对话智能推荐FAQ
  useEffect(() => {
    recommendFAQsBasedOnChat()
  }, [messages])
  
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
        const success = switchBackToAI(currentConversationId);
        if (success) {
          setIsConsultantTakeover(false);
      }
    } else {
        // 启用顾问模式
        const success = takeoverConversation(currentConversationId);
        if (success) {
          setIsConsultantTakeover(true);
        }
      }
      
      // 刷新消息
      fetchMessages();
    } catch (error) {
      console.error('切换顾问模式失败:', error);
    }
  }

  // 显示连接状态
  const connectionStatus = getConnectionStatus();
  const isConnected = connectionStatus === ConnectionStatus.CONNECTED;

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
  }, [showImportantOnly, importantMessages, messages]);

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
      
      {/* 网络错误提示 */}
      {networkError && (
        <div className="mx-4 my-2 rounded-md bg-red-50 p-3 text-center">
          <p className="text-sm text-red-600 mb-2">{networkError}</p>
          <div className="flex justify-center space-x-2">
            <button 
              onClick={() => {
                setNetworkError(null);
                if (currentConversationId) {
                  fetchMessages();
                } else {
                  // 重新尝试获取会话
                  router.replace('/customer/chat');
                }
              }}
              className="px-3 py-1 text-xs font-medium text-red-600 bg-red-100 rounded-md hover:bg-red-200"
            >
              重新加载
            </button>
            {!currentConversationId && (
              <button
                onClick={() => router.push('/')}
                className="px-3 py-1 text-xs font-medium text-gray-600 bg-gray-100 rounded-md hover:bg-gray-200"
              >
                返回首页
              </button>
            )}
          </div>
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
            {group.messages.map(msg => {
              const { name, avatar, isSelf } = getSenderInfo(msg);
              
              return (
                <div
                  key={msg.id}
                  id={`message-${msg.id}`}
                  className={`flex ${isSelf ? 'justify-end' : 'justify-start'} items-end space-x-2 ${
                    selectedMessageId === msg.id ? 'bg-yellow-50 -mx-2 px-2 py-1 rounded-lg' : ''
                  }`}
                >
                  {/* 非自己发送的消息显示头像 */}
                  {!isSelf && (
                    <img 
                      src={avatar} 
                      alt={name} 
                      className="h-8 w-8 rounded-full"
                      onError={(e) => {
                        const target = e.target as HTMLImageElement;
                        target.onerror = null;
                        const nameInitial = name.charAt(0);
                        target.style.display = 'flex';
                        target.style.backgroundColor = '#FF9800';
                        target.style.color = '#FFFFFF';
                        target.style.justifyContent = 'center';
                        target.style.alignItems = 'center';
                        target.src = 'data:image/svg+xml;charset=UTF-8,' + 
                          encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32"></svg>');
                        setTimeout(() => {
                          target.parentElement!.innerHTML = `<div class="h-8 w-8 rounded-full flex items-center justify-center text-white text-sm font-bold" style="background-color: #FF9800">${nameInitial}</div>`;
                        }, 0);
                      }}
                    />
                  )}
                  
                  <div className={`flex max-w-[75%] flex-col ${isSelf ? 'items-end' : 'items-start'}`}>
                    {/* 发送者名称 */}
                    <span className="mb-1 text-xs text-gray-500">{name}</span>
                    
                    {/* 消息内容气泡 */}
                    <div 
                      className={`relative rounded-lg p-3 ${
                        isSelf
                          ? 'bg-orange-500 text-white'
                          : msg.sender.type === 'ai'
                            ? 'bg-gray-100 text-gray-800'
                            : 'bg-white border border-gray-200 text-gray-800'
                      }`}
                    >
                      {renderMessageContent(msg)}
                      
                      {/* 重点标记 */}
                      <button
                        onClick={() => toggleMessageImportant(msg.id, msg.isImportant)}
                        className={`absolute -right-1.5 -top-1.5 rounded-full p-0.5 ${
                          msg.isImportant ? 'bg-yellow-400 text-white' : 'bg-gray-200 text-gray-500'
                        }`}
                      >
                          <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                            <path 
                              fillRule="evenodd" 
                              d="M3.172 5.172a4 4 0 015.656 0L10 6.343l1.172-1.171a4 4 0 115.656 5.656L10 17.657l-6.828-6.829a4 4 0 010-5.656z" 
                              clipRule="evenodd" 
                            />
                        </svg>
                      </button>
                      
                      {/* 消息时间 */}
                      <div className={`mt-1 text-right text-xs ${isSelf ? 'text-white text-opacity-75' : 'text-gray-500'}`}>
                        {new Date(msg.timestamp).toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'})}
                      </div>
                    </div>
                  </div>
                  
                  {/* 自己发送的消息显示头像 */}
                  {isSelf && (
                    <img 
                      src={avatar} 
                      alt={name} 
                      className="h-8 w-8 rounded-full"
                      onError={(e) => {
                        const target = e.target as HTMLImageElement;
                        target.onerror = null;
                        const nameInitial = name.charAt(0);
                        target.style.display = 'flex';
                        target.style.backgroundColor = '#FF9800';
                        target.style.color = '#FFFFFF';
                        target.style.justifyContent = 'center';
                        target.style.alignItems = 'center';
                        target.src = 'data:image/svg+xml;charset=UTF-8,' + 
                          encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32"></svg>');
                        setTimeout(() => {
                          target.parentElement!.innerHTML = `<div class="h-8 w-8 rounded-full flex items-center justify-center text-white text-sm font-bold" style="background-color: #FF9800">${nameInitial}</div>`;
                        }, 0);
                      }}
                    />
                  )}
                </div>
              );
            })}
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
      
      {/* FAQ快捷入口 */}
      {showFAQ && (
        <div className="border-t border-gray-200 bg-gray-50 p-3">
          <div className="flex justify-between items-center mb-2">
            <div className="text-sm font-medium text-gray-700">常见问题</div>
            <button 
              onClick={() => setShowFAQ(false)}
              className="text-gray-500 hover:text-gray-700"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          
          {/* FAQ搜索 */}
          <div className="mb-3">
            <div className="relative">
              <input
                type="text"
                value={searchQuery}
                onChange={e => {
                  setSearchQuery(e.target.value)
                  searchFAQs(e.target.value)
                }}
                placeholder="搜索常见问题..."
                className="w-full rounded-lg border border-gray-200 pl-10 pr-4 py-2 text-sm focus:border-orange-500 focus:outline-none"
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
              {searchQuery && (
                <button
                  className="absolute right-3 top-2.5 text-gray-400 hover:text-gray-600"
                  onClick={() => {
                    setSearchQuery('')
                    recommendFAQsBasedOnChat()
                  }}
                >
                  <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              )}
            </div>
          </div>
          
          <div className="flex flex-col gap-2">
            {recommendedFAQs.length > 0 ? (
              recommendedFAQs.map(faq => (
                <button
                  key={faq.id}
                  className="rounded-lg border border-orange-200 bg-white px-3 py-2 text-left text-sm text-gray-700 hover:bg-orange-50"
                  onClick={() => insertFAQ(faq)}
                >
                  <p className="font-medium text-orange-700">{faq.question}</p>
                  <p className="mt-1 text-xs text-gray-500 line-clamp-1">{faq.answer}</p>
                </button>
              ))
            ) : (
              <div className="text-center py-3 text-gray-500 text-sm">
                未找到相关问题，请尝试其他关键词
              </div>
            )}
          </div>
          
          {/* 查看全部FAQ */}
          <button 
            className="mt-3 text-sm text-orange-600 hover:text-orange-700 font-medium flex items-center justify-center w-full"
            onClick={() => {
              // 这里可以跳转到完整FAQ页面或展开更多FAQ
              setSearchQuery('')
              setRecommendedFAQs(allFAQs)
            }}
          >
            <span>查看全部常见问题</span>
            <svg className="h-4 w-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>
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