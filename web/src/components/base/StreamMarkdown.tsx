'use client';

import { Streamdown } from 'streamdown';
import 'katex/dist/katex.min.css';
import { useState } from 'react';

interface StreamMarkdownProps {
  content: string;
  className?: string;
}

/**
 * 处理 LLM 特殊标签
 * 将 <think> 等标签转换为可折叠的展示
 */
function processSpecialTags(content: string): { processedContent: string; thinkSections: string[] } {
  const thinkSections: string[] = [];
  
  // 提取所有 <think> 标签内容
  const thinkRegex = /<think>([\s\S]*?)<\/think>/gi;
  let match;
  
  while ((match = thinkRegex.exec(content)) !== null) {
    thinkSections.push(match[1].trim());
  }
  
  // 移除 <think> 标签，保留其他内容
  const processedContent = content.replace(thinkRegex, '').trim();
  
  return { processedContent, thinkSections };
}

/**
 * 流式 Markdown 渲染组件
 * 支持实时流式显示 Markdown 内容
 * 基于 streamdown 库实现
 */
export function StreamMarkdown({ content, className = '' }: StreamMarkdownProps) {
  const [expandedThinks, setExpandedThinks] = useState<Set<number>>(new Set());
  
  const { processedContent, thinkSections } = processSpecialTags(content);
  
  const toggleThink = (index: number) => {
    setExpandedThinks(prev => {
      const newSet = new Set(prev);
      if (newSet.has(index)) {
        newSet.delete(index);
      } else {
        newSet.add(index);
      }
      return newSet;
    });
  };
  
  return (
    <div>
      {/* 思考过程（可折叠） */}
      {thinkSections.length > 0 && (
        <div className="mb-3 space-y-2">
          {thinkSections.map((thinkContent, index) => (
            <div key={index} className="border border-gray-200 rounded-md bg-gray-50">
              <button
                onClick={() => toggleThink(index)}
                className="w-full px-3 py-2 text-left text-sm text-gray-600 hover:bg-gray-100 flex items-center justify-between"
              >
                <span className="flex items-center">
                  <span className="mr-2">💭</span>
                  <span className="font-medium">思考过程 {thinkSections.length > 1 ? `${index + 1}` : ''}</span>
                </span>
                <span className="text-gray-400">
                  {expandedThinks.has(index) ? '▼' : '▶'}
                </span>
              </button>
              {expandedThinks.has(index) && (
                <div className="px-3 py-2 border-t border-gray-200 text-sm text-gray-700 whitespace-pre-wrap">
                  {thinkContent}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
      
      {/* 主要内容 */}
      {processedContent && (
        <div className={`streamdown-markdown prose prose-sm max-w-none ${className}`}>
          <Streamdown>{processedContent}</Streamdown>
        </div>
      )}
    </div>
  );
}

