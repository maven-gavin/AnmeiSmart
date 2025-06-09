'use client';

import { useState } from 'react';
import { MediaPreview } from '@/components/chat/MediaPreview';

export default function TestMediaPreviewPage() {
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [audioPreview, setAudioPreview] = useState<string | null>(null);
  const [conversationId] = useState('test_conversation_media');
  const [messages, setMessages] = useState<string[]>([]);

  // 处理图片选择
  const handleImageSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file && file.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onload = (e) => {
        setImagePreview(e.target?.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  // 处理音频选择
  const handleAudioSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file && file.type.startsWith('audio/')) {
      const reader = new FileReader();
      reader.onload = (e) => {
        setAudioPreview(e.target?.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  // 处理图片发送 - 模拟父组件的消息创建逻辑
  const handleSendImage = (imageUrl: string) => {
    console.log('接收到图片URL:', imageUrl);
    setMessages(prev => [...prev, `图片消息已发送: ${imageUrl}`]);
    // 这里应该创建图片消息并调用实际的发送逻辑
  };

  // 处理语音发送 - 模拟父组件的消息创建逻辑
  const handleSendAudio = (audioUrl: string) => {
    console.log('接收到语音URL:', audioUrl);
    setMessages(prev => [...prev, `语音消息已发送: ${audioUrl}`]);
    // 这里应该创建语音消息并调用实际的发送逻辑
  };

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-2xl font-bold mb-6 text-center">媒体预览组件测试</h1>
        
        {/* 文件选择区域 */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">选择文件</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                选择图片
              </label>
              <input
                type="file"
                accept="image/*"
                onChange={handleImageSelect}
                className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-orange-50 file:text-orange-700 hover:file:bg-orange-100"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                选择音频
              </label>
              <input
                type="file"
                accept="audio/*"
                onChange={handleAudioSelect}
                className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-orange-50 file:text-orange-700 hover:file:bg-orange-100"
              />
            </div>
          </div>
        </div>

        {/* MediaPreview 组件测试 */}
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <div className="p-4 bg-gray-50 border-b">
            <h2 className="text-lg font-semibold">MediaPreview 组件</h2>
            <p className="text-sm text-gray-600">测试图片和语音的预览与发送功能</p>
          </div>
          
          <MediaPreview
            conversationId={conversationId}
            imagePreview={imagePreview}
            audioPreview={audioPreview}
            onCancelImage={() => setImagePreview(null)}
            onCancelAudio={() => setAudioPreview(null)}
            onSendSuccess={() => console.log('发送成功回调')}
            onUpdateMessages={() => console.log('更新消息回调')}
            onSendImage={handleSendImage}
            onSendAudio={handleSendAudio}
          />
          
          {/* 如果没有预览内容，显示提示 */}
          {!imagePreview && !audioPreview && (
            <div className="p-8 text-center text-gray-500">
              <p>请选择图片或音频文件以查看预览</p>
            </div>
          )}
        </div>

        {/* 消息日志 */}
        {messages.length > 0 && (
          <div className="bg-white rounded-lg shadow-md p-6 mt-6">
            <h2 className="text-lg font-semibold mb-4">发送日志</h2>
            <div className="space-y-2">
              {messages.map((message, index) => (
                <div key={index} className="text-sm text-gray-600 p-2 bg-gray-50 rounded">
                  {message}
                </div>
              ))}
            </div>
            <button
              onClick={() => setMessages([])}
              className="mt-4 px-4 py-2 text-sm bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
            >
              清空日志
            </button>
          </div>
        )}

        {/* 功能说明 */}
        <div className="bg-blue-50 rounded-lg p-6 mt-6">
          <h2 className="text-lg font-semibold mb-4 text-blue-900">功能说明</h2>
          <ul className="space-y-2 text-blue-800 text-sm">
            <li>• 选择图片文件后会显示预览界面</li>
            <li>• 选择音频文件后会显示音频播放器</li>
            <li>• 点击"发送"按钮会上传文件并获取URL</li>
            <li>• 上传成功后会通过回调传递给父组件</li>
            <li>• 支持取消预览和错误处理</li>
          </ul>
        </div>
      </div>
    </div>
  );
} 