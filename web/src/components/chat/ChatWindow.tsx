'use client';

import { useState, useRef, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { type Message } from '@/types/chat'
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
  ConnectionStatus,
  getConnectionStatus
} from '@/service/chatService'
import { useAuth } from '@/contexts/AuthContext'

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

export default function ChatWindow() {
  // 当前对话ID
  const currentConversationId = '1';
  
  // 获取身份验证上下文
  const { user } = useAuth();
  
  // 基本状态
  const [message, setMessage] = useState('')
  const [showFAQ, setShowFAQ] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [messages, setMessages] = useState<Message[]>([])
  
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
  
  // 使用模拟数据服务中的聊天消息
  const currentConversationMessages = getConversationMessages(currentConversationId) || []
  
  // WebSocket连接状态
  const [wsStatus, setWsStatus] = useState<ConnectionStatus>(ConnectionStatus.DISCONNECTED);
  
  // 插入FAQ内容
  const insertFAQ = (faq: { question: string, answer: string }) => {
    setMessage(faq.question)
    setShowFAQ(false)
  }
  
  // 搜索聊天记录
  const searchChatMessages = (term: string) => {
    if (!term.trim()) {
      setSearchResults([])
      setSelectedMessageId(null)
      return
    }
    
    const normalizedTerm = term.toLowerCase()
    const results = currentConversationMessages.filter(msg => 
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
  
  // 获取当前会话消息
  const fetchMessages = () => {
    setMessages(getConversationMessages(currentConversationId))
    fetchImportantMessages()
  }
  
  // 获取重点消息
  const fetchImportantMessages = () => {
    setImportantMessages(getImportantMessages(currentConversationId))
  }
  
  // 切换消息重点标记
  const toggleMessageImportant = (messageId: string, currentStatus: boolean = false) => {
    const updatedMessage = markMessageAsImportant(currentConversationId, messageId, !currentStatus)
    
    if (updatedMessage) {
      // 更新显示
      fetchMessages()
      
      // 如果取消标记且当前在"仅显示重点"模式，则更新
      if (showImportantOnly && !updatedMessage.isImportant) {
        fetchImportantMessages()
      }
    }
  }
  
  // 切换是否只显示重点消息
  const toggleShowImportantOnly = () => {
    setShowImportantOnly(!showImportantOnly)
    // 如果切换到只显示重点，刷新重点消息列表
    if (!showImportantOnly) {
      fetchImportantMessages()
    }
  }
  
  // 发送文本消息
  const handleSendTextMessage = async () => {
    if (!message.trim()) return
    
    setIsLoading(true)
    try {
      // 发送用户消息
      const userMsg = await sendTextMessage(currentConversationId, message)
      
      // 重新获取消息列表
      fetchMessages()
      
      // 清空输入框
      setMessage('')
      
      // 如果不是顾问接管模式，则生成AI回复
      if (!isConsultantTakeover) {
        await getAIResponse(currentConversationId, userMsg)
        
        // 再次更新消息列表
        fetchMessages()
      }
    } catch (error) {
      console.error('发送消息失败:', error)
    } finally {
      setIsLoading(false)
    }
  }
  
  // 发送图片消息
  const handleSendImageMessage = async () => {
    if (!imagePreview) return
    
    setIsLoading(true)
    try {
      // 发送图片消息
      await sendImageMessage(currentConversationId, imagePreview)
      
      // 清除图片预览
      setImagePreview(null)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
      
      // 更新消息列表
      fetchMessages()
    } catch (error) {
      console.error('发送图片失败:', error)
    } finally {
      setIsLoading(false)
    }
  }
  
  // 发送语音消息
  const handleSendVoiceMessage = async () => {
    if (!audioPreview) return
    
    setIsLoading(true)
    try {
      // 发送语音消息
      await sendVoiceMessage(currentConversationId, audioPreview)
      
      // 清除语音预览
      setAudioPreview(null)
      
      // 更新消息列表
      fetchMessages()
    } catch (error) {
      console.error('发送语音失败:', error)
    } finally {
      setIsLoading(false)
    }
  }
  
  // 发送消息（统一入口）
  const handleSendMessage = async () => {
    if (isLoading) return
    
    if (audioPreview) {
      await handleSendVoiceMessage()
    } else if (imagePreview) {
      await handleSendImageMessage()
    } else if (message.trim()) {
      await handleSendTextMessage()
    }
  }
  
  // 滚动到底部
  const scrollToBottom = () => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  };
  
  // 初始化
  useEffect(() => {
    fetchMessages()
  }, [currentConversationId])
  
  // 在组件初始化时建立WebSocket连接
  useEffect(() => {
    if (user && currentConversationId) {
      // 初始化WebSocket连接
      initializeWebSocket(user.id, currentConversationId);

      // 添加消息回调
      const handleMessage = (data: any) => {
        // 处理新消息，可能需要更新UI或播放提示音等
        if (data.action === 'message') {
          // 刷新消息列表
          fetchMessages();
          // 滚动到底部
          scrollToBottom();
        }
      };

      addMessageCallback('message', handleMessage);
      
      // 监听连接状态
      const checkConnectionStatus = () => {
        setWsStatus(getConnectionStatus());
      };
      
      const statusInterval = setInterval(checkConnectionStatus, 2000);

      // 组件卸载时清理
      return () => {
        removeMessageCallback('message', handleMessage);
        clearInterval(statusInterval);
        closeWebSocketConnection();
      };
    }
  }, [user, currentConversationId]);
  
  // 新消息自动滚动到底部
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight
    }
  }, [showImportantOnly ? importantMessages : currentConversationMessages])
  
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
    if (currentConversationMessages.length === 0) {
      setRecommendedFAQs(allFAQs.slice(0, 3))
      return
    }
    
    // 获取最近的5条消息用于分析
    const recentMessages = currentConversationMessages
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
      <p className="break-words">
        {showSearch && searchTerm.trim() && typeof msg.content === 'string'
          ? highlightText(msg.content, searchTerm)
          : msg.content}
      </p>
    )
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
  }, [currentConversationMessages])
  
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
    if (isConsultantTakeover) {
      // 切换回AI助手
      if (switchBackToAI(currentConversationId)) {
        setIsConsultantTakeover(false)
        fetchMessages()
      }
    } else {
      // 顾问接管
      if (takeoverConversation(currentConversationId)) {
        setIsConsultantTakeover(true)
        fetchMessages()
      }
    }
  }

  // 显示连接状态
  const connectionStatus = getConnectionStatus();
  const isConnected = connectionStatus === ConnectionStatus.CONNECTED;

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

        {/* 显示消息列表 */}
        {(showImportantOnly ? importantMessages : currentConversationMessages).map(msg => (
          <div
            key={msg.id}
            id={`message-${msg.id}`}
            className={`${msg.isSystemMessage ? 'my-2' : 'flex items-start space-x-3'} ${
              msg.sender.type === 'user' && !msg.isSystemMessage ? 'flex-row-reverse space-x-reverse' : ''
            } ${selectedMessageId === msg.id ? 'bg-orange-50 rounded-lg -mx-2 px-2 py-1' : ''}`}
          >
            {!msg.isSystemMessage && (
              <>
                <div className="flex-shrink-0">
                  <img
                    src={msg.sender.avatar}
                    alt={msg.sender.name}
                    className="h-8 w-8 rounded-full bg-gray-100 flex items-center justify-center"
                    onError={(e) => {
                      // 如果头像加载失败，使用首字母替代
                      const target = e.target as HTMLImageElement;
                      target.onerror = null; // 防止循环错误
                      const nameInitial = msg.sender.name.charAt(0);
                      target.style.fontSize = '14px';
                      target.style.fontWeight = 'bold';
                      target.style.display = 'flex';
                      target.style.alignItems = 'center';
                      target.style.justifyContent = 'center';
                      target.style.backgroundColor = msg.sender.type === 'ai' ? '#FFB300' : '#FF9800';
                      target.style.color = '#FFFFFF';
                      target.src = 'data:image/svg+xml;charset=UTF-8,' + 
                        encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32"></svg>');
                      setTimeout(() => {
                        (target.parentNode as HTMLElement).innerHTML = `<div class="h-8 w-8 rounded-full flex items-center justify-center text-white font-bold" style="background-color: ${msg.sender.type === 'ai' ? '#FFB300' : '#FF9800'}">${nameInitial}</div>`;
                      }, 0);
                    }}
                  />
                </div>
                <div
                  className={`max-w-[70%] rounded-lg p-3 ${
                    msg.sender.type === 'user'
                      ? 'bg-orange-500 text-white'
                      : 'bg-white'
                  }`}
                >
                  <div className={`flex justify-between items-center mb-1 ${
                    msg.sender.type === 'user' ? 'text-orange-100' : 'text-gray-500'
                  }`}>
                    <span className="text-xs">
                      {msg.sender.name} · {new Date(msg.timestamp).toLocaleTimeString()}
                    </span>
                    
                    {/* 标记重点按钮 */}
                    <button 
                      className={`ml-2 ${
                        msg.sender.type === 'user' 
                          ? msg.isImportant ? 'text-red-300' : 'text-orange-200 hover:text-red-300'
                          : msg.isImportant ? 'text-red-500' : 'text-gray-300 hover:text-red-500'
                      }`}
                      onClick={() => toggleMessageImportant(msg.id, !!msg.isImportant)}
                      title={msg.isImportant ? '取消标记' : '标记为重点'}
                    >
                      <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                        <path 
                          fillRule="evenodd" 
                          d="M3.172 5.172a4 4 0 015.656 0L10 6.343l1.172-1.171a4 4 0 115.656 5.656L10 17.657l-6.828-6.829a4 4 0 010-5.656z" 
                          clipRule="evenodd" 
                        />
                      </svg>
                    </button>
                  </div>
                  {renderMessageContent(msg)}
                </div>
              </>
            )}
            
            {msg.isSystemMessage && renderMessageContent(msg)}
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
          
          {/* 顾问接管按钮 */}
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
                d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
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
              disabled={isRecording || isLoading}
              onKeyPress={e => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
            />
            <Button
              onClick={handleSendMessage}
              disabled={isRecording || isLoading || (!message.trim() && !imagePreview && !audioPreview)}
              className={isLoading ? 'opacity-70 cursor-not-allowed' : ''}
            >
              {isLoading ? (
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