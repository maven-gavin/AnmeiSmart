'use client';

import { useState, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ChevronDown, ChevronUp, Upload, X, File, Image as ImageIcon, Loader2 } from 'lucide-react';
import type { UserInputFormField } from '@/types/agent-chat';
import { uploadAgentFile, uploadAgentFiles } from '@/service/agentFileService';
import toast from 'react-hot-toast';

interface UserInputFormProps {
  fields: UserInputFormField[];
  agentConfigId: string;  // 新增：Agent配置ID，用于文件上传
  onSubmit: (values: Record<string, any>) => void;
  onCancel?: () => void;
}

export function UserInputForm({ fields, agentConfigId, onSubmit, onCancel }: UserInputFormProps) {
  const [collapsed, setCollapsed] = useState(false);
  const [values, setValues] = useState<Record<string, any>>(() => {
    // 初始化默认值
    const initialValues: Record<string, any> = {};
    fields.forEach(field => {
      if (field.default !== undefined) {
        initialValues[field.variable] = field.default;
      }
    });
    return initialValues;
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [uploading, setUploading] = useState(false);

  // 过滤隐藏字段
  const visibleFields = fields.filter(f => !f.hide);

  if (visibleFields.length === 0) return null;

  // 验证表单
  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};
    
    visibleFields.forEach(field => {
      const value = values[field.variable];
      
      // 必填验证
      if (field.required) {
        if (field.type === 'file' || field.type === 'file-list') {
          // 文件字段验证（支持本地文件和远程URL）
          if (!value || (Array.isArray(value) && value.length === 0)) {
            newErrors[field.variable] = `${field.label} 是必填项`;
            return;
          }
          // URL格式验证（如果是remote_url方式）
          const uploadMethods = field.allowed_file_upload_methods || ['local_file'];
          const method = uploadMethods.length > 1 
            ? values[`${field.variable}_method`] || 'local_file'
            : uploadMethods[0];
          if (method === 'remote_url') {
            const urls = Array.isArray(value) ? value : [value];
            const invalidUrls = urls.filter(url => {
              try {
                new URL(url);
                return false;
              } catch {
                return true;
              }
            });
            if (invalidUrls.length > 0) {
              newErrors[field.variable] = '请输入有效的URL地址';
              return;
            }
          }
        } else {
          // 其他字段验证
          if (!value || (typeof value === 'string' && !value.trim())) {
            newErrors[field.variable] = `${field.label} 是必填项`;
            return;
          }
        }
      }
      
      // 长度验证
      if (field.type === 'text-input' && field.max_length && value) {
        const strValue = String(value);
        if (strValue.length > field.max_length) {
          newErrors[field.variable] = `不能超过 ${field.max_length} 个字符`;
        }
      }

      // 文件大小验证（可选）
      if ((field.type === 'file' || field.type === 'file-list') && value) {
        const files = Array.isArray(value) ? value : [value];
        const maxSize = 10 * 1024 * 1024; // 10MB 默认限制
        
        for (const file of files) {
          if (file.size > maxSize) {
            newErrors[field.variable] = `文件大小不能超过 ${formatFileSize(maxSize)}`;
            break;
          }
        }
      }
    });

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async () => {
    if (!validateForm()) return;
    
    setUploading(true);
    
    try {
      // 处理文件字段：上传文件到Dify并替换为文件ID
      const finalValues: Record<string, any> = { ...values };
      
      for (const field of visibleFields) {
        if (field.type === 'file' || field.type === 'file-list') {
          const value = values[field.variable];
          const uploadMethods = field.allowed_file_upload_methods || ['local_file'];
          const method = uploadMethods.length > 1 
            ? values[`${field.variable}_method`] || 'local_file'
            : uploadMethods[0];
          
          if (value) {
            if (method === 'local_file') {
              // 本地文件上传到Dify
              if (field.type === 'file') {
                const file = value as File;
                const uploadResult = await uploadAgentFile(agentConfigId, file);
                finalValues[field.variable] = uploadResult.id;
              } else if (field.type === 'file-list') {
                const files = value as File[];
                const uploadResults = await uploadAgentFiles(agentConfigId, files);
                finalValues[field.variable] = uploadResults.map(r => r.id);
              }
            } else {
              // 远程URL直接传递
              finalValues[field.variable] = value;
            }
          }
        }
      }
      
      // 清理内部状态字段（不传给后端）
      Object.keys(finalValues).forEach(key => {
        if (key.endsWith('_method')) {
          delete finalValues[key];
        }
      });
      
      // 提交最终值（包含Dify文件ID）
      onSubmit(finalValues);
    } catch (error: any) {
      console.error('文件上传失败:', error);
      const errorMessage = error?.message || '文件上传失败，请重试';
      toast.error(errorMessage);
    } finally {
      setUploading(false);
    }
  };

  const handleValueChange = (variable: string, value: any) => {
    setValues(prev => ({ ...prev, [variable]: value }));
    // 清除该字段的错误
    if (errors[variable]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[variable];
        return newErrors;
      });
    }
  };

  // 处理文件上传
  const handleFileUpload = (variable: string, files: FileList | null) => {
    if (!files || files.length === 0) return;

    const field = fields.find(f => f.variable === variable);
    if (!field) return;

    const fileArray = Array.from(files);
    
    // 根据字段类型处理文件
    if (field.type === 'file') {
      // 单文件上传，只取第一个文件
      const file = fileArray[0];
      handleValueChange(variable, file);
    } else if (field.type === 'file-list') {
      // 多文件上传
      const currentFiles = values[variable] || [];
      const newFiles = [...currentFiles, ...fileArray];
      handleValueChange(variable, newFiles);
    }
  };

  // 移除文件
  const removeFile = (variable: string, fileIndex?: number) => {
    const field = fields.find(f => f.variable === variable);
    if (!field) return;

    if (field.type === 'file') {
      handleValueChange(variable, null);
    } else if (field.type === 'file-list' && fileIndex !== undefined) {
      const currentFiles = values[variable] || [];
      const newFiles = currentFiles.filter((_: any, index: number) => index !== fileIndex);
      handleValueChange(variable, newFiles);
    }
  };

  // 获取文件图标
  const getFileIcon = (file: File) => {
    if (file.type.startsWith('image/')) {
      return <ImageIcon className="h-4 w-4 text-blue-500" />;
    }
    return <File className="h-4 w-4 text-gray-500" />;
  };

  // 格式化文件大小
  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // 渲染字段
  const renderField = (field: UserInputFormField) => {
    const value = values[field.variable] ?? '';
    // 默认使用 text-input 类型（Dify API可能不返回type字段）
    const fieldType = field.type || 'text-input';

    switch (fieldType) {
      case 'text-input':
        return (
          <Input
            value={value}
            onChange={(e) => handleValueChange(field.variable, e.target.value)}
            placeholder={field.description || `请输入${field.label}`}
            maxLength={field.max_length}
            className="w-full"
          />
        );
      
      case 'paragraph':
        return (
          <Textarea
            value={value}
            onChange={(e) => handleValueChange(field.variable, e.target.value)}
            placeholder={field.description || `请输入${field.label}`}
            rows={4}
            className="w-full resize-none"
          />
        );
      
      case 'number':
        return (
          <Input
            type="number"
            value={value}
            onChange={(e) => handleValueChange(field.variable, Number(e.target.value))}
            placeholder={field.description || `请输入${field.label}`}
            className="w-full"
          />
        );
      
      case 'select':
        return (
          <Select
            value={value}
            onValueChange={(val) => handleValueChange(field.variable, val)}
          >
            <SelectTrigger className="w-full">
              <SelectValue placeholder={field.description || `请选择${field.label}`} />
            </SelectTrigger>
            <SelectContent>
              {field.options?.map((option) => (
                <SelectItem key={option} value={option}>
                  {option}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        );
      
      case 'file':
      case 'file-list':
        const currentFile = values[field.variable];
        const isMultiple = field.type === 'file-list';
        const uploadMethods = field.allowed_file_upload_methods || ['local_file'];
        const currentMethod = uploadMethods.length > 1 
          ? (values[`${field.variable}_method`] || 'local_file')
          : uploadMethods[0];
        
        return (
          <div className="space-y-3">
            {/* 上传方式选择（如果支持多种方式） */}
            {uploadMethods.length > 1 && (
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => handleValueChange(`${field.variable}_method`, 'local_file')}
                  className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                    currentMethod === 'local_file'
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  本地上传
                </button>
                <button
                  type="button"
                  onClick={() => handleValueChange(`${field.variable}_method`, 'remote_url')}
                  className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                    currentMethod === 'remote_url'
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  远程URL
                </button>
              </div>
            )}

            {/* 本地文件上传 */}
            {currentMethod === 'local_file' && (
              <div className="relative">
                <input
                  type="file"
                  multiple={isMultiple}
                  onChange={(e) => handleFileUpload(field.variable, e.target.files)}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                  accept={field.allowed_file_extensions?.map(ext => `.${ext}`).join(',') || '*'}
                />
                <div className="rounded-lg border border-dashed border-gray-300 p-6 text-center hover:border-gray-400 transition-colors">
                  <Upload className="mx-auto h-8 w-8 text-gray-400 mb-2" />
                  <p className="text-sm text-gray-600 mb-1">
                    {isMultiple ? '点击或拖拽上传多个文件' : '点击或拖拽上传文件'}
                  </p>
                  <p className="text-xs text-gray-500">
                    {field.description || '支持所有文件类型'}
                  </p>
                </div>
              </div>
            )}

            {/* 远程URL输入 */}
            {currentMethod === 'remote_url' && (
              <div>
                {isMultiple ? (
                  <Textarea
                    value={Array.isArray(currentFile) ? currentFile.join('\n') : (currentFile || '')}
                    onChange={(e) => {
                      const urls = e.target.value.split('\n').filter(u => u.trim());
                      handleValueChange(field.variable, urls);
                    }}
                    placeholder="每行输入一个文件URL"
                    rows={4}
                    className="w-full resize-none"
                  />
                ) : (
                  <Input
                    value={currentFile || ''}
                    onChange={(e) => handleValueChange(field.variable, e.target.value)}
                    placeholder="输入文件URL"
                    className="w-full"
                  />
                )}
                <p className="mt-1 text-xs text-gray-500">
                  支持的文件类型: {field.allowed_file_types?.join(', ') || '全部'}
                </p>
              </div>
            )}

            {/* 已上传文件列表（仅本地文件） */}
            {currentMethod === 'local_file' && currentFile && (
              <div className="space-y-2">
                {isMultiple ? (
                  // 多文件显示
                  Array.isArray(currentFile) && currentFile.map((file: File, index: number) => (
                    <div key={`${field.variable}-file-${index}-${file.name}-${file.size}`} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center space-x-3">
                        {getFileIcon(file)}
                        <div>
                          <p className="text-sm font-medium text-gray-900">{file.name}</p>
                          <p className="text-xs text-gray-500">{formatFileSize(file.size)}</p>
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={() => removeFile(field.variable, index)}
                        className="p-1 text-gray-400 hover:text-red-500 transition-colors"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    </div>
                  ))
                ) : (
                  // 单文件显示
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center space-x-3">
                      {getFileIcon(currentFile)}
                      <div>
                        <p className="text-sm font-medium text-gray-900">{currentFile.name}</p>
                        <p className="text-xs text-gray-500">{formatFileSize(currentFile.size)}</p>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => removeFile(field.variable)}
                      className="p-1 text-gray-400 hover:text-red-500 transition-colors"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        );
      
      default:
        return (
          <p className="text-sm text-gray-500">
            暂不支持 {field.type} 类型
          </p>
        );
    }
  };

  return (
    <div className="mx-auto w-full max-w-2xl rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
      {/* 表单头部 */}
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">
          填写信息
        </h3>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setCollapsed(!collapsed)}
          className="h-8 w-8 p-0"
        >
          {collapsed ? (
            <ChevronDown className="h-4 w-4" />
          ) : (
            <ChevronUp className="h-4 w-4" />
          )}
        </Button>
      </div>

      {/* 表单内容 */}
      {!collapsed && (
        <>
          <div className="space-y-4">
            {visibleFields.map((field) => (
              <div key={field.variable}>
                <label className="mb-1.5 block text-sm font-medium text-gray-700">
                  {field.label}
                  {field.required && (
                    <span className="ml-1 text-red-500">*</span>
                  )}
                </label>
                {renderField(field)}
                {errors[field.variable] && (
                  <p className="mt-1 text-sm text-red-600">
                    {errors[field.variable]}
                  </p>
                )}
                {field.max_length && field.type === 'text-input' && (
                  <p className="mt-1 text-xs text-gray-500">
                    {String(values[field.variable] || '').length} / {field.max_length} 字符
                  </p>
                )}
              </div>
            ))}
          </div>

          {/* 操作按钮 */}
          <div className="mt-6 flex justify-end space-x-3">
            {onCancel && (
              <Button
                variant="outline"
                onClick={onCancel}
              >
                取消
              </Button>
            )}
            <Button
              onClick={handleSubmit}
              disabled={uploading}
              className="bg-orange-500 hover:bg-orange-600"
            >
              {uploading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  上传中...
                </>
              ) : (
                '开始聊天'
              )}
            </Button>
          </div>
        </>
      )}

      {/* 已折叠状态 */}
      {collapsed && (
        <Button
          variant="outline"
          size="sm"
          onClick={() => setCollapsed(false)}
          className="w-full"
        >
          编辑信息
        </Button>
      )}
    </div>
  );
}

