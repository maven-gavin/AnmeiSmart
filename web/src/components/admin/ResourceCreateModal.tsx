'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { resourceService, CreateResourceRequest } from '@/service/resourceService';
import toast from 'react-hot-toast';

interface ResourceCreateModalProps {
  isOpen: boolean;
  onClose: () => void;
  onResourceCreated: () => void;
}

export default function ResourceCreateModal({ isOpen, onClose, onResourceCreated }: ResourceCreateModalProps) {
  const [resourceForm, setResourceForm] = useState<CreateResourceRequest>({
    name: '',
    displayName: '',
    description: '',
    resourceType: 'api',
    resourcePath: '',
    httpMethod: '',
    parentId: '',
    priority: 0,
  });
  const [loading, setLoading] = useState(false);

  const validateForm = () => {
    if (!resourceForm.name.trim()) {
      toast.error('资源名称不能为空');
      return false;
    }
    if (!resourceForm.resourcePath.trim()) {
      toast.error('资源路径不能为空');
      return false;
    }
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    setLoading(true);
    
    try {
      await resourceService.createResource(resourceForm);
      toast.success('创建资源成功');
      onResourceCreated();
      // 重置表单
      setResourceForm({
        name: '',
        displayName: '',
        description: '',
        resourceType: 'api',
        resourcePath: '',
        httpMethod: '',
        parentId: '',
        priority: 0,
      });
      onClose();
    } catch (err: any) {
      toast.error(err.message || '创建资源失败');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 backdrop-blur-sm">
      <div className="w-full max-w-2xl rounded-lg bg-white p-6 shadow-xl animate-in fade-in zoom-in duration-200 max-h-[90vh] overflow-y-auto">
        <div className="mb-6 flex items-center justify-between">
          <h2 className="text-xl font-bold text-gray-800">创建资源</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            ✕
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="create-resource-name">资源名称 *</Label>
            <Input
              id="create-resource-name"
              value={resourceForm.name}
              onChange={(e) => setResourceForm({ ...resourceForm, name: e.target.value })}
              placeholder="如: api:user:create 或 menu:home"
              disabled={loading}
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="create-display-name">显示名称</Label>
            <Input
              id="create-display-name"
              value={resourceForm.displayName}
              onChange={(e) => setResourceForm({ ...resourceForm, displayName: e.target.value })}
              disabled={loading}
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="create-description">描述</Label>
            <Textarea
              id="create-description"
              value={resourceForm.description}
              onChange={(e) => setResourceForm({ ...resourceForm, description: e.target.value })}
              disabled={loading}
            />
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="create-resource-type">资源类型 *</Label>
              <Select
                value={resourceForm.resourceType}
                onValueChange={(value: 'api' | 'menu') =>
                  setResourceForm({ ...resourceForm, resourceType: value })
                }
                disabled={loading}
              >
                <SelectTrigger id="create-resource-type">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="api">API资源</SelectItem>
                  <SelectItem value="menu">菜单资源</SelectItem>
                </SelectContent>
              </Select>
            </div>
            {resourceForm.resourceType === 'api' && (
              <div className="space-y-2">
                <Label htmlFor="create-http-method">HTTP方法</Label>
                <Select
                  value={resourceForm.httpMethod || undefined}
                  onValueChange={(value) => setResourceForm({ ...resourceForm, httpMethod: value })}
                  disabled={loading}
                >
                  <SelectTrigger id="create-http-method">
                    <SelectValue placeholder="选择HTTP方法" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="GET">GET</SelectItem>
                    <SelectItem value="POST">POST</SelectItem>
                    <SelectItem value="PUT">PUT</SelectItem>
                    <SelectItem value="DELETE">DELETE</SelectItem>
                    <SelectItem value="PATCH">PATCH</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            )}
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="create-resource-path">资源路径 *</Label>
            <Input
              id="create-resource-path"
              value={resourceForm.resourcePath}
              onChange={(e) => setResourceForm({ ...resourceForm, resourcePath: e.target.value })}
              placeholder="/api/v1/users"
              disabled={loading}
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="create-priority">优先级</Label>
            <Input
              id="create-priority"
              type="number"
              value={(resourceForm.priority ?? 0).toString()}
              onChange={(e) => setResourceForm({ ...resourceForm, priority: parseInt(e.target.value) || 0 })}
              disabled={loading}
            />
          </div>
          
          <div className="flex justify-end space-x-3 pt-4 border-t">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={loading}
            >
              取消
            </Button>
            <Button
              type="submit"
              disabled={loading}
              className="bg-orange-500 hover:bg-orange-600"
            >
              {loading ? '创建中...' : '创建资源'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

