'use client';

import { Bot } from 'lucide-react';

/**
 * AI 思考中的打字指示器
 * 显示动画的点点点效果
 */
export function TypingIndicator() {
  return (
    <div className="flex items-start space-x-3">
      {/* AI 头像 */}
      <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-orange-100">
        <Bot className="h-5 w-5 text-orange-600" />
      </div>
      
      {/* 思考动画 */}
      <div className="flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-4 py-3">
        <div className="flex gap-1">
          <span 
            className="h-2 w-2 animate-bounce rounded-full bg-gray-400" 
            style={{ animationDelay: '0ms' }}
          />
          <span 
            className="h-2 w-2 animate-bounce rounded-full bg-gray-400" 
            style={{ animationDelay: '150ms' }}
          />
          <span 
            className="h-2 w-2 animate-bounce rounded-full bg-gray-400" 
            style={{ animationDelay: '300ms' }}
          />
        </div>
        <span className="text-sm text-gray-500">AI 正在思考...</span>
      </div>
    </div>
  );
}

