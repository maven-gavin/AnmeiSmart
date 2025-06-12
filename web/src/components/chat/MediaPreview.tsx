'use client';

import { useCallback, useState } from 'react';
import { FileService } from '@/service/fileService';
import { type FileInfo } from '@/types/chat';
import toast from 'react-hot-toast';

interface MediaPreviewProps {
  conversationId?: string | null;
  imagePreview?: string | null;
  audioPreview?: string | null;
  filePreview?: FileInfo | null;
  onCancelImage?: () => void;
  onCancelAudio?: () => void;
  onCancelFile?: () => void;
}

export function MediaPreview({ 
  conversationId,
  imagePreview, 
  audioPreview, 
  filePreview,
  onCancelImage, 
  onCancelAudio,
  onCancelFile
}: MediaPreviewProps) {
  const [sendError, setSendError] = useState<string | null>(null);

  if (!imagePreview && !audioPreview && !filePreview) {
    return null;
  }

  return (
    <>
      {/* 错误提示 */}
      {sendError && (
        <div className="border-t border-gray-200 bg-red-50 p-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center text-red-700">
              <svg className="h-4 w-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              <span className="text-sm">{sendError}</span>
            </div>
            <button 
              onClick={() => setSendError(null)}
              className="text-red-500 hover:text-red-700 transition-colors"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      )}

      {/* 图片预览 */}
      {imagePreview && (
        <div className="border-t border-gray-200 bg-gray-50 p-3">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-gray-700">图片预览</span>
            <button 
              onClick={onCancelImage}
              className="text-gray-500 hover:text-gray-700 transition-colors"
              title="关闭图片预览"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <div className="relative inline-block">
            <img 
              src={imagePreview} 
              alt="预览图片" 
              className="max-h-40 max-w-full rounded-lg object-contain shadow-sm"
            />
            {/* 图片缩略图删除按钮 - 在图片右下角 */}
            <button 
              onClick={onCancelImage}
              className="absolute -bottom-2 -right-2 w-6 h-6 bg-red-500 text-white rounded-full flex items-center justify-center hover:bg-red-600 transition-colors shadow-md"
              title="删除此图片"
            >
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      )}

      {/* 音频预览 */}
      {audioPreview && (
        <div className="border-t border-gray-200 bg-gradient-to-r from-orange-50 to-red-50 p-4">
          <div className="flex justify-between items-center mb-3">
            <div className="flex items-center space-x-2">
              <svg className="w-5 h-5 text-orange-500" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 2a3 3 0 00-3 3v6a3 3 0 006 0V5a3 3 0 00-3-3z"/>
                <path d="M19 10v1a7 7 0 01-14 0v-1a1 1 0 012 0v1a5 5 0 0010 0v-1a1 1 0 012 0z"/>
                <path d="M12 18.5a1 1 0 01-1-1v-1a1 1 0 012 0v1a1 1 0 01-1 1z"/>
                <path d="M8 21h8a1 1 0 010 2H8a1 1 0 010-2z"/>
              </svg>
              <span className="text-sm font-medium text-gray-700">语音预览</span>
            </div>
            <button 
              onClick={onCancelAudio}
              className="text-gray-500 hover:text-gray-700 transition-colors"
              title="关闭语音预览"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          
          {/* 语音控件容器 */}
          <div className="relative">
            <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-200">
              <div className="flex items-center space-x-3">
                {/* 语音图标 */}
                <div className="flex-shrink-0">
                  <div className="w-12 h-12 bg-orange-100 rounded-full flex items-center justify-center">
                    <svg className="w-6 h-6 text-orange-500" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M12 2a3 3 0 00-3 3v6a3 3 0 006 0V5a3 3 0 00-3-3z"/>
                      <path d="M19 10v1a7 7 0 01-14 0v-1a1 1 0 012 0v1a5 5 0 0010 0v-1a1 1 0 012 0z"/>
                    </svg>
                  </div>
                </div>
                
                {/* 语音信息和控件 */}
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-900">录音内容</span>
                    <span className="text-xs text-gray-500">点击播放试听</span>
                  </div>
                  
                  {/* HTML5 音频控件 */}
                  <audio 
                    src={audioPreview} 
                    controls 
                    preload="metadata"
                    className="w-full h-8"
                    style={{
                      outline: 'none',
                      borderRadius: '4px'
                    }}
                  />
                </div>
              </div>
            </div>
            
            {/* 语音删除按钮 - 在音频控件右下角 */}
            <button 
              onClick={onCancelAudio}
              className="absolute -bottom-2 -right-2 w-6 h-6 bg-red-500 text-white rounded-full flex items-center justify-center hover:bg-red-600 transition-colors shadow-md z-10"
              title="删除此语音"
            >
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          
          {/* 提示信息 */}
          <div className="mt-3 text-center">
            <p className="text-xs text-gray-500">
              可以试听录音内容，满意后点击"发送"按钮发送语音消息
            </p>
          </div>
        </div>
      )}

      {/* 文件预览 */}
      {filePreview && (
        <div className="border-t border-gray-200 bg-gray-50 p-3">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-gray-700">文件预览</span>
            <button 
              onClick={onCancelFile}
              className="text-gray-500 hover:text-gray-700 transition-colors"
              title="关闭文件预览"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <div className="relative inline-block">
            <div className="flex items-center space-x-3 p-3 bg-white rounded-lg border border-gray-200 shadow-sm">
              {/* 文件图标 */}
              <div className="flex-shrink-0">
                <svg className="w-8 h-8 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              
              {/* 文件信息 */}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {filePreview.file_name}
                </p>
                <p className="text-xs text-gray-500">
                  {filePreview.file_type} • {(filePreview.file_size / 1024).toFixed(1)} KB
                </p>
              </div>
            </div>
            
            {/* 文件删除按钮 - 在文件预览右下角 */}
            <button 
              onClick={onCancelFile}
              className="absolute -bottom-2 -right-2 w-6 h-6 bg-red-500 text-white rounded-full flex items-center justify-center hover:bg-red-600 transition-colors shadow-md"
              title="删除此文件"
            >
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      )}
    </>
  )
} 