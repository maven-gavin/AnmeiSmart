import React, { useState } from 'react';
import { Copy, Check, ChevronDown, ChevronRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface JsonFormatterProps {
  content: string;
  className?: string;
}

export function JsonFormatter({ content, className }: JsonFormatterProps) {
  const [copied, setCopied] = useState(false);
  const [isExpanded, setIsExpanded] = useState(true);

  // 检测是否为JSON格式
  const isJson = (text: string): boolean => {
    try {
      // 尝试解析JSON
      JSON.parse(text);
      return true;
    } catch {
      // 检查是否包含JSON模式
      const jsonPattern = /^\s*[\{\[].*[\}\]]\s*$/s;
      return jsonPattern.test(text.trim());
    }
  };

  // 格式化JSON
  const formatJson = (text: string): string => {
    try {
      const parsed = JSON.parse(text);
      return JSON.stringify(parsed, null, 2);
    } catch {
      return text;
    }
  };

  // 复制到剪贴板
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('复制失败:', err);
    }
  };

  if (!isJson(content)) {
    return <span className={className}>{content}</span>;
  }

  const formattedJson = formatJson(content);

  return (
    <div className={cn("border border-gray-200 rounded-lg bg-gray-50", className)}>
      {/* JSON头部工具栏 */}
      <div className="flex items-center justify-between px-3 py-2 bg-gray-100 border-b border-gray-200 rounded-t-lg">
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsExpanded(!isExpanded)}
            className="h-6 w-6 p-0"
          >
            {isExpanded ? (
              <ChevronDown className="h-3 w-3" />
            ) : (
              <ChevronRight className="h-3 w-3" />
            )}
          </Button>
          <span className="text-xs font-medium text-gray-600">JSON</span>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleCopy}
          className="h-6 w-6 p-0"
        >
          {copied ? (
            <Check className="h-3 w-3 text-green-600" />
          ) : (
            <Copy className="h-3 w-3 text-gray-500" />
          )}
        </Button>
      </div>

      {/* JSON内容 */}
      {isExpanded && (
        <div className="p-3">
          <pre className="text-xs text-gray-800 whitespace-pre-wrap font-mono leading-relaxed overflow-x-auto">
            {formattedJson}
          </pre>
        </div>
      )}
    </div>
  );
}
