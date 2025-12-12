'use client';

import { useState, useEffect, useRef } from 'react';
import { Info } from 'lucide-react';
import { cn } from '@/service/utils';

interface InfoTooltipProps {
  content: string;
  className?: string;
  iconClassName?: string;
  contentClassName?: string;
  children?: React.ReactNode;
}

export function InfoTooltip({
  content,
  className,
  iconClassName,
  contentClassName,
  children,
}: InfoTooltipProps) {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // 点击外部关闭
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => {
        document.removeEventListener('mousedown', handleClickOutside);
      };
    }
  }, [isOpen]);

  const handleToggle = () => {
    setIsOpen(!isOpen);
  };

  return (
    <div ref={containerRef} className={cn('relative inline-flex', className)}>
      <button
        type="button"
        onClick={handleToggle}
        className={cn(
          'inline-flex items-center justify-center rounded-full text-gray-400 hover:text-gray-600 focus:outline-none',
          iconClassName
        )}
      >
        {children || <Info className="h-4 w-4" />}
      </button>
      {isOpen && (
        <div
          className={cn(
            'absolute left-0 top-8 z-50 w-64 rounded-md border bg-white px-3 py-2 text-sm text-gray-900 shadow-lg',
            contentClassName
          )}
        >
          <p>{content}</p>
        </div>
      )}
    </div>
  );
}

