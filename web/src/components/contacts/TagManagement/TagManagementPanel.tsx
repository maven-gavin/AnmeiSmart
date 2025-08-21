'use client';

import { useState, useEffect } from 'react';
import { Plus, Edit, Trash2, Tag as TagIcon } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { CreateTagModal } from './CreateTagModal';
import type { ContactTag, TagCategory } from '@/types/contacts';
import { getContactTags, deleteContactTag } from '@/service/contacts/api';
import { toast } from 'react-hot-toast';

interface TagManagementPanelProps {
  onClose?: () => void;
}

export function TagManagementPanel({ onClose }: TagManagementPanelProps) {
  const [tags, setTags] = useState<ContactTag[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingTag, setEditingTag] = useState<ContactTag | null>(null);

  useEffect(() => {
    loadTags();
  }, []);

  const loadTags = async () => {
    try {
      setLoading(true);
      const result = await getContactTags();
      setTags(result);
    } catch (error) {
      console.error('加载标签失败:', error);
      toast.error('加载标签失败');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteTag = async (tagId: string, tagName: string) => {
    if (!confirm(`确定要删除标签"${tagName}"吗？删除后相关的好友分类将被清除。`)) {
      return;
    }

    try {
      await deleteContactTag(tagId);
      toast.success('标签删除成功');
      loadTags();
    } catch (error) {
      console.error('删除标签失败:', error);
      toast.error('删除标签失败');
    }
  };

  const handleCreateSuccess = () => {
    setShowCreateModal(false);
    loadTags();
    toast.success('标签创建成功');
  };

  const handleEditSuccess = () => {
    setEditingTag(null);
    loadTags();
    toast.success('标签更新成功');
  };

  // 筛选标签
  const filteredTags = tags.filter(tag => {
    const matchesSearch = !searchQuery || 
      tag.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      tag.description?.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesCategory = categoryFilter === 'all' || tag.category === categoryFilter;
    
    return matchesSearch && matchesCategory;
  });

  // 按分类分组
  const groupedTags = filteredTags.reduce((groups, tag) => {
    const category = tag.category;
    if (!groups[category]) {
      groups[category] = [];
    }
    groups[category].push(tag);
    return groups;
  }, {} as Record<string, ContactTag[]>);

  const categoryNames: Record<TagCategory, string> = {
    work: '工作关系',
    personal: '个人关系',
    business: '商务关系',
    medical: '医疗相关',
    custom: '自定义'
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
        <span className="ml-2 text-sm text-gray-500">加载中...</span>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-gray-900">标签管理</h2>
        <Button onClick={() => setShowCreateModal(true)}>
          <Plus className="w-4 h-4 mr-2" />
          创建标签
        </Button>
      </div>

      {/* 搜索和筛选 */}
      <div className="flex items-center space-x-4 mb-6">
        <div className="flex-1">
          <Input
            placeholder="搜索标签名称或描述..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        
        <div className="w-40">
          <Select value={categoryFilter} onValueChange={setCategoryFilter}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">所有分类</SelectItem>
              <SelectItem value="work">工作关系</SelectItem>
              <SelectItem value="business">商务关系</SelectItem>
              <SelectItem value="medical">医疗相关</SelectItem>
              <SelectItem value="personal">个人关系</SelectItem>
              <SelectItem value="custom">自定义</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* 标签列表 */}
      <div className="space-y-6">
        {Object.entries(groupedTags).map(([category, categoryTags]) => (
          <div key={category}>
            <h3 className="text-sm font-medium text-gray-700 mb-3">
              {categoryNames[category as TagCategory]} ({categoryTags.length})
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {categoryTags.map((tag) => (
                <div key={tag.id} className="flex items-center justify-between p-3 border border-gray-200 rounded-md hover:shadow-sm transition-shadow">
                  <div className="flex items-center space-x-3">
                    <div 
                      className="w-4 h-4 rounded-full"
                      style={{ backgroundColor: tag.color }}
                    />
                    
                    <div className="flex-1">
                      <div className="flex items-center space-x-2">
                        <span className="text-sm font-medium text-gray-900">{tag.name}</span>
                        {tag.is_system_tag && (
                          <Badge variant="outline" className="text-xs">系统</Badge>
                        )}
                      </div>
                      
                      {tag.description && (
                        <p className="text-xs text-gray-500 mt-1">{tag.description}</p>
                      )}
                      
                      <p className="text-xs text-gray-400 mt-1">
                        使用次数: {tag.usage_count}
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-1">
                    {!tag.is_system_tag && (
                      <>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setEditingTag(tag)}
                          className="h-8 w-8 p-0"
                        >
                          <Edit className="w-4 h-4" />
                        </Button>
                        
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDeleteTag(tag.id, tag.name)}
                          className="h-8 w-8 p-0 text-red-600 hover:text-red-700"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {filteredTags.length === 0 && (
        <div className="text-center py-8">
          <TagIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">暂无标签</h3>
          <p className="text-gray-500 mb-4">创建标签来更好地分类管理您的好友</p>
          <Button onClick={() => setShowCreateModal(true)}>
            <Plus className="w-4 h-4 mr-2" />
            创建第一个标签
          </Button>
        </div>
      )}

      {/* 创建标签弹窗 */}
      {showCreateModal && (
        <CreateTagModal
          onClose={() => setShowCreateModal(false)}
          onSuccess={handleCreateSuccess}
        />
      )}

      {/* 编辑标签弹窗 */}
      {editingTag && (
        <CreateTagModal
          tag={editingTag}
          onClose={() => setEditingTag(null)}
          onSuccess={handleEditSuccess}
        />
      )}
    </div>
  );
}
