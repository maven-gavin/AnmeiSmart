'use client';

import { useState } from 'react';
import { X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';

interface AddFriendModalProps {
  onClose: () => void;
  onSuccess: () => void;
}

export function AddFriendModal({ onClose, onSuccess }: AddFriendModalProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [verificationMessage, setVerificationMessage] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    // TODO: 实现添加好友逻辑
    console.log('添加好友:', { searchQuery, verificationMessage });
    onSuccess();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">添加好友</h2>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="w-4 h-4" />
          </Button>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label htmlFor="search">搜索用户</Label>
            <Input
              id="search"
              type="text"
              placeholder="输入手机号、邮箱或用户名"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              required
            />
          </div>
          
          <div>
            <Label htmlFor="message">验证消息</Label>
            <Textarea
              id="message"
              placeholder="请输入验证消息（可选）"
              value={verificationMessage}
              onChange={(e) => setVerificationMessage(e.target.value)}
              rows={3}
            />
          </div>
          
          <div className="flex justify-end space-x-2">
            <Button type="button" variant="outline" onClick={onClose}>
              取消
            </Button>
            <Button type="submit" disabled={loading || !searchQuery.trim()}>
              {loading ? '搜索中...' : '搜索并添加'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}



