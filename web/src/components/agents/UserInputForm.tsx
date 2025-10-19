'use client';

import { useState, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ChevronDown, ChevronUp, Upload, X, File, Image as ImageIcon } from 'lucide-react';
import type { UserInputFormField } from '@/types/agent-chat';

interface UserInputFormProps {
  fields: UserInputFormField[];
  onSubmit: (values: Record<string, any>) => void;
  onCancel?: () => void;
}

export function UserInputForm({ fields, onSubmit, onCancel }: UserInputFormProps) {
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
  const [fileInputs, setFileInputs] = useState<Record<string, HTMLInputElement | null>>({});

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
          // 文件字段验证
          if (!value || (Array.isArray(value) && value.length === 0)) {
            newErrors[field.variable] = `${field.label} 是必填项`;
            return;
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

  const handleSubmit = () => {
    if (validateForm()) {
      onSubmit(values);
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

    switch (field.type) {
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
        
        return (
          <div className="space-y-3">
            {/* 文件上传区域 */}
            <div className="relative">
              <input
                ref={(el) => {
                  if (el) {
                    setFileInputs(prev => ({ ...prev, [field.variable]: el }));
                  }
                }}
                type="file"
                multiple={isMultiple}
                onChange={(e) => handleFileUpload(field.variable, e.target.files)}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                accept={field.options?.join(',') || '*'}
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

            {/* 已上传文件列表 */}
            {currentFile && (
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
              className="bg-orange-500 hover:bg-orange-600"
            >
              开始聊天
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

