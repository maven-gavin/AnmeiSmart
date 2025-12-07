'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  X,
  Users,
  Search,
  UserPlus,
} from 'lucide-react';
import { useAuthContext } from '@/contexts/AuthContext';
import {
  getConversationParticipants,
  addConversationParticipant,
  removeConversationParticipant,
} from '@/service/chatService';
import { ChatApiService } from '@/service/chat/api';
import { getFriends } from '@/service/contacts/api';
import type { Friendship } from '@/types/contacts';
import type { ConversationParticipant } from '@/service/chat';

interface ConversationParticipantsPanelProps {
  conversationId: string;
  isOpen: boolean;
  onClose: () => void;
}

// 获取角色颜色（owner/admin/member/guest）
const getRoleColor = (role: ConversationParticipant['role']) => {
  switch (role) {
    case 'owner':
      return 'bg-blue-100 text-blue-800';
    case 'admin':
      return 'bg-purple-100 text-purple-800';
    case 'member':
      return 'bg-green-100 text-green-800';
    case 'guest':
    default:
      return 'bg-gray-100 text-gray-800';
  }
};

// 获取角色名称
const getRoleName = (role: ConversationParticipant['role']) => {
  switch (role) {
    case 'owner':
      return '所有者';
    case 'admin':
      return '管理员';
    case 'member':
      return '成员';
    case 'guest':
    default:
      return '访客';
  }
};

export function ConversationParticipantsPanel({
  conversationId,
  isOpen,
  onClose,
}: ConversationParticipantsPanelProps) {
  const { user } = useAuthContext();

  const [participants, setParticipants] = useState<ConversationParticipant[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [searchQuery, setSearchQuery] = useState('');
  // 搜索结果显示的好友信息（从好友关系表查询）
  const [searchResults, setSearchResults] = useState<Array<{
    id: string;
    username: string;
    avatar?: string;
  }>>([]);
  const [searching, setSearching] = useState(false);

  // 加载会话参与者（来自 conversation_participants 表）
  useEffect(() => {
    if (!isOpen) return;
    if (!conversationId) return;

    let cancelled = false;

    const loadParticipants = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await getConversationParticipants(conversationId);
        if (!cancelled) {
          setParticipants(data);
        }
      } catch (e) {
        if (!cancelled) {
          console.error('加载会话参与者失败:', e);
          setError('加载参与者失败，请稍后重试');
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    loadParticipants();

    return () => {
      cancelled = true;
    };
  }, [conversationId, isOpen]);

  // 搜索好友，用于添加为参与者（从好友关系表查询）
  useEffect(() => {
    if (!isOpen || !user) return;

    const query = searchQuery.trim();
    if (query.length < 2) {
      setSearchResults([]);
      return;
    }

    let cancelled = false;

    const doSearch = async () => {
      setSearching(true);
      try {
        // 使用 getFriends API，从好友关系表查询，支持搜索参数
        const result = await getFriends({
          search: query,
          status: 'accepted', // 只查询已接受的好友关系
          page: 1,
          size: 10,
        });
        
        if (!cancelled && result?.items) {
          // 从 Friendship 中提取好友信息
          // 后端已经处理了双向关系，friend 字段始终表示当前用户的好友
          const friends = result.items
            .filter((friendship: Friendship) => {
              // 只保留已接受的好友关系
              return friendship.status === 'accepted' && friendship.friend;
            })
            .map((friendship: Friendship) => {
              const friendInfo = friendship.friend;
              return {
                id: friendInfo?.id || '',
                username: friendInfo?.username || '未知用户',
                avatar: friendInfo?.avatar,
              };
            })
            .filter(f => f.id); // 过滤掉无效的好友信息
          
          setSearchResults(friends);
        }
      } catch (e) {
        if (!cancelled) {
          console.error('搜索好友失败:', e);
        }
      } finally {
        if (!cancelled) {
          setSearching(false);
        }
      }
    };

    // 简单防抖：200ms
    const timer = setTimeout(doSearch, 200);

    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [searchQuery, isOpen, user]);

  const handleAddParticipant = useCallback(
    async (userId: string) => {
      if (!conversationId || !userId) return;

      try {
        // 先获取会话详情，检查聊天模式
        const conversation = await ChatApiService.getConversationDetails(conversationId);
        if (!conversation) {
          setError('会话不存在');
          return;
        }

        // 如果会话是 single 模式，先更新为 group 模式
        if (conversation.chat_mode === 'single') {
          await ChatApiService.updateConversation(conversationId, {
            chat_mode: 'group',
          });
        }

        // 添加参与者
        const created = await addConversationParticipant(conversationId, userId, 'member');
        if (!created) return;

        setParticipants(prev => {
          if (prev.some(p => p.userId === created.userId)) {
            return prev;
          }
          return [...prev, created];
        });
      } catch (e) {
        console.error('添加参与者失败:', e);
        setError('添加参与者失败，请稍后重试');
      }
    },
    [conversationId]
  );

  const handleRemoveParticipant = useCallback(
    async (participantId: string) => {
      if (!conversationId || !participantId) return;

      try {
        await removeConversationParticipant(conversationId, participantId);
        setParticipants(prev => prev.filter(p => p.id !== participantId));
      } catch (e) {
        console.error('移除参与者失败:', e);
        setError('移除参与者失败，请稍后重试');
      }
    },
    [conversationId]
  );

  // 当前用户是否是会话参与者中的 owner/admin，用于前端按钮权限控制（后端仍会做最终校验）
  const canManageParticipants = participants.some(p => {
    if (!user || !p.userId) return false;
    if (p.userId !== user.id) return false;
    return p.role === 'owner' || p.role === 'admin';
  });

  // 过滤参与者列表（按名称）
  const filteredParticipants = participants.filter(p => {
    const name = p.userName || '';
    return name.toLowerCase().includes(searchQuery.toLowerCase());
  });

  // 搜索结果已经是好友关系表中的好友，无需再过滤
  const friendSearchResults = searchResults;

  if (!isOpen) return null;

  return (
    <Card className="w-full h-[600px] flex flex-col shadow-lg">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-medium flex items-center">
            <Users className="w-5 h-5 mr-2" />
            参与者
          </CardTitle>
          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            className="h-8 w-8 p-0"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>

      <CardContent className="flex-1 overflow-y-auto space-y-6">
        {/* 参与者管理 */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium text-gray-700 flex items-center">
              <Users className="w-4 h-4 mr-2" />
              参与者 ({participants.length})
            </h3>
          </div>

          {/* 搜索参与者（搜索好友后添加） */}
          <div className="space-y-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <Input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="搜索好友并添加为参与者..."
                className="pl-10"
              />
            </div>

            {searchQuery.trim().length >= 2 && (
              <div className="mt-1 max-h-40 overflow-y-auto rounded-md border bg-white shadow-sm">
                {searching ? (
                  <div className="px-3 py-2 text-xs text-gray-400">
                    正在搜索好友...
                  </div>
                ) : friendSearchResults.length === 0 ? (
                  <div className="px-3 py-2 text-xs text-gray-400">
                    未找到匹配的好友
                  </div>
                ) : (
                  friendSearchResults.map((result) => {
                    const alreadyInConversation = participants.some(
                      (p) => p.userId === result.id
                    );

                    return (
                      <div
                        key={result.id}
                        className="flex items-center justify-between px-3 py-2 hover:bg-gray-50"
                      >
                        <div className="flex items-center space-x-3">
                          <div className="w-7 h-7 rounded-full bg-gray-200 flex items-center justify-center text-xs font-medium">
                            {(result.username || '友').charAt(0)}
                          </div>
                          <div className="text-xs">
                            <div className="font-medium text-gray-800">
                              {result.username}
                            </div>
                            <div className="text-[11px] text-gray-400">
                              好友
                            </div>
                          </div>
                        </div>
                        <Button
                          variant="outline"
                          size="sm"
                          className="h-7 px-2 text-xs"
                          disabled={alreadyInConversation || !canManageParticipants}
                          onClick={() => handleAddParticipant(result.id)}
                        >
                          <UserPlus className="w-3 h-3 mr-1" />
                          {alreadyInConversation ? '已在会话中' : '添加'}
                        </Button>
                      </div>
                    );
                  })
                )}
              </div>
            )}
          </div>

          {/* 错误提示 */}
          {error && (
            <div className="text-xs text-red-500">
              {error}
            </div>
          )}

          {/* 参与者列表 */}
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {loading && (
              <div className="px-2 py-3 text-xs text-gray-400">
                正在加载参与者...
              </div>
            )}
            {!loading && filteredParticipants.length === 0 && (
              <div className="px-2 py-3 text-xs text-gray-400">
                暂无参与者
              </div>
            )}
            {filteredParticipants.map((participant) => {
              const displayName = participant.userName || '未知用户';
              const canRemove =
                canManageParticipants &&
                participant.role !== 'owner' &&
                (!user || participant.userId !== user.id);

              return (
                <div
                  key={participant.id}
                  className="flex items-center justify-between p-2 bg-gray-50 rounded-md hover:bg-gray-100"
                >
                  <div className="flex items-center space-x-3">
                    <div className="relative">
                      <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center">
                        <span className="text-xs font-medium">
                          {displayName.charAt(0)}
                        </span>
                      </div>
                    </div>

                    <div>
                      <div className="text-sm font-medium">
                        {displayName}
                      </div>
                      <Badge
                        variant="secondary"
                        className={`text-xs ${getRoleColor(participant.role)}`}
                      >
                        {getRoleName(participant.role)}
                      </Badge>
                    </div>
                  </div>

                  {canRemove && (
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-6 w-6 p-0 text-gray-400 hover:text-red-500"
                      onClick={() => handleRemoveParticipant(participant.id)}
                    >
                      <X className="w-3 h-3" />
                    </Button>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
