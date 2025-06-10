'use client';

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import toast from 'react-hot-toast';
import { MessageContentProps } from './ChatMessage';
import { FileService } from '@/service/fileService';
import { API_BASE_URL } from '@/config';

// 图片缓存 - 避免重复请求
const imageCache = new Map<string, string>();

// 清理过期的blob URLs
const cleanupBlobUrls = () => {
  imageCache.forEach((blobUrl) => {
    if (blobUrl.startsWith('blob:')) {
      URL.revokeObjectURL(blobUrl);
    }
  });
  imageCache.clear();
};

// 页面卸载时清理资源
if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', cleanupBlobUrls);
}

export default function ImageMessage({ message, searchTerm, compact }: MessageContentProps) {
  const [imageExpanded, setImageExpanded] = useState(false);
  const [imageError, setImageError] = useState(false);
  const [authenticatedImageUrl, setAuthenticatedImageUrl] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // 提取图片对象名称 - 使用useMemo优化
  const objectName = useMemo(() => {
    try {
      if (message.type === 'file' && message.file_info?.object_name) {
        return message.file_info.object_name;
      } else if (typeof message.content === 'string' && message.content.trim()) {
        const content = message.content.trim();
        if (content.includes('/chat-files/')) {
          return content.split('/chat-files/')[1];
        }
        return content; // 外部URL
      }
      throw new Error('无效的图片数据');
    } catch (error) {
      console.error('解析图片URL失败:', error);
      return null;
    }
  }, [message.type, message.content, message.file_info?.object_name]);

  // 创建认证图片URL - 使用useCallback优化
  const createAuthenticatedImageUrl = useCallback(async (objectName: string): Promise<string> => {
    // 检查缓存
    if (imageCache.has(objectName)) {
      return imageCache.get(objectName)!;
    }

    // 外部URL直接返回
    if (objectName.startsWith('http://') || objectName.startsWith('https://')) {
      imageCache.set(objectName, objectName);
      return objectName;
    }

    try {
      // 使用统一的文件服务获取图片
      const fileService = new FileService();
      const blob = await fileService.getFilePreviewStream(objectName);
      
      if (blob.size === 0) {
        throw new Error('接收到空的图片数据');
      }
      
      const blobUrl = URL.createObjectURL(blob);
      
      // 缓存blob URL
      imageCache.set(objectName, blobUrl);
      
      return blobUrl;
    } catch (error) {
      console.error('创建认证图片URL失败:', error);
      throw error;
    }
  }, []);

  // 加载图片 - 使用useCallback优化
  const loadImage = useCallback(async () => {
    if (!objectName) {
      setImageError(true);
      setIsLoading(false);
      return;
    }

    try {
      setIsLoading(true);
      setImageError(false);
      
      const authUrl = await createAuthenticatedImageUrl(objectName);
      setAuthenticatedImageUrl(authUrl);
    } catch (error) {
      console.error('加载图片失败:', error);
      setImageError(true);
      setAuthenticatedImageUrl(null);
    } finally {
      setIsLoading(false);
    }
  }, [objectName, createAuthenticatedImageUrl]);

  // 错误重试
  const retryLoad = useCallback(() => {
    if (objectName && imageCache.has(objectName)) {
      // 清除缓存的错误结果
      const cachedUrl = imageCache.get(objectName);
      if (cachedUrl && cachedUrl.startsWith('blob:')) {
        URL.revokeObjectURL(cachedUrl);
      }
      imageCache.delete(objectName);
    }
    loadImage();
  }, [objectName, loadImage]);

  // 组件挂载时加载图片
  useEffect(() => {
    loadImage();
  }, [loadImage]);

  // 组件卸载时清理资源
  useEffect(() => {
    return () => {
      if (authenticatedImageUrl && authenticatedImageUrl.startsWith('blob:')) {
        URL.revokeObjectURL(authenticatedImageUrl);
      }
    };
  }, [authenticatedImageUrl]);

  // 下载图片
  const downloadImage = useCallback(async () => {
    if (!authenticatedImageUrl) return;
    
    try {
      const a = document.createElement('a');
      a.href = authenticatedImageUrl;
      a.download = message.file_info?.file_name || `image_${Date.now()}.jpg`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      toast.success('图片下载成功');
    } catch (error) {
      console.error('图片下载失败:', error);
      toast.error('图片下载失败');
    }
  }, [authenticatedImageUrl, message.file_info?.file_name]);

  // 复制图片链接
  const copyImageLink = useCallback(() => {
    const originalUrl = message.content as string;
    navigator.clipboard.writeText(originalUrl).then(() => {
      toast.success('图片链接已复制到剪贴板');
    }).catch(() => {
      toast.error('复制失败');
    });
  }, [message.content]);

  // 渲染加载状态
  const renderLoadingState = () => (
    <div className="w-full h-40 bg-gray-100 rounded-lg flex items-center justify-center border border-gray-200">
      <div className="text-center text-gray-500">
        <svg className="animate-spin h-8 w-8 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <p className="text-sm">正在加载图片...</p>
      </div>
    </div>
  );

  // 渲染错误状态
  const renderErrorState = () => (
    <div className="w-full h-40 bg-gray-100 rounded-lg flex items-center justify-center border border-gray-200">
      <div className="text-center text-gray-500">
        <svg className="h-12 w-12 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 002 2z" />
        </svg>
        <p className="text-sm">图片加载失败</p>
        <button 
          onClick={retryLoad}
          className="text-xs text-blue-600 hover:text-blue-800 mt-1 px-2 py-1 rounded hover:bg-blue-50 transition-colors"
        >
          重新加载
        </button>
      </div>
    </div>
  );

  // 渲染图片
  const renderImage = () => (
    <div className="relative group max-w-[300px]">
      <img 
        src={authenticatedImageUrl!} 
        alt="聊天图片" 
        className="w-full h-auto max-h-60 rounded-lg cursor-pointer object-contain border border-gray-200 transition-all duration-200 group-hover:shadow-md bg-white"
        onClick={() => setImageExpanded(true)}
        onError={() => setImageError(true)}
        loading="lazy"
        style={{ minHeight: '100px' }}
      />
      
      {/* 悬浮覆盖层 */}
      <div className="absolute inset-0 bg-transparent group-hover:bg-black/20 rounded-lg transition-all duration-200 flex items-center justify-center">
        <div className="opacity-0 group-hover:opacity-100 transition-opacity duration-200 bg-black/50 rounded-full p-2">
          <svg className="h-6 w-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7" />
          </svg>
        </div>
      </div>
    </div>
  );

  // 渲染图片模态框
  const renderImageModal = () => {
    if (!imageExpanded || imageError || !authenticatedImageUrl) return null;

    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-75 p-4">
        <div className="relative max-w-[90vw] max-h-[90vh]">
          {/* 关闭按钮 */}
          <button
            onClick={() => setImageExpanded(false)}
            className="absolute -top-12 right-0 text-white hover:text-gray-300 z-10 bg-black bg-opacity-50 rounded-full p-2 transition-colors"
          >
            <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
          
          {/* 图片 */}
          <img
            src={authenticatedImageUrl}
            alt="聊天图片"
            className="max-w-full max-h-full object-contain rounded-lg shadow-2xl"
            onClick={() => setImageExpanded(false)}
          />
          
          {/* 操作栏 */}
          <div className="absolute -bottom-16 left-0 right-0 flex justify-center space-x-4">
            <button
              onClick={downloadImage}
              className="px-4 py-2 bg-white bg-opacity-20 text-white rounded-lg hover:bg-opacity-30 transition-all text-sm backdrop-blur-sm"
            >
              下载
            </button>
            <button
              onClick={copyImageLink}
              className="px-4 py-2 bg-white bg-opacity-20 text-white rounded-lg hover:bg-opacity-30 transition-all text-sm backdrop-blur-sm"
            >
              复制链接
            </button>
          </div>
        </div>
      </div>
    );
  };

  // 主渲染逻辑
  if (isLoading) {
    return renderLoadingState();
  }

  if (imageError || !authenticatedImageUrl) {
    return renderErrorState();
  }

  return (
    <>
      {renderImage()}
      {renderImageModal()}
    </>
  );
} 