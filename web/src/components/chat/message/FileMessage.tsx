'use client';

import React, { useState, useCallback } from 'react';
import toast from 'react-hot-toast';
import { tokenManager } from '@/service/tokenManager';
import { MessageContentProps } from './ChatMessage';
import { MediaMessageContent } from '@/types/chat';

interface FileInfo {
  file_url: string;
  file_name: string;
  file_size: number;
  file_type: string; // image, document, audio, video, archive
  mime_type: string;
  object_name?: string;
}

interface FileMessageProps extends MessageContentProps {
  fileInfo?: FileInfo;
}

export default function FileMessage({ message, searchTerm, compact, fileInfo, onRetry }: FileMessageProps) {
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);
  const [downloadError, setDownloadError] = useState<string | null>(null);
  const [isDownloading, setIsDownloading] = useState(false);

  // 从新消息结构中获取文件信息
  const getFileInfo = (): FileInfo => {
    if (fileInfo) return fileInfo;
    
    // 适配新的MediaMessageContent结构
    if (message.type === 'media') {
      const mediaContent = message.content as MediaMessageContent;
      const mediaInfo = mediaContent.media_info;
      
      if (mediaInfo) {
        return {
          file_url: mediaInfo.url,
          file_name: mediaInfo.name,
          file_size: mediaInfo.size_bytes,
          file_type: getFileTypeFromMimeType(mediaInfo.mime_type),
          mime_type: mediaInfo.mime_type,
          object_name: extractObjectName(mediaInfo.url)
        };
      }
    }
    
    throw new Error('缺少文件信息');
  };

  // 从MIME类型推断文件类型
  const getFileTypeFromMimeType = (mimeType: string): string => {
    if (mimeType.startsWith('image/')) return 'image';
    if (mimeType.startsWith('video/')) return 'video';
    if (mimeType.startsWith('audio/')) return 'audio';
    if (mimeType.includes('pdf') || mimeType.includes('document') || mimeType.includes('text')) return 'document';
    if (mimeType.includes('zip') || mimeType.includes('compressed')) return 'archive';
    return 'document';
  };

  // 从URL中提取对象名称
  const extractObjectName = (url: string): string | undefined => {
    if (url.includes('/chat-files/')) {
      return url.split('/chat-files/')[1];
    }
    return undefined;
  };

  // 格式化文件大小
  const formatFileSize = useCallback((bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }, []);

  // 获取文件类型图标
  const getFileIcon = useCallback((fileType: string, mimeType: string) => {
    const iconClass = "h-8 w-8";
    
    switch (fileType) {
      case 'image':
        return (
          <svg className={`${iconClass} text-green-500`} fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clipRule="evenodd" />
          </svg>
        );
      case 'document':
        if (mimeType === 'application/pdf') {
          return (
            <svg className={`${iconClass} text-red-500`} fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
            </svg>
          );
        }
        return (
          <svg className={`${iconClass} text-blue-500`} fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
          </svg>
        );
      case 'audio':
        return (
          <svg className={`${iconClass} text-purple-500`} fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M9.383 3.076A1 1 0 0110 4v12a1 1 0 01-1.707.707L4.586 13H2a1 1 0 01-1-1V8a1 1 0 011-1h2.586l3.707-3.707a1 1 0 011.09-.217zM15.657 6.343a1 1 0 011.414 0A9.972 9.972 0 0119 12a9.972 9.972 0 01-1.929 5.657 1 1 0 11-1.414-1.414A7.971 7.971 0 0017 12a7.971 7.971 0 00-1.343-4.243 1 1 0 010-1.414z" clipRule="evenodd" />
          </svg>
        );
      case 'video':
        return (
          <svg className={`${iconClass} text-indigo-500`} fill="currentColor" viewBox="0 0 20 20">
            <path d="M2 6a2 2 0 012-2h6a2 2 0 012 2v8a2 2 0 01-2 2H4a2 2 0 01-2-2V6zM14.553 7.106A1 1 0 0014 8v4a1 1 0 00.553.894l2 1A1 1 0 0018 13V7a1 1 0 00-1.447-.894l-2 1z" />
          </svg>
        );
      case 'archive':
        return (
          <svg className={`${iconClass} text-yellow-500`} fill="currentColor" viewBox="0 0 20 20">
            <path d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z" />
          </svg>
        );
      default:
        return (
          <svg className={`${iconClass} text-gray-500`} fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
          </svg>
        );
    }
  }, []);

  // 获取安全的下载URL
  const getDownloadUrl = useCallback((fileInfo: FileInfo) => {
    if (fileInfo.object_name) {
      return `/api/v1/files/download/${fileInfo.object_name}`;
    }
    return fileInfo.file_url;
  }, []);

  // 获取安全的预览URL
  const getPreviewUrl = useCallback((fileInfo: FileInfo) => {
    if (fileInfo.object_name) {
      return `/api/v1/files/preview/${fileInfo.object_name}`;
    }
    return fileInfo.file_url;
  }, []);

  // 处理文件下载
  const handleDownload = useCallback(async (fileInfo: FileInfo) => {
    if (isDownloading) return;
    
    setDownloadError(null);
    setIsDownloading(true);
    
    try {
      const downloadUrl = getDownloadUrl(fileInfo);
      
      // 获取认证token
      const token = await tokenManager.getValidToken();
      if (!token) {
        throw new Error('用户未登录，请重新登录');
      }
      
      const response = await fetch(downloadUrl, {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Accept': '*/*',
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!response.ok) {
        let errorMessage = `下载失败: ${response.status}`;
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorMessage;
        } catch (e) {
          // 忽略JSON解析错误
        }
        throw new Error(errorMessage);
      }
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = fileInfo.file_name;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      toast.success('文件下载成功');
    } catch (error) {
      console.error('文件下载失败:', error);
      const errorMessage = error instanceof Error ? error.message : '下载失败';
      setDownloadError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setIsDownloading(false);
    }
  }, [getDownloadUrl, isDownloading]);

  // 处理预览
  const handlePreview = useCallback(async (fileInfo: FileInfo) => {
    if (fileInfo.file_type === 'image') {
      setIsPreviewOpen(true);
    } else if (canPreview(fileInfo)) {
      try {
        // 获取认证token
        const token = await tokenManager.getValidToken();
        if (!token) {
          toast.error('用户未登录，请重新登录');
          return;
        }
        
        // 对于其他可预览的文件，在新窗口打开预览端点
        const previewUrl = getPreviewUrl(fileInfo);
        
        // 创建一个临时的带认证的预览链接
        const response = await fetch(previewUrl, {
          method: 'HEAD', // 先检查文件是否可访问
          credentials: 'include',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (!response.ok) {
          throw new Error('无法预览此文件');
        }
        
        // 如果检查通过，开始下载文件
        toast('正在准备预览，开始下载文件...', { icon: '📎' });
        handleDownload(fileInfo);
      } catch (error) {
        console.error('预览失败:', error);
        toast.error(error instanceof Error ? error.message : '预览失败');
        handleDownload(fileInfo);
      }
    } else {
      // 不支持预览的文件，触发下载
      handleDownload(fileInfo);
    }
  }, [getPreviewUrl, handleDownload]);

  // 判断是否可以预览
  const canPreview = useCallback((fileInfo: FileInfo) => {
    const previewableTypes = ['image', 'document'];
    const previewableMimeTypes = [
      'application/pdf', 
      'text/plain',
      'image/jpeg', 'image/png', 'image/gif', 'image/webp'
    ];
    
    return previewableTypes.includes(fileInfo.file_type) || 
           previewableMimeTypes.includes(fileInfo.mime_type);
  }, []);

  try {
    const currentFileInfo = getFileInfo();

    return (
      <>
        <div className={`bg-white border border-gray-200 rounded-lg ${compact ? 'p-3' : 'p-4'} max-w-sm`}>
          <div className="flex items-start space-x-3">
            {/* 文件图标 */}
            <div className="flex-shrink-0">
              {getFileIcon(currentFileInfo.file_type, currentFileInfo.mime_type)}
            </div>
            
            {/* 文件信息 */}
            <div className="flex-1 min-w-0">
              <div className={`font-medium text-gray-900 truncate ${compact ? 'text-sm' : 'text-sm'}`}>
                {currentFileInfo.file_name}
              </div>
              <div className={`text-gray-500 mt-1 ${compact ? 'text-xs' : 'text-xs'}`}>
                {formatFileSize(currentFileInfo.file_size)}
              </div>
              
              {/* 操作按钮 */}
              <div className={`flex items-center space-x-2 ${compact ? 'mt-1' : 'mt-2'}`}>
                {canPreview(currentFileInfo) && (
                  <button
                    onClick={() => handlePreview(currentFileInfo)}
                    className="text-xs text-orange-600 hover:text-orange-800 font-medium disabled:opacity-50"
                    disabled={isDownloading}
                  >
                    预览
                  </button>
                )}
                <button
                  onClick={() => handleDownload(currentFileInfo)}
                  disabled={isDownloading}
                  className="text-xs text-blue-600 hover:text-blue-800 font-medium disabled:opacity-50"
                >
                  {isDownloading ? (
                    <span className="flex items-center">
                      <svg className="animate-spin h-3 w-3 mr-1" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      下载中
                    </span>
                  ) : '下载'}
                </button>
              </div>
              
              {/* 下载错误提示 */}
              {downloadError && (
                <div className="text-xs text-red-600 mt-1">
                  {downloadError}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* 图片预览模态框 */}
        {isPreviewOpen && currentFileInfo.file_type === 'image' && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-75">
            <div className="relative max-w-4xl max-h-full p-4">
              {/* 关闭按钮 */}
              <button
                onClick={() => setIsPreviewOpen(false)}
                className="absolute top-4 right-4 z-10 text-white hover:text-gray-300"
              >
                <svg className="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
              
              {/* 图片 */}
              <img
                src={getPreviewUrl(currentFileInfo)}
                alt={currentFileInfo.file_name}
                className="max-w-full max-h-full object-contain"
                onClick={() => setIsPreviewOpen(false)}
                onError={(e) => {
                  console.error('图片预览加载失败');
                  toast.error('图片加载失败');
                  setIsPreviewOpen(false);
                }}
              />
              
              {/* 文件名和操作 */}
              <div className="absolute bottom-4 left-4 right-4 text-center">
                <div className="bg-black bg-opacity-50 text-white px-4 py-2 rounded">
                  <div className="mb-2">{currentFileInfo.file_name}</div>
                  <div className="flex justify-center space-x-4">
                    <button
                      onClick={() => handleDownload(currentFileInfo)}
                      className="px-3 py-1 bg-white bg-opacity-20 hover:bg-opacity-30 rounded text-sm transition-all"
                    >
                      下载
                    </button>
                    <button
                      onClick={() => {
                        const previewUrl = getPreviewUrl(currentFileInfo);
                        navigator.clipboard.writeText(previewUrl).then(() => {
                          toast.success('图片链接已复制到剪贴板');
                        }).catch(() => {
                          toast.error('复制失败');
                        });
                      }}
                      className="px-3 py-1 bg-white bg-opacity-20 hover:bg-opacity-30 rounded text-sm transition-all"
                    >
                      复制链接
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </>
    );
  } catch (error) {
    return (
      <div className="flex items-center space-x-2 p-3 bg-red-50 border border-red-200 rounded-lg">
        <svg className="h-5 w-5 text-red-500" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
        </svg>
        <span className="text-sm text-red-700">
          文件加载失败：{error instanceof Error ? error.message : '文件信息缺失'}
        </span>
      </div>
    );
  }
}