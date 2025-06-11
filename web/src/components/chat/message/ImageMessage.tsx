'use client';

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import toast from 'react-hot-toast';
import type { MessageContentProps } from './ChatMessage';
import { FileService } from '@/service/fileService';
import { MediaMessageContent } from '@/types/chat';

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
  const [isModalMounted, setIsModalMounted] = useState(false);

  // 提取图片对象名称 - 使用useMemo优化，适配新的消息模型
  const objectName = useMemo(() => {
    try {
      // 检查是否为媒体消息
      if (message.type === 'media') {
        const mediaContent = message.content as MediaMessageContent;
        
        // 如果有media_info，使用其中的URL
        if (mediaContent.media_info?.url) {
          const url = mediaContent.media_info.url;
          // 如果是内部文件路径，提取对象名称
          if (url.includes('/chat-files/')) {
            return url.split('/chat-files/')[1];
          }
          // 外部URL直接返回
          return url;
        }
      }
      
      throw new Error('无效的图片数据');
    } catch (error) {
      console.error('解析图片URL失败:', error);
      return null;
    }
  }, [message.type, message.content]);

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

  // 键盘事件处理 - ESC关闭模态框
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && imageExpanded) {
        setImageExpanded(false);
      }
    };

    if (imageExpanded) {
      document.addEventListener('keydown', handleKeyDown);
      // 防止页面滚动
      document.body.style.overflow = 'hidden';
      
      // 设置进入动画
      setIsModalMounted(false);
      const timer = setTimeout(() => {
        setIsModalMounted(true);
      }, 50);
      
      return () => {
        clearTimeout(timer);
      };
    } else {
      setIsModalMounted(false);
    }

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'unset';
    };
  }, [imageExpanded]);

  // 下载图片
  const downloadImage = useCallback(async () => {
    if (!authenticatedImageUrl) return;
    
    try {
      const a = document.createElement('a');
      a.href = authenticatedImageUrl;
      
      // 从media_info结构中获取文件名
      let fileName = `image_${Date.now()}.jpg`;
      if (message.type === 'media') {
        const mediaContent = message.content as MediaMessageContent;
        fileName = mediaContent.media_info?.name || fileName;
      }
      
      a.download = fileName;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      toast.success('图片下载成功');
    } catch (error) {
      console.error('图片下载失败:', error);
      toast.error('图片下载失败');
    }
  }, [authenticatedImageUrl, message.type, message.content]);

  // 复制图片链接
  const copyImageLink = useCallback(() => {
    if (message.type === 'media') {
      const mediaContent = message.content as MediaMessageContent;
      const originalUrl = mediaContent.media_info?.url || '';
      
      if (originalUrl) {
        navigator.clipboard.writeText(originalUrl).then(() => {
          toast.success('图片链接已复制到剪贴板');
        }).catch(() => {
          toast.error('复制失败');
        });
      } else {
        toast.error('无法获取图片链接');
      }
    } else {
      toast.error('无法获取图片链接');
    }
  }, [message.type, message.content]);

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
  const renderImage = () => {
    const mediaContent = message.content as MediaMessageContent;
    
    return (
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
        {/* 文本内容 - 如果存在的话，显示在图片下方 */}
        {mediaContent.text && (
          <div className={`mt-3 ${compact ? 'text-xs' : 'text-sm'} text-gray-800 break-words`}>
            {searchTerm ? (
              mediaContent.text.split(new RegExp(`(${searchTerm})`, 'gi')).map((part, index) => 
                part.toLowerCase() === searchTerm.toLowerCase() ? (
                  <mark key={index} className="bg-yellow-200 text-yellow-800 px-1 rounded">
                    {part}
                  </mark>
                ) : (
                  part
                )
              )
            ) : (
              mediaContent.text
            )}
          </div>
        )}
        
        {/* 悬浮覆盖层 - 修复点击事件被阻止的问题 */}
        <div className="absolute inset-0 bg-transparent group-hover:bg-black/20 rounded-lg transition-all duration-200 flex items-center justify-center pointer-events-none">
          <div className="opacity-0 group-hover:opacity-100 transition-opacity duration-200 bg-black/50 rounded-full p-2">
            <svg className="h-6 w-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7" />
            </svg>
          </div>
        </div>
      </div>
    );
  };

  // 渲染图片模态框
  const renderImageModal = () => {
    if (!imageExpanded || imageError || !authenticatedImageUrl) return null;

    const mediaContent = message.content as MediaMessageContent;

    const getModalClasses = () => {
      const baseClasses = "fixed inset-0 z-50 bg-black/80 backdrop-blur-sm transition-all duration-300";
      if (!isModalMounted) {
        return `${baseClasses} opacity-0`;
      }
      return `${baseClasses} opacity-100`;
    };

    const getContentClasses = () => {
      const baseClasses = "relative w-full max-w-7xl mx-auto bg-white dark:bg-gray-900 rounded-2xl shadow-2xl overflow-hidden transform transition-all duration-300";
      if (!isModalMounted) {
        return `${baseClasses} scale-95 opacity-0`;
      }
      return `${baseClasses} scale-100 opacity-100`;
    };

    return (
      <div 
        className={getModalClasses()}
        onClick={() => setImageExpanded(false)}
      >
        <div className="flex min-h-full items-center justify-center p-4">
          <div 
            className={getContentClasses()}
            onClick={(e) => e.stopPropagation()}
          >
            
            {/* 头部区域 */}
            <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
              <div className="flex items-center space-x-3">
                <img
                  src={message.sender.avatar || '/avatars/default.png'}
                  alt={message.sender.name}
                  className="w-8 h-8 rounded-full"
                />
                <div>
                  <h3 className="text-sm font-medium text-gray-900 dark:text-white">
                    {message.sender.name}
                  </h3>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {mediaContent.media_info?.name || '图片'}
                  </p>
                </div>
              </div>
              
              {/* 关闭按钮 */}
              <button
                onClick={() => setImageExpanded(false)}
                className="rounded-full p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-800 dark:hover:text-gray-300 transition-colors"
              >
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* 图片内容区域 */}
            <div className="relative bg-gray-50 dark:bg-gray-800 flex items-center justify-center min-h-[60vh] max-h-[80vh]">
              <img
                src={authenticatedImageUrl}
                alt="聊天图片"
                className="max-w-full max-h-full object-contain"
                draggable={false}
              />
              
              {/* 图片元信息 */}
              {mediaContent.media_info?.metadata && (
                <div className="absolute top-4 left-4 bg-black/50 text-white text-xs px-2 py-1 rounded-md backdrop-blur-sm">
                  {mediaContent.media_info.metadata.width} × {mediaContent.media_info.metadata.height}
                </div>
              )}
            </div>

            {/* 文本内容区域 */}
            {mediaContent.text && (
              <div className="p-4 bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700">
                <div className="text-sm text-gray-800 dark:text-gray-200 leading-relaxed">
                  {searchTerm ? (
                    mediaContent.text.split(new RegExp(`(${searchTerm})`, 'gi')).map((part, index) => 
                      part.toLowerCase() === searchTerm.toLowerCase() ? (
                        <mark key={index} className="bg-yellow-200 text-yellow-800 px-1 rounded">
                          {part}
                        </mark>
                      ) : (
                        part
                      )
                    )
                  ) : (
                    mediaContent.text
                  )}
                </div>
              </div>
            )}
            
            {/* 底部操作栏 */}
            <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700">
              <div className="flex items-center space-x-2 text-xs text-gray-500 dark:text-gray-400">
                <span>{mediaContent.media_info?.mime_type}</span>
                {mediaContent.media_info?.size_bytes && (
                  <>
                    <span>•</span>
                    <span>{(mediaContent.media_info.size_bytes / 1024).toFixed(1)} KB</span>
                  </>
                )}
              </div>
              
              <div className="flex items-center space-x-2">
                <button
                  onClick={copyImageLink}
                  className="inline-flex items-center gap-2 px-3 py-2 text-xs font-medium text-orange-600 dark:text-orange-400 bg-white dark:bg-gray-700 border border-orange-300 dark:border-orange-600 rounded-md hover:bg-orange-50 dark:hover:bg-gray-600 hover:border-orange-400 transition-colors shadow-sm"
                >
                  <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                  复制链接
                </button>
                <button
                  onClick={downloadImage}
                  className="inline-flex items-center gap-2 px-3 py-2 text-xs font-medium text-white bg-orange-500 hover:bg-orange-600 rounded-md transition-colors shadow-sm"
                >
                  <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  下载
                </button>
              </div>
            </div>
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