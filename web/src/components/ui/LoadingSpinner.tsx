'use client';

import React from 'react';
import { cn } from '@/service/utils';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  color?: 'orange' | 'blue' | 'gray';
  className?: string;
  fullScreen?: boolean;
}

export default function LoadingSpinner({
  size = 'md',
  color = 'orange',
  className,
  fullScreen = false,
}: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: 'h-4 w-4 border-2',
    md: 'h-8 w-8 border-2',
    lg: 'h-12 w-12 border-3',
  };

  const colorClasses = {
    orange: 'border-t-orange-500',
    blue: 'border-t-blue-500',
    gray: 'border-t-gray-500',
  };
  
  const spinner = (
    <div
      className={cn(
        'animate-spin rounded-full border-gray-300',
        sizeClasses[size],
        colorClasses[color],
        className
      )}
    ></div>
  );
  
  if (fullScreen) {
    return (
      <div className="fixed inset-0 flex items-center justify-center bg-gray-100 bg-opacity-75 z-50">
        <div className="flex flex-col items-center">
          {spinner}
          <p className="mt-4 text-gray-700">加载中...</p>
        </div>
      </div>
    );
  }

  return spinner;
} 