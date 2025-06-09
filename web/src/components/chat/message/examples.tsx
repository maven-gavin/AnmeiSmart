/**
 * 聊天消息组件使用示例
 * 
 * 这个文件展示了如何使用重构后的聊天消息组件
 */

import React from 'react';
import ChatMessage from './ChatMessage';
import TextMessage from './TextMessage';
import ImageMessage from './ImageMessage';
import VoiceMessage from './VoiceMessage';
import VideoMessage from './VideoMessage';
import FileMessage from './FileMessage';
import { type Message } from '@/types/chat';

// 示例消息数据
const sampleMessages: Message[] = [
  // 文本消息
  {
    id: '1',
    content: '这是一条普通的文本消息，支持搜索高亮功能。',
    type: 'text',
    sender: {
      id: 'user1',
      name: '张三',
      type: 'user',
      avatar: '/avatars/user1.png'
    },
    conversationId: 'conv1',
    timestamp: new Date().toISOString(),
    status: 'sent'
  },
  
  // 图片消息
  {
    id: '2',
    content: '/api/v1/files/preview/image123.jpg',
    type: 'image',
    sender: {
      id: 'user2',
      name: '李四',
      type: 'user',
      avatar: '/avatars/user2.png'
    },
    conversationId: 'conv1',
    timestamp: new Date().toISOString(),
    status: 'sent',
    file_info: {
      file_name: 'screenshot.jpg',
      file_size: 1024000,
      file_type: 'image',
      mime_type: 'image/jpeg',
      file_url: '/api/v1/files/preview/image123.jpg',
      object_name: 'image123.jpg'
    }
  },
  
  // 语音消息
  {
    id: '3',
    content: '/api/v1/files/preview/voice123.mp3',
    type: 'voice',
    sender: {
      id: 'user3',
      name: '王五',
      type: 'user',
      avatar: '/avatars/user3.png'
    },
    conversationId: 'conv1',
    timestamp: new Date().toISOString(),
    status: 'sent'
  },
  
  // 视频消息
  {
    id: '4',
    content: '/api/v1/files/preview/video123.mp4',
    type: 'video',
    sender: {
      id: 'user4',
      name: '赵六',
      type: 'user',
      avatar: '/avatars/user4.png'
    },
    conversationId: 'conv1',
    timestamp: new Date().toISOString(),
    status: 'sent'
  },
  
  // 文件消息
  {
    id: '5',
    content: '',
    type: 'file',
    sender: {
      id: 'user5',
      name: '孙七',
      type: 'user',
      avatar: '/avatars/user5.png'
    },
    conversationId: 'conv1',
    timestamp: new Date().toISOString(),
    status: 'sent',
    file_info: {
      file_name: 'report.pdf',
      file_size: 2048000,
      file_type: 'document',
      mime_type: 'application/pdf',
      file_url: '/api/v1/files/download/report123.pdf',
      object_name: 'report123.pdf'
    }
  }
];

// 使用示例组件
export function ChatMessageExamples() {
  return (
    <div className="space-y-6 p-6 bg-gray-50 min-h-screen">
      <h1 className="text-2xl font-bold text-gray-800 mb-8">聊天消息组件示例</h1>
      
      {/* 1. 基础使用 - 自动分发消息类型 */}
      <section>
        <h2 className="text-lg font-semibold text-gray-700 mb-4">1. 基础使用（自动分发）</h2>
        <div className="bg-white rounded-lg p-4">
          {sampleMessages.map(message => (
            <ChatMessage 
              key={message.id}
              message={message}
              searchTerm="消息"
              showSender={true}
              compact={false}
            />
          ))}
        </div>
      </section>
      
      {/* 2. 紧凑模式 */}
      <section>
        <h2 className="text-lg font-semibold text-gray-700 mb-4">2. 紧凑模式</h2>
        <div className="bg-white rounded-lg p-4">
          {sampleMessages.slice(0, 2).map(message => (
            <ChatMessage 
              key={`compact-${message.id}`}
              message={message}
              showSender={false}
              compact={true}
            />
          ))}
        </div>
      </section>
      
      {/* 3. 直接使用特定组件 */}
      <section>
        <h2 className="text-lg font-semibold text-gray-700 mb-4">3. 直接使用特定组件</h2>
        
        {/* 文本组件 */}
        <div className="bg-white rounded-lg p-4 mb-4">
          <h3 className="text-md font-medium text-gray-600 mb-2">文本组件</h3>
          <TextMessage 
            message={sampleMessages[0]} 
            searchTerm="文本" 
            compact={false}
          />
        </div>
        
        {/* 图片组件 */}
        <div className="bg-white rounded-lg p-4 mb-4">
          <h3 className="text-md font-medium text-gray-600 mb-2">图片组件</h3>
          <ImageMessage 
            message={sampleMessages[1]} 
            compact={false}
          />
        </div>
        
        {/* 语音组件 */}
        <div className="bg-white rounded-lg p-4 mb-4">
          <h3 className="text-md font-medium text-gray-600 mb-2">语音组件</h3>
          <VoiceMessage 
            message={sampleMessages[2]} 
            compact={false}
          />
        </div>
        
        {/* 视频组件 */}
        <div className="bg-white rounded-lg p-4 mb-4">
          <h3 className="text-md font-medium text-gray-600 mb-2">视频组件</h3>
          <VideoMessage 
            message={sampleMessages[3]} 
            compact={false}
          />
        </div>
        
        {/* 文件组件 */}
        <div className="bg-white rounded-lg p-4 mb-4">
          <h3 className="text-md font-medium text-gray-600 mb-2">文件组件</h3>
          <FileMessage 
            message={sampleMessages[4]} 
            compact={false}
          />
        </div>
      </section>
      
      {/* 4. 状态示例 */}
      <section>
        <h2 className="text-lg font-semibold text-gray-700 mb-4">4. 消息状态示例</h2>
        <div className="bg-white rounded-lg p-4">
          {/* 发送中状态 */}
          <ChatMessage 
            message={{
              ...sampleMessages[0],
              id: 'pending-1',
              status: 'pending',
              localId: 'temp-1'
            }}
            showSender={true}
          />
          
          {/* 发送失败状态 */}
          <ChatMessage 
            message={{
              ...sampleMessages[0],
              id: 'failed-1',
              status: 'failed',
              error: '网络连接失败',
              canRetry: true,
              canDelete: true
            }}
            showSender={true}
          />
          
          {/* 可撤销状态 */}
          <ChatMessage 
            message={{
              ...sampleMessages[0],
              id: 'recall-1',
              status: 'sent',
              canRecall: true
            }}
            showSender={true}
          />
        </div>
      </section>
    </div>
  );
}

export default ChatMessageExamples; 