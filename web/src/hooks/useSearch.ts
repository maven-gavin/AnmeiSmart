import { useState, useCallback, useRef } from 'react'
import { type Message } from '@/types/chat'

export function useSearch(messages: Message[]) {
  const [showSearch, setShowSearch] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [searchResults, setSearchResults] = useState<Message[]>([])
  const [selectedMessageId, setSelectedMessageId] = useState<string | null>(null)
  
  const searchTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  // 防抖搜索函数
  const debouncedSearch = useCallback((term: string) => {
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current)
    }
    
    searchTimeoutRef.current = setTimeout(() => {
      if (!term.trim()) {
        setSearchResults([])
        setSelectedMessageId(null)
        return
      }
      
      const normalizedTerm = term.toLowerCase()
      const results = messages.filter(msg => 
        typeof msg.content === 'string' && 
        msg.content.toLowerCase().includes(normalizedTerm) &&
        msg.type === 'text'
      )
      
      setSearchResults(results)
      
      // 如果有结果，选中第一条
      if (results.length > 0) {
        setSelectedMessageId(results[0].id)
      } else {
        setSelectedMessageId(null)
      }
    }, 300)
  }, [messages])

  // 搜索聊天记录
  const searchChatMessages = useCallback((term: string) => {
    setSearchTerm(term)
    debouncedSearch(term)
  }, [debouncedSearch])

  // 滚动到指定消息
  const scrollToMessage = useCallback((messageId: string) => {
    setTimeout(() => {
      const messageElement = document.getElementById(`message-${messageId}`)
      const chatContainer = document.querySelector('[data-chat-container]')
      
      if (messageElement && chatContainer) {
        chatContainer.scrollTo({
          top: messageElement.offsetTop - 100,
          behavior: 'smooth'
        })
      }
    }, 100)
  }, [])

  // 切换到下一个搜索结果
  const goToNextSearchResult = useCallback(() => {
    if (searchResults.length === 0 || !selectedMessageId) return
    
    const currentIndex = searchResults.findIndex(msg => msg.id === selectedMessageId)
    const nextIndex = (currentIndex + 1) % searchResults.length
    
    setSelectedMessageId(searchResults[nextIndex].id)
    scrollToMessage(searchResults[nextIndex].id)
  }, [searchResults, selectedMessageId, scrollToMessage])

  // 切换到上一个搜索结果
  const goToPreviousSearchResult = useCallback(() => {
    if (searchResults.length === 0 || !selectedMessageId) return
    
    const currentIndex = searchResults.findIndex(msg => msg.id === selectedMessageId)
    const prevIndex = currentIndex === 0 ? searchResults.length - 1 : currentIndex - 1
    
    setSelectedMessageId(searchResults[prevIndex].id)
    scrollToMessage(searchResults[prevIndex].id)
  }, [searchResults, selectedMessageId, scrollToMessage])

  // 关闭搜索
  const closeSearch = useCallback(() => {
    setShowSearch(false)
    setSearchTerm('')
    setSearchResults([])
    setSelectedMessageId(null)
    
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current)
    }
  }, [])

  // 清除搜索
  const clearSearch = useCallback(() => {
    setSearchTerm('')
    setSearchResults([])
    setSelectedMessageId(null)
  }, [])

  return {
    showSearch,
    setShowSearch,
    searchTerm,
    searchResults,
    selectedMessageId,
    searchChatMessages,
    goToNextSearchResult,
    goToPreviousSearchResult,
    closeSearch,
    clearSearch
  }
} 