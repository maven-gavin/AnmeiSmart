'use client';

import { useCallback, useState, useEffect } from 'react';

interface RecordingControlsProps {
  isRecording: boolean;
  recordingTime: number;
  onStopRecording: () => Promise<void>;
  onCancelRecording: () => void;
  onPauseRecording?: () => void;
  onResumeRecording?: () => void;
  isPaused?: boolean;
  maxDuration?: number; // 最大录音时长（秒）
}

export function RecordingControls({
  isRecording,
  recordingTime,
  onStopRecording,
  onCancelRecording,
  onPauseRecording,
  onResumeRecording,
  isPaused = false,
  maxDuration = 300 // 默认5分钟
}: RecordingControlsProps) {
  const [audioLevel, setAudioLevel] = useState(0); // 音量等级 0-100
  
  // 模拟音量检测（实际项目中应该从MediaRecorder获取）
  useEffect(() => {
    if (isRecording && !isPaused) {
      const interval = setInterval(() => {
        // 模拟音量波动
        setAudioLevel(Math.random() * 80 + 20);
      }, 100);
      
      return () => clearInterval(interval);
    } else {
      setAudioLevel(0);
    }
  }, [isRecording, isPaused]);

  // 格式化录音时间
  const formatRecordingTime = useCallback((seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
  }, []);

  // 处理停止录音
  const handleStopRecording = useCallback(async () => {
    try {
      await onStopRecording();
    } catch (error) {
      console.error('停止录音失败:', error);
    }
  }, [onStopRecording]);

  // 处理取消录音
  const handleCancelRecording = useCallback(() => {
    try {
      onCancelRecording();
    } catch (error) {
      console.error('取消录音失败:', error);
    }
  }, [onCancelRecording]);

  // 处理暂停/继续录音
  const handlePauseToggle = useCallback(() => {
    if (isPaused) {
      onResumeRecording?.();
    } else {
      onPauseRecording?.();
    }
  }, [isPaused, onPauseRecording, onResumeRecording]);

  // 计算进度百分比
  const progressPercentage = Math.min((recordingTime / maxDuration) * 100, 100);
  
  // 判断是否接近最大时长
  const isNearMaxDuration = recordingTime >= maxDuration * 0.9;
  const isMaxDuration = recordingTime >= maxDuration;

  // 只在录音时显示录音状态UI
  if (!isRecording) {
    return null;
  }

  return (
    <div className="border-t border-gray-200 bg-gradient-to-r from-orange-50 to-red-50 p-4">
      {/* 录音状态头部 */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-3">
          {/* 录音状态指示器 */}
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${isPaused ? 'bg-yellow-500' : 'bg-red-500 animate-pulse'}`} />
            <span className="text-sm font-medium text-gray-700">
              {isPaused ? '录音已暂停' : '正在录音'}
            </span>
          </div>
          
          {/* 音量指示器 */}
          <div className="flex items-center space-x-1">
            {[1, 2, 3, 4, 5].map((level) => (
              <div
                key={level}
                className={`w-1 rounded-full transition-all duration-100 ${
                  audioLevel > (level - 1) * 20
                    ? level <= 3 
                      ? 'bg-green-500 h-3' 
                      : level === 4 
                        ? 'bg-yellow-500 h-4' 
                        : 'bg-red-500 h-5'
                    : 'bg-gray-300 h-2'
                }`}
              />
            ))}
          </div>
        </div>

        {/* 录音时间 */}
        <div className="flex items-center space-x-2">
          <span className={`text-lg font-mono font-bold ${
            isNearMaxDuration ? 'text-red-500' : 'text-gray-700'
          }`}>
            {formatRecordingTime(recordingTime)}
          </span>
          <span className="text-xs text-gray-500">
            / {formatRecordingTime(maxDuration)}
          </span>
        </div>
      </div>

      {/* 进度条 */}
      <div className="mb-3">
        <div className="w-full bg-gray-200 rounded-full h-2 relative overflow-hidden">
          <div 
            className={`h-2 rounded-full transition-all duration-300 ${
              isNearMaxDuration 
                ? 'bg-gradient-to-r from-orange-500 to-red-500' 
                : 'bg-gradient-to-r from-orange-400 to-orange-500'
            }`}
            style={{ width: `${progressPercentage}%` }}
          />
          {/* 进度条上的波纹效果 */}
          {!isPaused && (
            <div 
              className="absolute top-0 h-2 w-8 bg-white opacity-30 rounded-full animate-pulse"
              style={{ 
                left: `${Math.max(0, progressPercentage - 8)}%`,
                animationDuration: '1s'
              }}
            />
          )}
        </div>
        {isMaxDuration && (
          <p className="text-xs text-red-500 mt-1">已达到最大录音时长</p>
        )}
      </div>

      {/* 控制按钮 */}
      <div className="flex items-center justify-center space-x-4">
        {/* 取消录音 */}
        <button 
          onClick={handleCancelRecording}
          className="flex items-center justify-center w-10 h-10 rounded-full bg-gray-500 text-white hover:bg-gray-600 transition-colors shadow-md"
          title="取消录音"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        {/* 暂停/继续录音 */}
        {onPauseRecording && onResumeRecording && (
          <button 
            onClick={handlePauseToggle}
            className={`flex items-center justify-center w-12 h-12 rounded-full text-white transition-colors shadow-md ${
              isPaused 
                ? 'bg-green-500 hover:bg-green-600' 
                : 'bg-yellow-500 hover:bg-yellow-600'
            }`}
            title={isPaused ? "继续录音" : "暂停录音"}
          >
            {isPaused ? (
              <svg className="w-6 h-6 ml-0.5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M8 5v14l11-7z"/>
              </svg>
            ) : (
              <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                <path d="M6 4h4v16H6zM14 4h4v16h-4z"/>
              </svg>
            )}
          </button>
        )}

        {/* 停止录音 */}
        <button 
          onClick={handleStopRecording}
          className="flex items-center justify-center w-12 h-12 rounded-full bg-orange-500 text-white hover:bg-orange-600 transition-colors shadow-md"
          title="完成录音"
        >
          <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
            <rect x="4" y="4" width="16" height="16" rx="2" />
          </svg>
        </button>
      </div>

      {/* 录音提示 */}
      <div className="mt-3 text-center">
        <p className="text-xs text-gray-500">
          {isPaused 
            ? "点击播放按钮继续录音" 
            : "说话时请保持设备靠近嘴部，录音质量更佳"
          }
        </p>
      </div>
    </div>
  );
} 