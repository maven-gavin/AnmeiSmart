'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { resourceService, Resource, UpdateResourceRequest } from '@/service/resourceService';
import toast from 'react-hot-toast';

interface ResourceEditModalProps {
  isOpen: boolean;
  onClose: () => void;
  resource: Resource | null;
  onResourceUpdated: () => void;
}

export default function ResourceEditModal({ isOpen, onClose, resource, onResourceUpdated }: ResourceEditModalProps) {
  const [resourceForm, setResourceForm] = useState<UpdateResourceRequest>({
    displayName: '',
    description: '',
    resourcePath: '',
    httpMethod: '',
    priority: 0,
  });
  const [loading, setLoading] = useState(false);

  // 初始化表单数据
  useEffect(() => {
    if (resource) {
      setResourceForm({
        displayName: resource.displayName || '',
        description: resource.description || '',
        resourcePath: resource.resourcePath,
        httpMethod: resource.httpMethod || '',
        priority: resource.priority,
      });
    }
  }, [resource]);

  const validateForm = () => {
    if (!resourceForm.resourcePath?.trim()) {
      toast.error('资源路径不能为空');
      return false;
    }
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!resource || !validateForm()) {
      return;
    }
    
    setLoading(true);
    
    try {
      await resourceService.updateResource(resource.id, resourceForm);
      toast.success('更新资源成功');
      onResourceUpdated();
      onClose();
    } catch (err: any) {
      toast.error(err.message || '更新资源失败');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen || !resource) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 backdrop-blur-sm">
      <div className="w-full max-w-2xl rounded-lg bg-white p-6 shadow-xl animate-in fade-in zoom-in duration-200 max-h-[90vh] overflow-y-auto">
        <div className="mb-6 flex items-center justify-between">
          <h2 className="text-xl font-bold text-gray-800">编辑资源</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            ✕
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="edit-resource-name">资源名称</Label>
            <Input
              id="edit-resource-name"
              value={resource.name}
              disabled
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="edit-display-name">显示名称</Label>
            <Input
              id="edit-display-name"
              value={resourceForm.displayName}
              onChange={(e) => setResourceForm({ ...resourceForm, displayName: e.target.value })}
              disabled={loading}
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="edit-description">描述</Label>
            <Textarea
              id="edit-description"
              value={resourceForm.description}
              onChange={(e) => setResourceForm({ ...resourceForm, description: e.target.value })}
              disabled={loading}
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="edit-resource-path">资源路径 *</Label>
            <Input
              id="edit-resource-path"
              value={resourceForm.resourcePath}
              onChange={(e) => setResourceForm({ ...resourceForm, resourcePath: e.target.value })}
              disabled={loading}
            />
          </div>
          
          {resource.resourceType === 'api' && (
            <div className="space-y-2">
              <Label htmlFor="edit-http-method">HTTP方法</Label>
              <Select
                value={resourceForm.httpMethod || undefined}
                onValueChange={(value) => setResourceForm({ ...resourceForm, httpMethod: value })}
                disabled={loading}
              >
                <SelectTrigger id="edit-http-method">
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
          
          <div className="space-y-2">
            <Label htmlFor="edit-priority">优先级</Label>
            <Input
              id="edit-priority"
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
              {loading ? '更新中...' : '保存更改'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

