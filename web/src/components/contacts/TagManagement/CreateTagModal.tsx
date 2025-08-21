'use client';

import { useState } from 'react';
import { X, Palette } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import type { ContactTag, TagCategory } from '@/types/contacts';
import { createContactTag, updateContactTag } from '@/service/contacts/api';

interface CreateTagModalProps {
  tag?: ContactTag; // 如果提供了tag，则为编辑模式
  onClose: () => void;
  onSuccess: () => void;
}

// 预设颜色选项
const COLOR_OPTIONS = [
  '#3B82F6', '#8B5CF6', '#EC4899', '#10B981', '#F59E0B',
  '#EF4444', '#06B6D4', '#84CC16', '#F97316', '#6366F1'
];

export function CreateTagModal({ tag, onClose, onSuccess }: CreateTagModalProps) {
  const isEdit = !!tag;
  
  const [name, setName] = useState(tag?.name || '');
  const [description, setDescription] = useState(tag?.description || '');
  const [category, setCategory] = useState<TagCategory>(tag?.category || 'custom');
  const [color, setColor] = useState(tag?.color || '#3B82F6');
  const [icon, setIcon] = useState(tag?.icon || '');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const tagData = {
        name: name.trim(),
        description: description.trim() || undefined,
        category,
        color,
        icon: icon.trim() || undefined
      };

      if (isEdit && tag) {
        await updateContactTag(tag.id, tagData);
      } else {
        await createContactTag(tagData);
      }

      onSuccess();
    } catch (error) {
      console.error('保存标签失败:', error);
      alert('保存失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">
            {isEdit ? '编辑标签' : '创建标签'}
          </h2>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="w-4 h-4" />
          </Button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label htmlFor="name">标签名称 *</Label>
            <Input
              id="name"
              type="text"
              placeholder="输入标签名称"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              maxLength={50}
            />
          </div>

          <div>
            <Label htmlFor="description">标签描述</Label>
            <Textarea
              id="description"
              placeholder="添加标签描述（可选）"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
              maxLength={200}
            />
          </div>

          <div>
            <Label htmlFor="category">标签分类</Label>
            <Select value={category} onValueChange={(value) => setCategory(value as TagCategory)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="work">工作关系</SelectItem>
                <SelectItem value="business">商务关系</SelectItem>
                <SelectItem value="medical">医疗相关</SelectItem>
                <SelectItem value="personal">个人关系</SelectItem>
                <SelectItem value="custom">自定义</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label>标签颜色</Label>
            <div className="flex items-center space-x-2 mt-2">
              <div 
                className="w-8 h-8 rounded-full border-2 border-gray-300"
                style={{ backgroundColor: color }}
              />
              
              <div className="flex flex-wrap gap-2">
                {COLOR_OPTIONS.map((colorOption) => (
                  <button
                    key={colorOption}
                    type="button"
                    className="w-6 h-6 rounded-full border-2 border-gray-200 hover:border-gray-400 transition-colors"
                    style={{ backgroundColor: colorOption }}
                    onClick={() => setColor(colorOption)}
                  />
                ))}
              </div>
              
              <Input
                type="color"
                value={color}
                onChange={(e) => setColor(e.target.value)}
                className="w-12 h-8 p-0 border-0"
              />
            </div>
          </div>

          <div>
            <Label htmlFor="icon">图标标识</Label>
            <Input
              id="icon"
              type="text"
              placeholder="输入图标名称（可选）"
              value={icon}
              onChange={(e) => setIcon(e.target.value)}
              maxLength={50}
            />
            <p className="text-xs text-gray-500 mt-1">
              例如：star、heart、briefcase等
            </p>
          </div>

          <div className="flex justify-end space-x-2">
            <Button type="button" variant="outline" onClick={onClose}>
              取消
            </Button>
            <Button type="submit" disabled={loading || !name.trim()}>
              {loading ? '保存中...' : (isEdit ? '更新' : '创建')}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
