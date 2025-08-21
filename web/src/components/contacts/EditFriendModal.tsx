'use client';

import { useState } from 'react';
import { X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Checkbox } from '@/components/ui/checkbox';
import type { Friendship, ContactTag } from '@/types/contacts';

interface EditFriendModalProps {
  friendship: Friendship;
  onClose: () => void;
  onSuccess: () => void;
  tags: ContactTag[];
}

export function EditFriendModal({ friendship, onClose, onSuccess, tags }: EditFriendModalProps) {
  const [nickname, setNickname] = useState(friendship.nickname || '');
  const [remark, setRemark] = useState(friendship.remark || '');
  const [isStarred, setIsStarred] = useState(friendship.is_starred);
  const [isMuted, setIsMuted] = useState(friendship.is_muted);
  const [isPinned, setIsPinned] = useState(friendship.is_pinned);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const { updateFriendship } = await import('@/service/contacts/api');
      
      await updateFriendship(friendship.id, {
        nickname: nickname || undefined,
        remark: remark || undefined,
        is_starred: isStarred,
        is_muted: isMuted,
        is_pinned: isPinned
      });
      
      onSuccess();
    } catch (error) {
      console.error('更新好友信息失败:', error);
      // 这里可以使用toast显示错误信息
      alert('更新失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">编辑好友信息</h2>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="w-4 h-4" />
          </Button>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label htmlFor="nickname">昵称</Label>
            <Input
              id="nickname"
              type="text"
              placeholder="给好友设置一个昵称"
              value={nickname}
              onChange={(e) => setNickname(e.target.value)}
            />
          </div>
          
          <div>
            <Label htmlFor="remark">备注</Label>
            <Textarea
              id="remark"
              placeholder="添加备注信息"
              value={remark}
              onChange={(e) => setRemark(e.target.value)}
              rows={3}
            />
          </div>
          
          <div className="space-y-3">
            <div className="flex items-center space-x-2">
              <Checkbox
                id="starred"
                checked={isStarred}
                onCheckedChange={setIsStarred}
              />
              <Label htmlFor="starred">星标好友</Label>
            </div>
            
            <div className="flex items-center space-x-2">
              <Checkbox
                id="pinned"
                checked={isPinned}
                onCheckedChange={setIsPinned}
              />
              <Label htmlFor="pinned">置顶显示</Label>
            </div>
            
            <div className="flex items-center space-x-2">
              <Checkbox
                id="muted"
                checked={isMuted}
                onCheckedChange={setIsMuted}
              />
              <Label htmlFor="muted">消息免打扰</Label>
            </div>
          </div>
          
          <div className="flex justify-end space-x-2">
            <Button type="button" variant="outline" onClick={onClose}>
              取消
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? '保存中...' : '保存'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}



