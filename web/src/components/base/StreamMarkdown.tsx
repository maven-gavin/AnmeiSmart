'use client';

import 'katex/dist/katex.min.css';
import dynamic from 'next/dynamic';
import { useEffect, useMemo, useRef, useState } from 'react';

const Streamdown = dynamic(
  async () => {
    const mod = await import('streamdown');
    return mod.Streamdown;
  },
  {
    ssr: false,
    loading: () => (
      <div className="text-sm text-gray-500">Markdown 渲染器加载中...</div>
    ),
  }
);

interface StreamMarkdownProps {
  content?: string;  // 正常内容（可选，向后兼容）
  normalContent?: string;  // 正常内容（新方式）
  thinkSections?: string[];  // 思考内容数组（新方式）
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
export function StreamMarkdown({ 
  content, 
  normalContent, 
  thinkSections: externalThinkSections,
  className = '' 
}: StreamMarkdownProps) {
  const [expandedThinks, setExpandedThinks] = useState<Set<number>>(new Set());
  const prevThinkSectionsLengthRef = useRef<number>(0);

  const supportsAdvancedRegex = useMemo(() => {
    // 企业微信桌面端（WebKit 605）可能不支持 lookbehind / Unicode property escapes
    // streamdown 依赖中包含 (?<=...) 和 \p{...}，不支持会直接在加载 chunk 时 SyntaxError
    try {
      // lookbehind
      // eslint-disable-next-line no-new
      new RegExp('(?<=a)b');
      // Unicode property escapes
      // eslint-disable-next-line no-new
      new RegExp('\\p{P}', 'u');
      return true;
    } catch {
      return false;
    }
  }, []);

  useEffect(() => {
    if (supportsAdvancedRegex) return;
    // 写入页面日志，便于企业微信定位（ErrorHandler 会展示）
    try {
      const key = '__anmei_client_error_logs__';
      const raw = sessionStorage.getItem(key);
      const prev = raw ? (JSON.parse(raw) as any[]) : [];
      const next = [
        ...(Array.isArray(prev) ? prev : []),
        {
          id: `${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
          time: new Date().toLocaleTimeString('zh-CN'),
          message: '检测到浏览器不支持 lookbehind/Unicode 正则特性，已禁用 streamdown，Markdown 改为纯文本渲染',
        },
      ].slice(-20);
      sessionStorage.setItem(key, JSON.stringify(next));
    } catch {
      // ignore
    }
  }, [supportsAdvancedRegex]);
  
  // 如果提供了分离的内容，直接使用；否则从 content 中解析（向后兼容）
  let processedContent: string;
  let thinkSections: string[];
  
  if (normalContent !== undefined || externalThinkSections !== undefined) {
    // 新方式：使用分离的内容
    processedContent = normalContent || '';
    thinkSections = externalThinkSections || [];
  } else {
    // 向后兼容：从 content 中解析标签
    const parsed = processSpecialTags(content || '');
    processedContent = parsed.processedContent;
    thinkSections = parsed.thinkSections;
  }
  
  // 默认展开所有思考过程（仅在新增时展开，避免流式输出时的频繁更新）
  useEffect(() => {
    const currentLength = thinkSections.length;
    const prevLength = prevThinkSectionsLengthRef.current;
    
    // 只在思考过程数量增加时才更新展开状态
    if (currentLength > prevLength) {
      setExpandedThinks(prev => {
        const newSet = new Set(prev);
        // 只展开新出现的思考过程索引
        for (let index = prevLength; index < currentLength; index++) {
          newSet.add(index);
        }
        return newSet;
      });
      prevThinkSectionsLengthRef.current = currentLength;
    }
  }, [thinkSections.length]);
  
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
          {supportsAdvancedRegex ? (
            <Streamdown>{processedContent}</Streamdown>
          ) : (
            <div className="rounded-md border border-orange-200 bg-orange-50 p-3 text-sm text-gray-800">
              <div className="mb-2 text-xs text-orange-700">
                当前浏览器不支持部分 Markdown 渲染能力，已降级为纯文本显示。
              </div>
              <pre className="whitespace-pre-wrap break-words">{processedContent}</pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

