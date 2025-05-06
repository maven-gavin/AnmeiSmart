'use client';

import { useEffect, useState, useRef } from 'react';
import { customerService } from '@/lib/customerService';
import { Message } from '@/types/chat';

// 聊天消息组件
function ChatMessage({ message }: { message: Message }) {
  const isUser = message.sender.type === 'user';
  
  return (
    <div className={`mb-4 flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && (
        <img 
          src={message.sender.avatar} 
          alt={message.sender.name}
          className="mr-3 h-8 w-8 rounded-full"
        />
      )}
      
      <div className={`max-w-[70%] rounded-lg p-3 ${
        isUser ? 'bg-orange-100 text-orange-900' : 'bg-white text-gray-800 shadow-sm'
      }`}>
        {message.type === 'text' && (
          <p className="text-sm">{message.content}</p>
        )}
        
        {message.type === 'image' && (
          <img 
            src={message.content} 
            alt="Shared image" 
            className="max-h-64 rounded-md"
          />
        )}
        
        {message.type === 'voice' && (
          <div className="flex items-center">
            <button className="mr-2 rounded-full bg-white p-2 shadow-sm">
              <svg className="h-4 w-4 text-gray-700" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
              </svg>
            </button>
            <div className="h-1 w-24 bg-gray-300">
              <div className="h-full w-1/3 bg-orange-500"></div>
            </div>
          </div>
        )}
        
        <p className="mt-1 text-right text-xs text-gray-500">
          {new Date(message.timestamp).toLocaleString('zh-CN', {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </p>
      </div>
      
      {isUser && (
        <img 
          src={message.sender.avatar} 
          alt={message.sender.name}
          className="ml-3 h-8 w-8 rounded-full"
        />
      )}
    </div>
  );
}

// 聊天快捷问题组件
function QuickQuestions({ onSelect }: { onSelect: (question: string) => void }) {
  const questions = [
    "我想了解双眼皮手术的恢复期",
    "玻尿酸填充需要多久做一次？",
    "光子嫩肤有副作用吗？",
    "医美项目有优惠活动吗？",
  ];
  
  return (
    <div className="mb-4 flex flex-wrap gap-2">
      {questions.map((question, index) => (
        <button
          key={index}
          onClick={() => onSelect(question)}
          className="rounded-full bg-orange-50 px-3 py-1 text-xs text-orange-700 hover:bg-orange-100"
        >
          {question}
        </button>
      ))}
    </div>
  );
}

export default function CustomerChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const messageEndRef = useRef<HTMLDivElement>(null);
  
  // 加载聊天历史
  useEffect(() => {
    const loadChatHistory = async () => {
      try {
        const history = await customerService.getChatHistory();
        setMessages(history);
      } catch (error) {
        console.error('加载聊天历史失败', error);
      } finally {
        setLoading(false);
      }
    };
    
    loadChatHistory();
  }, []);
  
  // 滚动到最新消息
  useEffect(() => {
    if (messageEndRef.current) {
      messageEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);
  
  // 发送消息
  const handleSendMessage = async () => {
    if (!inputValue.trim() || sending) return;
    
    try {
      setSending(true);
      
      // 发送消息并获取新消息对象
      const newMessage = await customerService.sendMessage(inputValue);
      setMessages((prev) => [...prev, newMessage]);
      setInputValue('');
      
      // 模拟AI回复
      setTimeout(async () => {
        // 随机选择一个AI回复
        const aiResponses = [
          "感谢您的咨询，我们的医生会尽快为您解答。",
          "我们已收到您的问题，稍后会有专业顾问联系您。",
          "已为您记录，是否还有其他问题需要了解？",
          "这个问题我需要咨询医生，请稍候。",
        ];
        
        const aiResponse: Message = {
          id: `m${Date.now()}`,
          content: aiResponses[Math.floor(Math.random() * aiResponses.length)],
          type: 'text',
          sender: {
            id: 'ai1',
            type: 'ai',
            name: 'AI助手',
            avatar: '/avatars/ai.png',
          },
          timestamp: new Date().toISOString(),
        };
        
        setMessages((prev) => [...prev, aiResponse]);
        setSending(false);
      }, 1000);
      
    } catch (error) {
      console.error('发送消息失败', error);
      setSending(false);
    }
  };
  
  // 处理按键事件
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };
  
  // 处理快捷问题选择
  const handleQuickQuestionSelect = (question: string) => {
    setInputValue(question);
  };
  
  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="h-12 w-12 animate-spin rounded-full border-4 border-orange-500 border-t-transparent"></div>
      </div>
    );
  }
  
  return (
    <div className="flex h-full flex-col bg-gray-50">
      {/* 聊天头部 */}
      <div className="border-b border-gray-200 bg-white p-4 shadow-sm">
        <div className="flex items-center">
          <div className="mr-3 rounded-full bg-orange-100 p-2">
            <svg className="h-6 w-6 text-orange-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
            </svg>
          </div>
          <div>
            <h2 className="text-lg font-medium text-gray-800">在线咨询</h2>
            <p className="text-sm text-gray-500">与专业顾问实时沟通</p>
          </div>
        </div>
      </div>
      
      {/* 聊天内容区 */}
      <div className="flex-1 overflow-y-auto p-4">
        {messages.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center">
            <div className="rounded-full bg-orange-100 p-4">
              <svg className="h-8 w-8 text-orange-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
            </div>
            <p className="mt-4 text-center text-gray-500">
              开始您的咨询，向我们提问任何医美相关问题
            </p>
            <QuickQuestions onSelect={handleQuickQuestionSelect} />
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))}
          </>
        )}
        <div ref={messageEndRef} />
      </div>
      
      {/* 输入区域 */}
      <div className="border-t border-gray-200 bg-white p-4">
        {messages.length > 0 && (
          <QuickQuestions onSelect={handleQuickQuestionSelect} />
        )}
        
        <div className="flex">
          <button className="mr-2 rounded-full bg-gray-100 p-2 hover:bg-gray-200">
            <svg className="h-6 w-6 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </button>
          
          <div className="relative flex-1">
            <textarea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="输入您的问题..."
              className="w-full resize-none rounded-lg border border-gray-300 py-2 pl-3 pr-10 focus:border-orange-500 focus:outline-none focus:ring-1 focus:ring-orange-500"
              rows={1}
            />
            
            <button
              onClick={handleSendMessage}
              disabled={!inputValue.trim() || sending}
              className={`absolute bottom-0 right-0 top-0 rounded-r-lg px-3 ${
                !inputValue.trim() || sending
                  ? 'cursor-not-allowed bg-gray-100 text-gray-400'
                  : 'bg-orange-500 text-white hover:bg-orange-600'
              }`}
            >
              {sending ? (
                <svg className="h-5 w-5 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              ) : (
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
} 