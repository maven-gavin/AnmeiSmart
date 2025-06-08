'use client';

import React, { useRef, useState, useCallback } from 'react';
import { Button } from '@/components/ui/button';

interface FileInfo {
  file_url: string;
  file_name: string;
  file_size: number;
  file_type: string;
  mime_type: string;
  object_name?: string;
}

interface FileSelectorProps {
  conversationId?: string | null;
  onFileSelect: (file: File) => void;
  onFileUpload: (fileInfo: FileInfo) => void;
  disabled?: boolean;
  accept?: string;
  maxSize?: number; // 最大文件大小（字节）
  className?: string;
}

export default function FileSelector({
  conversationId,
  onFileSelect,
  onFileUpload,
  disabled = false,
  accept = "*/*",
  maxSize = 50 * 1024 * 1024, // 默认50MB
  className = ""
}: FileSelectorProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // 文件类型验证
  const validateFile = useCallback((file: File): string | null => {
    // 检查文件大小
    if (file.size > maxSize) {
      const sizeMB = Math.round(maxSize / (1024 * 1024));
      return `文件大小超出限制，最大允许 ${sizeMB}MB`;
    }

    // 检查文件类型（如果指定了accept）
    if (accept !== "*/*") {
      const acceptTypes = accept.split(',').map(type => type.trim());
      const fileType = file.type;
      const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
      
      const isValidType = acceptTypes.some(acceptType => {
        if (acceptType.startsWith('.')) {
          return acceptType === fileExtension;
        } else if (acceptType.includes('*')) {
          const baseType = acceptType.split('/')[0];
          return fileType.startsWith(baseType);
        } else {
          return fileType === acceptType;
        }
      });

      if (!isValidType) {
        return `不支持的文件类型: ${fileType}`;
      }
    }

    return null;
  }, [accept, maxSize]);

  // 上传文件到服务器
  const uploadFile = useCallback(async (file: File): Promise<FileInfo> => {
    if (!conversationId) {
      throw new Error('会话ID不能为空');
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('conversation_id', conversationId);

    const response = await fetch('/api/v1/files/upload', {
      method: 'POST',
      body: formData,
      credentials: 'include',
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `上传失败: ${response.status}`);
    }

    const result = await response.json();
    if (!result.success) {
      throw new Error(result.message || '上传失败');
    }

    return result.file_info;
  }, [conversationId]);

  // 处理文件选择
  const handleFileSelect = useCallback(async (file: File) => {
    setUploadError(null);
    
    // 验证文件
    const validationError = validateFile(file);
    if (validationError) {
      setUploadError(validationError);
      return;
    }

    // 通知父组件文件已选择
    onFileSelect(file);

    // 开始上传
    setIsUploading(true);
    setUploadProgress(0);

    try {
      // 模拟上传进度
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 200);

      const fileInfo = await uploadFile(file);
      
      clearInterval(progressInterval);
      setUploadProgress(100);
      
      // 延迟一下让用户看到100%
      setTimeout(() => {
        onFileUpload(fileInfo);
        setIsUploading(false);
        setUploadProgress(0);
      }, 500);

    } catch (error) {
      setIsUploading(false);
      setUploadProgress(0);
      setUploadError(error instanceof Error ? error.message : '上传失败');
    }
  }, [validateFile, onFileSelect, uploadFile, onFileUpload]);

  // 处理文件输入变化
  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileSelect(file);
    }
    // 清空input值，允许重复选择同一文件
    e.target.value = '';
  }, [handleFileSelect]);

  // 处理拖拽事件
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    if (!disabled && !isUploading) {
      setIsDragOver(true);
    }
  }, [disabled, isUploading]);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    
    if (disabled || isUploading) return;

    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFileSelect(files[0]); // 只处理第一个文件
    }
  }, [disabled, isUploading, handleFileSelect]);

  // 触发文件选择
  const triggerFileSelect = useCallback(() => {
    if (!disabled && !isUploading) {
      fileInputRef.current?.click();
    }
  }, [disabled, isUploading]);

  // 格式化文件大小
  const formatFileSize = useCallback((bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }, []);

  return (
    <div className={`relative ${className}`}>
      {/* 隐藏的文件输入 */}
      <input
        ref={fileInputRef}
        type="file"
        className="hidden"
        accept={accept}
        onChange={handleInputChange}
        disabled={disabled || isUploading}
      />

      {/* 拖拽区域 */}
      <div
        className={`
          border-2 border-dashed rounded-lg p-6 text-center transition-colors
          ${isDragOver 
            ? 'border-orange-500 bg-orange-50' 
            : 'border-gray-300 hover:border-gray-400'
          }
          ${disabled || isUploading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
        `}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={triggerFileSelect}
      >
        {isUploading ? (
          <div className="space-y-4">
            <div className="flex items-center justify-center">
              <svg className="animate-spin h-8 w-8 text-orange-500" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            </div>
            <div>
              <p className="text-sm text-gray-600">上传中...</p>
              <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-orange-500 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                ></div>
              </div>
              <p className="text-xs text-gray-500 mt-1">{uploadProgress}%</p>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="flex items-center justify-center">
              <svg className="h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
            </div>
            <div>
              <p className="text-sm text-gray-600">
                拖拽文件到此处或 <span className="text-orange-500 font-medium">点击选择文件</span>
              </p>
              <p className="text-xs text-gray-500 mt-1">
                最大文件大小: {formatFileSize(maxSize)}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* 错误提示 */}
      {uploadError && (
        <div className="mt-2 p-3 bg-red-50 border border-red-200 rounded-md">
          <div className="flex items-center">
            <svg className="h-4 w-4 text-red-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            <span className="text-sm text-red-700">{uploadError}</span>
            <button 
              onClick={() => setUploadError(null)}
              className="ml-auto text-red-500 hover:text-red-700"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      )}
    </div>
  );
} 