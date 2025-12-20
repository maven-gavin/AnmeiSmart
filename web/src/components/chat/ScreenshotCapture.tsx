'use client';

import React, { useState } from 'react';
import html2canvas from 'html2canvas';
import { Button } from '@/components/ui/button';
import { Camera, Loader2 } from 'lucide-react';
import { toast } from 'react-hot-toast';

interface ScreenshotCaptureProps {
  onCapture: (blob: Blob) => void;
  targetElement?: HTMLElement | null;  // 可选：指定截图区域，默认截取整个页面
  className?: string;
}

export function ScreenshotCapture({ 
  onCapture, 
  targetElement,
  className 
}: ScreenshotCaptureProps) {
  const [isCapturing, setIsCapturing] = useState(false);

  const captureScreenshot = async () => {
    try {
      setIsCapturing(true);
      
      // 确定要截图的元素
      const element = targetElement || document.body;
      
      // 使用 html2canvas 截图
      const canvas = await html2canvas(element, {
        useCORS: true,
        allowTaint: false,
        background: '#ffffff',
        scale: 1,  // 可根据需要调整清晰度（1 = 标准，2 = 高清）
        logging: false,  // 禁用日志以提高性能
        windowWidth: element.scrollWidth,
        windowHeight: element.scrollHeight,
      });
      
      // 将 canvas 转换为 blob
      canvas.toBlob(
        (blob) => {
          if (blob) {
            onCapture(blob);
            toast.success('截图成功');
          } else {
            toast.error('截图失败：无法生成图片');
          }
          setIsCapturing(false);
        },
        'image/png',
        0.95  // 图片质量（0-1）
      );
    } catch (error) {
      console.error('截图失败:', error);
      toast.error('截图失败，请重试');
      setIsCapturing(false);
    }
  };

  return (
    <Button
      type="button"
      variant="ghost"
      size="sm"
      onClick={captureScreenshot}
      disabled={isCapturing}
      className={className}
      title="截图"
    >
      {isCapturing ? (
        <Loader2 className="h-4 w-4 animate-spin" />
      ) : (
        <Camera className="h-4 w-4" />
      )}
    </Button>
  );
}

