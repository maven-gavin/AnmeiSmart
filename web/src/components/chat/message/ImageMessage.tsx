'use client';

import React, { useState } from 'react';
import toast from 'react-hot-toast';
import { tokenManager } from '@/service/tokenManager';
import { MessageContentProps } from './ChatMessage';

export default function ImageMessage({ message, searchTerm, compact }: MessageContentProps) {
  const [imageExpanded, setImageExpanded] = useState(false);
  const [imageError, setImageError] = useState(false);

  // 确定图片URL来源
  const getImageUrl = (): string => {
    if (message.type === 'file' && message.file_info?.object_name) {
      // 对于file类型的图片，使用预览API端点
      return `/api/v1/files/preview/${encodeURIComponent(message.file_info.object_name)}`;
    } else if (typeof message.content === 'string') {
      // 对于image类型，检查content是否是MinIO直链，如果是则转换为API端点
      const content = message.content;
      if (content.includes('/chat-files/')) {
        // 提取object_name并转换为API端点
        const objectName = content.split('/chat-files/')[1];
        return `/api/v1/files/preview/${encodeURIComponent(objectName)}`;
      } else {
        return content;
      }
    }
    throw new Error('无效的图片数据');
  };

  // 渲染图片消息
  const renderImageMessage = (imageUrl: string) => {
    return (
      <div className="relative group max-w-[300px]">
        {!imageError ? (
          <>
            <img 
              src={imageUrl} 
              alt="聊天图片" 
              className="w-full h-auto max-h-60 rounded-lg cursor-pointer object-cover border border-gray-200 transition-all duration-200 group-hover:shadow-md"
              onClick={() => setImageExpanded(true)}
              onError={() => setImageError(true)}
              loading="lazy"
            />
            {/* 放大图标 - 悬浮时显示 */}
            <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-20 rounded-lg transition-all duration-200 flex items-center justify-center">
              <div className="opacity-0 group-hover:opacity-100 transition-opacity duration-200 bg-black bg-opacity-50 rounded-full p-2">
                <svg className="h-6 w-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7" />
                </svg>
              </div>
            </div>
          </>
        ) : (
          <div className="w-full h-40 bg-gray-100 rounded-lg flex items-center justify-center border border-gray-200">
            <div className="text-center text-gray-500">
              <svg className="h-12 w-12 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <p className="text-sm">图片加载失败</p>
              <button 
                onClick={() => setImageError(false)}
                className="text-xs text-blue-600 hover:text-blue-800 mt-1"
              >
                重新加载
              </button>
            </div>
          </div>
        )}
      </div>
    );
  };

  // 渲染图片预览模态框
  const renderImageModal = (imageUrl: string) => {
    if (!imageExpanded || imageError) return null;

    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-75 p-4">
        <div className="relative max-w-[90vw] max-h-[90vh]">
          {/* 关闭按钮 */}
          <button
            onClick={() => setImageExpanded(false)}
            className="absolute -top-12 right-0 text-white hover:text-gray-300 z-10 bg-black bg-opacity-50 rounded-full p-2"
          >
            <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
          
          {/* 图片 */}
          <img
            src={imageUrl}
            alt="聊天图片"
            className="max-w-full max-h-full object-contain rounded-lg shadow-2xl"
            onClick={() => setImageExpanded(false)}
          />
          
          {/* 操作栏 */}
          <div className="absolute -bottom-16 left-0 right-0 flex justify-center space-x-4">
            <button
              onClick={async () => {
                try {
                  const token = await tokenManager.getValidToken();
                  if (!token) {
                    toast.error('用户未登录，请重新登录');
                    return;
                  }
                  
                  const response = await fetch(imageUrl, {
                    method: 'GET',
                    credentials: 'include',
                    headers: {
                      'Accept': '*/*',
                      'Authorization': `Bearer ${token}`
                    }
                  });
                  
                  if (!response.ok) {
                    throw new Error(`下载失败: ${response.status}`);
                  }
                  
                  const blob = await response.blob();
                  const url = window.URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  
                  const fileName = message.file_info?.file_name || 
                                 `image_${new Date().getTime()}.jpg`;
                  a.download = fileName;
                  
                  document.body.appendChild(a);
                  a.click();
                  window.URL.revokeObjectURL(url);
                  document.body.removeChild(a);
                  
                  toast.success('图片下载成功');
                } catch (error) {
                  console.error('图片下载失败:', error);
                  toast.error('图片下载失败');
                }
              }}
              className="px-4 py-2 bg-white bg-opacity-20 text-white rounded-lg hover:bg-opacity-30 transition-all text-sm backdrop-blur-sm"
            >
              下载
            </button>
            <button
              onClick={() => {
                navigator.clipboard.writeText(imageUrl).then(() => {
                  toast.success('图片链接已复制到剪贴板');
                }).catch(() => {
                  toast.error('复制失败');
                });
              }}
              className="px-4 py-2 bg-white bg-opacity-20 text-white rounded-lg hover:bg-opacity-30 transition-all text-sm backdrop-blur-sm"
            >
              复制链接
            </button>
          </div>
        </div>
      </div>
    );
  };

  try {
    const imageUrl = getImageUrl();
    return (
      <>
        {renderImageMessage(imageUrl)}
        {renderImageModal(imageUrl)}
      </>
    );
  } catch (error) {
    return <p>图片加载失败：{error instanceof Error ? error.message : '无效的图片数据'}</p>;
  }
} 