'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import FileMessage from './message/FileMessage';
import toast from 'react-hot-toast';

interface FileInfo {
  file_url: string;
  file_name: string;
  file_size: number;
  file_type: string;
  mime_type: string;
  object_name?: string;
}

interface ConversationFile {
  message_id: string;
  file_info: FileInfo;
  sender: {
    id: string;
    type: string;
    name: string;
  };
  timestamp: string;
}

interface FileManagerProps {
  conversationId: string;
  isOpen: boolean;
  onClose: () => void;
}

export default function FileManager({ conversationId, isOpen, onClose }: FileManagerProps) {
  const [files, setFiles] = useState<ConversationFile[]>([]);
  const [filteredFiles, setFilteredFiles] = useState<ConversationFile[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedFileType, setSelectedFileType] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);

  const ITEMS_PER_PAGE = 20;

  // 获取文件列表
  const fetchFiles = useCallback(async (page: number = 1, fileType?: string) => {
    if (!conversationId) return;

    setIsLoading(true);
    try {
      const params = new URLSearchParams({
        limit: ITEMS_PER_PAGE.toString(),
        offset: ((page - 1) * ITEMS_PER_PAGE).toString()
      });

      if (fileType && fileType !== 'all') {
        params.append('file_type', fileType);
      }

      const response = await fetch(
        `/api/v1/files/conversation/${conversationId}/files?${params}`,
        {
          method: 'GET',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json'
          }
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || '获取文件列表失败');
      }

      const data = await response.json();
      
      if (page === 1) {
        setFiles(data.files || []);
      } else {
        setFiles(prev => [...prev, ...(data.files || [])]);
      }
      
      setHasMore(data.files?.length === ITEMS_PER_PAGE);
    } catch (error) {
      console.error('获取文件列表失败:', error);
      toast.error(error instanceof Error ? error.message : '获取文件列表失败');
    } finally {
      setIsLoading(false);
    }
  }, [conversationId]);

  // 过滤文件
  useEffect(() => {
    let filtered = files;

    // 按文件类型过滤
    if (selectedFileType !== 'all') {
      filtered = filtered.filter(file => file.file_info.file_type === selectedFileType);
    }

    // 按文件名搜索
    if (searchTerm.trim()) {
      filtered = filtered.filter(file => 
        file.file_info.file_name.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    setFilteredFiles(filtered);
  }, [files, selectedFileType, searchTerm]);

  // 初始化加载
  useEffect(() => {
    if (isOpen && conversationId) {
      setCurrentPage(1);
      fetchFiles(1, selectedFileType);
    }
  }, [isOpen, conversationId, selectedFileType, fetchFiles]);

  // 加载更多
  const loadMore = useCallback(() => {
    if (!isLoading && hasMore) {
      const nextPage = currentPage + 1;
      setCurrentPage(nextPage);
      fetchFiles(nextPage, selectedFileType);
    }
  }, [currentPage, isLoading, hasMore, selectedFileType, fetchFiles]);

  // 删除文件
  const handleDeleteFile = useCallback(async (file: ConversationFile) => {
    if (!file.file_info.object_name) {
      toast.error('无法删除此文件：缺少文件标识');
      return;
    }

    if (!confirm(`确定要删除文件 "${file.file_info.file_name}" 吗？`)) {
      return;
    }

    try {
      const response = await fetch(
        `/api/v1/files/delete/${file.file_info.object_name}`,
        {
          method: 'DELETE',
          credentials: 'include'
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || '删除文件失败');
      }

      // 从列表中移除文件
      setFiles(prev => prev.filter(f => f.message_id !== file.message_id));
      toast.success('文件删除成功');
    } catch (error) {
      console.error('删除文件失败:', error);
      toast.error(error instanceof Error ? error.message : '删除文件失败');
    }
  }, []);

  // 格式化文件大小统计
  const getFileStats = useCallback(() => {
    const totalSize = filteredFiles.reduce((sum, file) => sum + file.file_info.file_size, 0);
    const formatSize = (bytes: number) => {
      if (bytes === 0) return '0 Bytes';
      const k = 1024;
      const sizes = ['Bytes', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };

    return {
      count: filteredFiles.length,
      totalSize: formatSize(totalSize)
    };
  }, [filteredFiles]);

  if (!isOpen) return null;

  const stats = getFileStats();

  return (
    <div className="fixed inset-0 z-50 bg-black bg-opacity-50 flex items-center justify-center">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl h-5/6 flex flex-col">
        {/* 头部 */}
        <div className="flex items-center justify-between p-6 border-b">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">文件管理</h2>
            <p className="text-sm text-gray-500 mt-1">
              共 {stats.count} 个文件，总大小 {stats.totalSize}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* 过滤和搜索 */}
        <div className="p-6 border-b bg-gray-50">
          <div className="flex flex-col sm:flex-row gap-4">
            {/* 文件类型过滤 */}
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                文件类型
              </label>
              <select
                value={selectedFileType}
                onChange={(e) => setSelectedFileType(e.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-orange-500 focus:outline-none"
              >
                <option value="all">全部类型</option>
                <option value="image">图片</option>
                <option value="document">文档</option>
                <option value="audio">音频</option>
                <option value="video">视频</option>
                <option value="archive">压缩包</option>
              </select>
            </div>

            {/* 文件名搜索 */}
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                搜索文件名
              </label>
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="输入文件名搜索..."
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-orange-500 focus:outline-none"
              />
            </div>
          </div>
        </div>

        {/* 文件列表 */}
        <div className="flex-1 overflow-y-auto p-6">
          {isLoading && filteredFiles.length === 0 ? (
            <div className="flex items-center justify-center h-32">
              <div className="flex items-center space-x-2 text-gray-500">
                <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span>加载中...</span>
              </div>
            </div>
          ) : filteredFiles.length === 0 ? (
            <div className="text-center py-12">
              <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
              </svg>
              <p className="mt-4 text-gray-500">暂无文件</p>
            </div>
          ) : (
            <div className="space-y-4">
              {filteredFiles.map((file) => (
                <div key={file.message_id} className="flex items-center space-x-4 p-4 border border-gray-200 rounded-lg">
                  {/* 文件展示 */}
                  <div className="flex-1">
                    <FileMessage 
                      fileInfo={file.file_info} 
                      message={{} as any}
                      searchTerm=""
                      compact={false}
                    />
                  </div>

                  {/* 文件信息 */}
                  <div className="flex-shrink-0 text-sm text-gray-500">
                    <div>发送者: {file.sender.name}</div>
                    <div>时间: {new Date(file.timestamp).toLocaleString()}</div>
                  </div>

                  {/* 操作按钮 */}
                  <div className="flex-shrink-0">
                    <button
                      onClick={() => handleDeleteFile(file)}
                      className="text-red-600 hover:text-red-800 p-2 rounded-md hover:bg-red-50"
                      title="删除文件"
                    >
                      <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                </div>
              ))}

              {/* 加载更多按钮 */}
              {hasMore && (
                <div className="text-center pt-4">
                  <Button
                    onClick={loadMore}
                    disabled={isLoading}
                    variant="outline"
                  >
                    {isLoading ? '加载中...' : '加载更多'}
                  </Button>
                </div>
              )}
            </div>
          )}
        </div>

        {/* 底部 */}
        <div className="flex items-center justify-end p-6 border-t bg-gray-50">
          <Button onClick={onClose} variant="outline">
            关闭
          </Button>
        </div>
      </div>
    </div>
  );
} 