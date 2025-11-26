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
 * 使用逐字符解析，完美处理流式传输中的未闭合标签
 */
function processSpecialTags(content: string): { processedContent: string; thinkSections: string[] } {
  const thinkSections: string[] = [];
  let processedContent = '';
  let thinkContent = '';
  let isInThinkTag = false;
  let i = 0;
  
  const OPEN_TAG = '<think>';
  const CLOSE_TAG = '</think>';
  
  while (i < content.length) {
    // 检查是否遇到开始标签
    if (!isInThinkTag && content.substring(i, i + OPEN_TAG.length) === OPEN_TAG) {
      isInThinkTag = true;
      thinkContent = '';
      i += OPEN_TAG.length;
      continue;
    }
    
    // 检查是否遇到结束标签
    if (isInThinkTag && content.substring(i, i + CLOSE_TAG.length) === CLOSE_TAG) {
      // 保存思考内容
      if (thinkContent.trim()) {
        thinkSections.push(thinkContent.trim());
      }
      isInThinkTag = false;
      thinkContent = '';
      i += CLOSE_TAG.length;
      continue;
    }
    
    // 根据当前状态追加内容
    if (isInThinkTag) {
      thinkContent += content[i];
    } else {
      processedContent += content[i];
    }
    
    i++;
  }
  
  // 如果最后还在 think 标签内（未闭合），不追加到 processedContent，避免显示未闭合标签
  // thinkContent 中的内容会在标签闭合后自动处理
  
  return { processedContent: processedContent.trim(), thinkSections };
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

