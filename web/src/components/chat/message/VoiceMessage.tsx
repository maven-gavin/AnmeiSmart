'use client';

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { MessageContentProps } from './ChatMessage';
import { MediaMessageContent } from '@/types/chat';
import { FileService } from '@/service/fileService';

export default function VoiceMessage({ message, searchTerm, compact, onRetry }: MessageContentProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [duration, setDuration] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);
  const [authenticatedAudioUrl, setAuthenticatedAudioUrl] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement>(null);

  // 调试：输出消息信息（可选）
  // console.log('VoiceMessage 渲染:', {
  //   messageType: message.type,
  //   messageContent: message.content,
  //   messageId: message.id
  // });

  // 获取对象名称
  const getObjectName = (): string | null => {
    if (message.type === 'media') {
      const mediaContent = message.content as MediaMessageContent;
      const mediaInfo = mediaContent.media_info;
      
      console.log('解析语音URL:', { mediaInfo });
      
      if (mediaInfo?.url) {
        // 如果是内部文件路径，提取对象名称
        if (mediaInfo.url.includes('/chat-files/')) {
          const objectName = mediaInfo.url.split('/chat-files/')[1];
          console.log('提取对象名称:', { originalUrl: mediaInfo.url, objectName });
          return objectName;
        }
        // 外部URL，返回完整URL
        console.log('使用外部URL:', mediaInfo.url);
        return mediaInfo.url;
      }
    }
    
    console.error('语音数据无效:', { messageType: message.type, content: message.content });
    return null;
  };

  // 创建认证的音频URL
  const createAuthenticatedAudioUrl = useCallback(async (objectName: string): Promise<string> => {
    try {
      console.log('开始获取认证音频URL:', objectName);
      
      // 如果是外部URL，直接返回
      if (objectName.startsWith('http')) {
        return objectName;
      }
      
      // 使用FileService获取认证的音频流
      const fileService = new FileService();
      const response = await fileService.getFilePreviewStream(objectName);
      
      // 详细检查返回的数据
      console.log('API响应详情:', {
        responseType: typeof response,
        responseConstructor: response?.constructor?.name,
        isBlob: response instanceof Blob,
        blobSize: response instanceof Blob ? response.size : 'N/A',
        blobType: response instanceof Blob ? response.type : 'N/A',
        response: response
      });
      
      // 确保返回的是Blob对象
      if (!response || !(response instanceof Blob)) {
        throw new Error(`API返回的不是Blob对象: ${typeof response}, ${(response as any)?.constructor?.name || 'unknown'}`);
      }
      
      if (response.size === 0) {
        throw new Error('接收到空的音频数据');
      }
      
      console.log('准备创建blob URL，blob信息:', {
        size: response.size,
        type: response.type
      });
      
      const blobUrl = URL.createObjectURL(response);
      console.log('创建认证音频URL成功:', { objectName, blobUrl });
      
      return blobUrl;
    } catch (error) {
      console.error('创建认证音频URL失败:', error);
      throw error;
    }
  }, []);

  // 加载音频
  const loadAudio = useCallback(async () => {
    const objectName = getObjectName();
    if (!objectName) {
      setHasError(true);
      setIsLoading(false);
      return;
    }

    try {
      setIsLoading(true);
      setHasError(false);
      
      const authUrl = await createAuthenticatedAudioUrl(objectName);
      setAuthenticatedAudioUrl(authUrl);
      
      console.log('音频URL设置成功:', authUrl);
    } catch (error) {
      console.error('加载音频失败:', error);
      setHasError(true);
      setAuthenticatedAudioUrl(null);
    } finally {
      setIsLoading(false);
    }
  }, [createAuthenticatedAudioUrl]);

  // 获取音频时长
  const getAudioDuration = (): number => {
    if (message.type === 'media') {
      const mediaContent = message.content as MediaMessageContent;
      return mediaContent.media_info?.metadata?.duration_seconds || 0;
    }
    return 0;
  };

  // 格式化时间
  const formatTime = (seconds: number): string => {
    // 检查输入是否为有效数字
    if (!isFinite(seconds) || seconds < 0) {
      return '0:00';
    }
    
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  // 播放/暂停控制
  const togglePlay = () => {
    const audio = audioRef.current;
    if (!audio) return;

    if (isPlaying) {
      audio.pause();
    } else {
      audio.play();
    }
  };

  // 组件挂载时加载音频
  useEffect(() => {
    loadAudio();
  }, [loadAudio]);

  // 组件卸载时清理资源
  useEffect(() => {
    return () => {
      if (authenticatedAudioUrl && authenticatedAudioUrl.startsWith('blob:')) {
        URL.revokeObjectURL(authenticatedAudioUrl);
      }
    };
  }, [authenticatedAudioUrl]);

  // 设置音频事件监听器
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio || !authenticatedAudioUrl) return;

    const handleLoadedMetadata = () => {
      const audioDuration = audio.duration;
      console.log('音频元数据加载完成:', {
        duration: audioDuration,
        isFinite: isFinite(audioDuration),
        src: audio.src
      });
      
      // 确保时长是有效数字
      if (isFinite(audioDuration) && audioDuration > 0) {
        setDuration(audioDuration);
      } else {
        console.warn('音频时长无效:', audioDuration);
        setDuration(0);
      }
      setIsLoading(false);
    };

    const handleTimeUpdate = () => {
      const currentTimeValue = audio.currentTime;
      // 确保当前时间是有效数字
      if (isFinite(currentTimeValue) && currentTimeValue >= 0) {
        setCurrentTime(currentTimeValue);
      }
    };

    const handlePlay = () => {
      setIsPlaying(true);
    };

    const handlePause = () => {
      setIsPlaying(false);
    };

    const handleEnded = () => {
      setIsPlaying(false);
      setCurrentTime(0);
    };

    const handleError = (e: Event) => {
      console.error('语音播放失败:', e);
      console.error('音频URL:', audioRef.current?.src);
      setHasError(true);
      setIsLoading(false);
    };

    const handleCanPlay = () => {
      setIsLoading(false);
    };

    audio.addEventListener('loadedmetadata', handleLoadedMetadata);
    audio.addEventListener('timeupdate', handleTimeUpdate);
    audio.addEventListener('play', handlePlay);
    audio.addEventListener('pause', handlePause);
    audio.addEventListener('ended', handleEnded);
    audio.addEventListener('error', handleError);
    audio.addEventListener('canplay', handleCanPlay);

    return () => {
      audio.removeEventListener('loadedmetadata', handleLoadedMetadata);
      audio.removeEventListener('timeupdate', handleTimeUpdate);
      audio.removeEventListener('play', handlePlay);
      audio.removeEventListener('pause', handlePause);
      audio.removeEventListener('ended', handleEnded);
      audio.removeEventListener('error', handleError);
      audio.removeEventListener('canplay', handleCanPlay);
    };
  }, [authenticatedAudioUrl]);

  // 进度条点击处理
  const handleProgressClick = (e: React.MouseEvent<HTMLDivElement>) => {
    const audio = audioRef.current;
    if (!audio || !isFinite(duration) || duration <= 0) return;

    const rect = e.currentTarget.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const percentage = Math.max(0, Math.min(1, clickX / rect.width));
    const newTime = percentage * duration;
    
    // 确保新时间是有效的
    if (isFinite(newTime) && newTime >= 0 && newTime <= duration) {
      audio.currentTime = newTime;
      setCurrentTime(newTime);
    }
  };

  if (hasError) {
    return (
      <div className="flex items-center space-x-3 p-3 bg-gray-100 rounded-lg max-w-sm">
        <div className="text-red-500">
          <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <div className="flex-1">
          <p className="text-sm text-gray-700">语音消息加载失败</p>
          <button 
            onClick={() => {
              console.log('尝试重新加载语音');
              // 清理之前的URL
              if (authenticatedAudioUrl && authenticatedAudioUrl.startsWith('blob:')) {
                URL.revokeObjectURL(authenticatedAudioUrl);
              }
              setAuthenticatedAudioUrl(null);
              // 重新加载
              loadAudio();
            }}
            className="text-xs text-blue-600 hover:text-blue-800"
          >
            重新加载
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-center space-x-3 p-3 bg-white border border-gray-200 rounded-lg max-w-sm relative">
      {/* 隐藏的音频元素 */}
      {authenticatedAudioUrl && (
        <audio ref={audioRef} src={authenticatedAudioUrl} preload="metadata" />
      )}
        
        {/* 播放按钮 */}
        <button
          onClick={togglePlay}
          disabled={isLoading}
          className="flex-shrink-0 w-10 h-10 bg-orange-500 text-white rounded-full flex items-center justify-center hover:bg-orange-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? (
            <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          ) : isPlaying ? (
            <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
          ) : (
            <svg className="h-5 w-5 ml-0.5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
            </svg>
          )}
        </button>

        {/* 进度条和时间 */}
        <div className="flex-1 min-w-0">
          <div 
            className="w-full h-2 bg-gray-200 rounded-full cursor-pointer mb-1"
            onClick={handleProgressClick}
          >
            <div 
              className="h-2 bg-orange-500 rounded-full transition-all duration-100"
              style={{ width: duration > 0 ? `${(currentTime / duration) * 100}%` : '0%' }}
            />
          </div>
          
          <div className="flex justify-between text-xs text-gray-500">
            <span>{formatTime(currentTime)}</span>
            <span>{duration > 0 ? formatTime(duration) : '--:--'}</span>
          </div>
        </div>

        {/* 语音图标 */}
        <div className="flex-shrink-0 text-gray-400">
          <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 015 8a1 1 0 00-2 0 7.001 7.001 0 006 6.93V17H6a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07z" clipRule="evenodd" />
          </svg>
        </div>

        {/* 发送状态指示器 */}
        {message.status === 'pending' && (
          <div className="absolute top-1 right-1 bg-white bg-opacity-80 rounded-full p-0.5">
            <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse"></div>
          </div>
        )}
        
        {message.status === 'failed' && (
          <div 
            className="absolute top-1 right-1 bg-red-500 text-white rounded-full p-0.5 cursor-pointer hover:bg-red-600 transition-colors z-10" 
            title="点击重新发送"
            onClick={(e) => {
              e.stopPropagation();
              onRetry?.(message);
            }}
          >
            <svg className="w-2 h-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
          </div>
        )}
        
        {/* 重要标记 */}
        {message.is_important && (
          <div className="absolute top-1 left-1 bg-yellow-400 text-yellow-800 rounded-full p-0.5 z-10">
            <svg className="w-2 h-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M3.172 5.172a4 4 0 015.656 0L10 6.343l1.172-1.171a4 4 0 115.656 5.656L10 17.657l-6.828-6.829a4 4 0 010-5.656z" clipRule="evenodd" />
            </svg>
          </div>
        )}
      </div>
    );
} 