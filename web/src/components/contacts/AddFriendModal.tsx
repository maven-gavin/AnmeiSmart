'use client';

import { useState } from 'react';
import { X, Search, UserPlus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import type { UserSearchResult } from '@/types/contacts';

interface AddFriendModalProps {
  onClose: () => void;
  onSuccess: () => void;
}

export function AddFriendModal({ onClose, onSuccess }: AddFriendModalProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [verificationMessage, setVerificationMessage] = useState('');
  const [searchResults, setSearchResults] = useState<UserSearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [searching, setSearching] = useState(false);

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    
    setSearching(true);
    try {
      const { searchUsers } = await import('@/service/contacts/api');
      
      const results = await searchUsers({
        query: searchQuery.trim(),
        search_type: 'all',
        limit: 10
      });
      
      setSearchResults(results);
    } catch (error) {
      console.error('搜索用户失败:', error);
      // alert('搜索失败，请重试'); // apiClient 已处理错误提示
    } finally {
      setSearching(false);
    }
  };

  const handleAddFriend = async (userId: string) => {
    setLoading(true);
    try {
      const { sendFriendRequest } = await import('@/service/contacts/api');
      
      await sendFriendRequest({
        friend_id: userId,
        verification_message: verificationMessage || undefined,
        source: 'search'
      });
      
      onSuccess();
    } catch (error) {
      console.error('发送好友请求失败:', error);
      // alert('发送好友请求失败，请重试'); // apiClient 已处理错误提示
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await handleSearch();
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
        
        <div className="space-y-4">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="search">搜索用户</Label>
              <div className="flex space-x-2">
                <Input
                  id="search"
                  type="text"
                  placeholder="输入手机号、邮箱或用户名"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  required
                />
                <Button type="submit" disabled={searching || !searchQuery.trim()}>
                  <Search className="w-4 h-4 mr-2" />
                  {searching ? '搜索中...' : '搜索'}
                </Button>
              </div>
            </div>
          </form>
          
          {/* 搜索结果 */}
          {searchResults.length > 0 && (
            <div className="space-y-2">
              <Label>搜索结果</Label>
              <div className="max-h-60 overflow-y-auto space-y-2">
                {searchResults.map((user) => (
                  <div key={user.id} className="flex items-center justify-between p-3 border border-gray-200 rounded-md">
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center">
                        {user.avatar ? (
                          <img
                            src={user.avatar}
                            alt={user.username}
                            className="w-10 h-10 rounded-full object-cover"
                          />
                        ) : (
                          <span className="text-sm font-medium text-gray-600">
                            {user.username.charAt(0).toUpperCase()}
                          </span>
                        )}
                      </div>
                      
                      <div>
                        <p className="text-sm font-medium text-gray-900">{user.username}</p>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {user.roles.map(role => (
                            <Badge key={role} variant="secondary" className="text-xs">
                              {role}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    </div>
                    
                    <div>
                      {user.is_friend ? (
                        <Badge variant="outline" className="text-xs">
                          {user.friendship_status === 'pending' ? '待确认' : '已是好友'}
                        </Badge>
                      ) : (
                        <Button
                          size="sm"
                          onClick={() => handleAddFriend(user.id)}
                          disabled={loading}
                        >
                          <UserPlus className="w-4 h-4 mr-1" />
                          添加
                        </Button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
          
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
          </div>
        </div>
      </div>
    </div>
  );
}



