'use client';

import React, { useState } from 'react';
import FileSelector from '@/components/chat/FileSelector';
import FileMessage from '@/components/chat/message/FileMessage';
import { type FileInfo } from '@/types/chat';

export default function TestFileUploadPage() {
  const [uploadedFiles, setUploadedFiles] = useState<FileInfo[]>([]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
    console.log('文件已选择:', file.name, file.size, file.type);
  };

  const handleFileUpload = (fileInfo: FileInfo) => {
    setUploadedFiles(prev => [...prev, fileInfo]);
    setSelectedFile(null);
    console.log('文件上传成功:', fileInfo);
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">文件上传测试</h1>
        
        {/* 当前选择的文件信息 */}
        {selectedFile && (
          <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <h3 className="text-lg font-medium text-blue-900 mb-2">当前选择的文件:</h3>
            <p className="text-blue-700">
              <strong>文件名:</strong> {selectedFile.name}<br/>
              <strong>大小:</strong> {(selectedFile.size / 1024 / 1024).toFixed(2)} MB<br/>
              <strong>类型:</strong> {selectedFile.type}
            </p>
          </div>
        )}
        
        {/* 文件选择器 */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">选择文件上传</h2>
          <FileSelector
            conversationId="test_conversation_123"
            onFileSelect={handleFileSelect}
            onFileUpload={handleFileUpload}
            accept="*/*"
            maxSize={50 * 1024 * 1024} // 50MB
          />
        </div>
        
        {/* 已上传的文件列表 */}
        {uploadedFiles.length > 0 && (
          <div>
            <h2 className="text-xl font-semibold text-gray-800 mb-4">
              已上传的文件 ({uploadedFiles.length})
            </h2>
            <div className="space-y-4">
              {uploadedFiles.map((fileInfo, index) => (
                <div key={index} className="p-4 bg-white rounded-lg shadow">
                  <FileMessage fileInfo={fileInfo} />
                </div>
              ))}
            </div>
          </div>
        )}
        
        {/* 调试信息 */}
        <div className="mt-8 p-4 bg-gray-100 rounded-lg">
          <h3 className="text-lg font-medium text-gray-800 mb-2">调试信息:</h3>
          <pre className="text-sm text-gray-600 overflow-auto">
            {JSON.stringify({ selectedFile: selectedFile?.name, uploadedFiles }, null, 2)}
          </pre>
        </div>
      </div>
    </div>
  );
} 