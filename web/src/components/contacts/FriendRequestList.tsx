'use client';

import { useState, useEffect } from 'react';
import { Check, X, User } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/service/utils';
import type { FriendRequest } from '@/types/contacts';
import { getFriendRequests, handleFriendRequest } from '@/service/contacts/api';
import { toast } from 'react-hot-toast';

interface FriendRequestListProps {
  onRequestHandled?: () => void;
}

export function FriendRequestList({ onRequestHandled }: FriendRequestListProps) {
  const [requests, setRequests] = useState<FriendRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [processingIds, setProcessingIds] = useState<Set<string>>(new Set());

  useEffect(() => {
    loadFriendRequests();
  }, []);

  const loadFriendRequests = async () => {
    try {
      setLoading(true);
      const result = await getFriendRequests('received', 'pending');
      setRequests(result.items);
    } catch (error) {
      console.error('加载好友请求失败:', error);
      toast.error('加载好友请求失败');
    } finally {
      setLoading(false);
    }
  };

  const handleRequest = async (requestId: string, action: 'accept' | 'reject') => {
    setProcessingIds(prev => new Set(prev).add(requestId));
    
    try {
      await handleFriendRequest(requestId, { action });
      
      // 从列表中移除已处理的请求
      setRequests(prev => prev.filter(req => req.id !== requestId));
      
      toast.success(action === 'accept' ? '已接受好友请求' : '已拒绝好友请求');
      
      if (onRequestHandled) {
        onRequestHandled();
      }
    } catch (error) {
      console.error('处理好友请求失败:', error);
      toast.error('处理请求失败');
    } finally {
      setProcessingIds(prev => {
        const newSet = new Set(prev);
        newSet.delete(requestId);
        return newSet;
      });
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
        <span className="ml-2 text-sm text-gray-500">加载中...</span>
      </div>
    );
  }

  if (requests.length === 0) {
    return (
      <div className="text-center py-8">
        <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <User className="w-8 h-8 text-gray-400" />
        </div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">暂无好友请求</h3>
        <p className="text-gray-500">当有人向您发送好友请求时，会在这里显示</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        好友请求 ({requests.length})
      </h3>
      
      {requests.map((request) => (
        <div key={request.id} className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 rounded-full bg-gray-200 flex items-center justify-center">
                {request.user?.avatar ? (
                  <img
                    src={request.user.avatar}
                    alt={request.user.username}
                    className="w-12 h-12 rounded-full object-cover"
                  />
                ) : (
                  <span className="text-lg font-medium text-gray-600">
                    {request.user?.username?.charAt(0).toUpperCase()}
                  </span>
                )}
              </div>
              
              <div className="flex-1">
                <div className="flex items-center space-x-2">
                  <h4 className="text-sm font-medium text-gray-900">
                    {request.user?.username}
                  </h4>
                  {request.source && (
                    <Badge variant="outline" className="text-xs">
                      {request.source === 'search' ? '搜索添加' : request.source}
                    </Badge>
                  )}
                </div>
                
                {request.verification_message && (
                  <p className="text-sm text-gray-600 mt-1">
                    "{request.verification_message}"
                  </p>
                )}
                
                <p className="text-xs text-gray-400 mt-1">
                  {new Date(request.requested_at).toLocaleString()}
                </p>
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              <Button
                size="sm"
                variant="outline"
                onClick={() => handleRequest(request.id, 'reject')}
                disabled={processingIds.has(request.id)}
                className="text-red-600 hover:text-red-700 hover:bg-red-50"
              >
                <X className="w-4 h-4 mr-1" />
                拒绝
              </Button>
              
              <Button
                size="sm"
                onClick={() => handleRequest(request.id, 'accept')}
                disabled={processingIds.has(request.id)}
              >
                <Check className="w-4 h-4 mr-1" />
                接受
              </Button>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
