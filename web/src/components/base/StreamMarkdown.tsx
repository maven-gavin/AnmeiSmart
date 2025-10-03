'use client';

import { Streamdown } from 'streamdown';
import 'katex/dist/katex.min.css';

interface StreamMarkdownProps {
  content: string;
  className?: string;
}

/**
 * 流式 Markdown 渲染组件
 * 支持实时流式显示 Markdown 内容
 * 基于 streamdown 库实现
 */
export function StreamMarkdown({ content, className = '' }: StreamMarkdownProps) {
  return (
    <div className={`streamdown-markdown prose prose-sm max-w-none ${className}`}>
      <Streamdown>{content}</Streamdown>
    </div>
  );
}

