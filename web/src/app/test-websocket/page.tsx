'use client';

import { useWebSocketByPage } from '@/hooks/useWebSocketByPage';
import { ChatWebSocketStatus } from '@/components/chat/ChatWebSocketStatus';
import { useEffect, useState } from 'react';
import { notFound } from 'next/navigation';

export default function TestWebSocketPage() {
  // 生产环境下不显示测试页面
  if (process.env.NODE_ENV === 'production') {
    notFound();
  }

  const {
    isConnected,
    connectionStatus,
    isEnabled,
    connectionType,
    supportedFeatures,
    lastMessage,
    connect,
    disconnect,
    config
  } = useWebSocketByPage();

  const [statusHistory, setStatusHistory] = useState<string[]>([]);

  // 记录状态变化历史
  useEffect(() => {
    const timestamp = new Date().toLocaleTimeString();
    const statusInfo = `${timestamp}: ${isConnected ? '已连接' : '未连接'} (${connectionStatus})`;
    
    setStatusHistory(prev => [...prev.slice(-9), statusInfo]);
  }, [isConnected, connectionStatus]);

  return (
    <div className="container mx-auto px-4 py-6">
      <div className="mb-4 p-4 bg-yellow-100 border border-yellow-400 rounded-lg">
        <h2 className="text-lg font-semibold text-yellow-800 mb-2">🚧 开发环境专用页面</h2>
        <p className="text-yellow-700">此页面仅在开发环境中可用，用于测试 WebSocket 架构 V2 功能。</p>
      </div>
      
      <h1 className="text-2xl font-bold mb-6">WebSocket 架构 V2 测试页面</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* 状态信息 */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-lg font-semibold mb-4">连接状态</h2>
          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
              <span className="font-medium">{isConnected ? '已连接' : '未连接'}</span>
            </div>
            <div>状态: <span className="text-blue-600">{connectionStatus}</span></div>
            <div>类型: <span className="text-purple-600">{connectionType}</span></div>
            <div>启用: <span className="text-orange-600">{isEnabled ? '是' : '否'}</span></div>
          </div>
        </div>

        {/* 功能特性 */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-lg font-semibold mb-4">支持功能</h2>
          <div className="flex flex-wrap gap-2">
            {supportedFeatures.map((feature) => (
              <span
                key={feature}
                className="px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded-full"
              >
                {feature}
              </span>
            ))}
            {supportedFeatures.length === 0 && (
              <span className="text-gray-500">无特殊功能</span>
            )}
          </div>
        </div>

        {/* 控制按钮 */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-lg font-semibold mb-4">连接控制</h2>
          <div className="space-x-3">
            <button
              onClick={connect}
              disabled={isConnected}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-400 transition-colors"
            >
              手动连接
            </button>
            <button
              onClick={disconnect}
              disabled={!isConnected}
              className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 disabled:bg-gray-400 transition-colors"
            >
              断开连接
            </button>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 transition-colors"
            >
              刷新页面
            </button>
          </div>
        </div>

        {/* 状态历史 */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-lg font-semibold mb-4">状态变化历史</h2>
          <div className="max-h-40 overflow-y-auto space-y-1">
            {statusHistory.map((status, index) => (
              <div key={index} className="text-sm text-gray-600 py-1 font-mono">
                {status}
              </div>
            ))}
          </div>
        </div>

        {/* 最近消息 */}
        <div className="bg-white p-6 rounded-lg shadow md:col-span-2">
          <h2 className="text-lg font-semibold mb-4">最近消息</h2>
          {lastMessage ? (
            <pre className="bg-gray-100 p-3 rounded text-sm overflow-auto font-mono">
              {JSON.stringify(lastMessage, null, 2)}
            </pre>
          ) : (
            <p className="text-gray-500">暂无消息</p>
          )}
        </div>

        {/* 配置信息 */}
        <div className="bg-white p-6 rounded-lg shadow md:col-span-2">
          <h2 className="text-lg font-semibold mb-4">页面配置</h2>
          {config ? (
            <pre className="bg-gray-100 p-3 rounded text-sm overflow-auto font-mono">
              {JSON.stringify(config, null, 2)}
            </pre>
          ) : (
            <p className="text-gray-500">配置加载中...</p>
          )}
        </div>
      </div>

      {/* 浮动状态指示器 */}
      <ChatWebSocketStatus />
    </div>
  );
} 