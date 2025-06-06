'use client';

import { useCallback } from 'react';

interface RecordingControlsProps {
  isRecording: boolean;
  recordingTime: number;
  onStopRecording: () => Promise<void>;
  onCancelRecording: () => void;
}

export function RecordingControls({
  isRecording,
  recordingTime,
  onStopRecording,
  onCancelRecording
}: RecordingControlsProps) {
  
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

  // 只在录音时显示录音状态UI
  if (!isRecording) {
    return null;
  }

  return (
    <div className="border-t border-gray-200 bg-gray-50 p-3">
      <div className="flex justify-between items-center">
        <div className="flex items-center space-x-2">
          <span className="inline-block w-3 h-3 rounded-full bg-red-500 animate-pulse" />
          <span className="text-sm font-medium text-gray-700">
            正在录音 {formatRecordingTime(recordingTime)}
          </span>
        </div>
        <div className="flex space-x-2">
          <button 
            onClick={handleCancelRecording}
            className="rounded-full p-1 text-gray-500 hover:bg-gray-200"
            title="取消录音"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
          <button 
            onClick={handleStopRecording}
            className="rounded-full p-1 text-orange-500 hover:bg-orange-100"
            title="停止录音"
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <rect x="6" y="6" width="12" height="12" rx="1" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
} 