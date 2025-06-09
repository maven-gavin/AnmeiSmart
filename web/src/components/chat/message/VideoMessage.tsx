'use client';

import React, { useState, useRef } from 'react';
import toast from 'react-hot-toast';
import { tokenManager } from '@/service/tokenManager';
import { MessageContentProps } from './ChatMessage';

export default function VideoMessage({ message, searchTerm, compact }: MessageContentProps) {
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [videoError, setVideoError] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const videoRef = useRef<HTMLVideoElement>(null);

  // 获取视频URL
  const getVideoUrl = (): string => {
    if (typeof message.content === 'string') {
      const content = message.content;
      if (content.includes('/chat-files/')) {
        const objectName = content.split('/chat-files/')[1];
        return `/api/v1/files/preview/${encodeURIComponent(objectName)}`;
      } else {
        return content;
      }
    }
    throw new Error('无效的视频数据');
  };

  // 下载视频
  const handleDownload = async () => {
    try {
      const videoUrl = getVideoUrl();
      const token = await tokenManager.getValidToken();
      if (!token) {
        toast.error('用户未登录，请重新登录');
        return;
      }
      
      const response = await fetch(videoUrl, {
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
                     `video_${new Date().getTime()}.mp4`;
      a.download = fileName;
      
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      toast.success('视频下载成功');
    } catch (error) {
      console.error('视频下载失败:', error);
      toast.error('视频下载失败');
    }
  };

  // 全屏播放
  const handleFullscreen = () => {
    if (videoRef.current) {
      if (videoRef.current.requestFullscreen) {
        videoRef.current.requestFullscreen();
      }
    }
  };

  try {
    const videoUrl = getVideoUrl();

    if (videoError) {
      return (
        <div className="w-full max-w-md h-48 bg-gray-100 rounded-lg flex items-center justify-center border border-gray-200">
          <div className="text-center text-gray-500">
            <svg className="h-12 w-12 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
            <p className="text-sm mb-2">视频加载失败</p>
            <button 
              onClick={() => setVideoError(false)}
              className="text-xs text-blue-600 hover:text-blue-800"
            >
              重新加载
            </button>
          </div>
        </div>
      );
    }

    return (
      <div className="relative group max-w-md">
        <video
          ref={videoRef}
          src={videoUrl}
          controls
          preload="metadata"
          className="w-full h-auto max-h-64 rounded-lg border border-gray-200 bg-black"
          onError={() => setVideoError(true)}
          onLoadStart={() => setIsLoading(true)}
          onCanPlay={() => setIsLoading(false)}
          onLoadedData={() => setIsLoading(false)}
          poster="" // 可以添加封面图片
        >
          您的浏览器不支持视频播放
        </video>

        {/* 加载状态 */}
        {isLoading && (
          <div className="absolute inset-0 bg-black bg-opacity-50 rounded-lg flex items-center justify-center">
            <div className="text-white text-center">
              <svg className="animate-spin h-8 w-8 mx-auto mb-2" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <p className="text-sm">视频加载中...</p>
            </div>
          </div>
        )}

        {/* 悬浮操作按钮 */}
        <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex space-x-2">
          <button
            onClick={handleFullscreen}
            className="p-2 bg-black bg-opacity-50 text-white rounded-full hover:bg-opacity-70 transition-all"
            title="全屏播放"
          >
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-5h-4m4 0v4m0-4l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
            </svg>
          </button>
          <button
            onClick={handleDownload}
            className="p-2 bg-black bg-opacity-50 text-white rounded-full hover:bg-opacity-70 transition-all"
            title="下载视频"
          >
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
          </button>
        </div>

        {/* 视频信息 */}
        {message.file_info && (
          <div className="mt-2 text-xs text-gray-500">
            <span>{message.file_info.file_name}</span>
            {message.file_info.file_size && (
              <span className="ml-2">
                ({(message.file_info.file_size / (1024 * 1024)).toFixed(1)} MB)
              </span>
            )}
          </div>
        )}
      </div>
    );
  } catch (error) {
    return (
      <div className="flex items-center space-x-2 p-3 bg-red-50 border border-red-200 rounded-lg">
        <svg className="h-5 w-5 text-red-500" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
        </svg>
        <span className="text-sm text-red-700">
          视频消息加载失败：{error instanceof Error ? error.message : '无效的视频数据'}
        </span>
      </div>
    );
  }
} 