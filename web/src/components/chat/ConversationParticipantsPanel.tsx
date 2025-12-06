'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { 
  X,
  Users,
  UserPlus,
  Search,
} from 'lucide-react';

interface ConversationParticipantsPanelProps {
  conversationId: string;
  isOpen: boolean;
  onClose: () => void;
}

interface Participant {
  id: string;
  name: string;
  avatar?: string;
  role: 'customer' | 'consultant' | 'ai' | 'admin';
  isOnline: boolean;
  lastSeen?: string;
}

export function ConversationParticipantsPanel({
  conversationId,
  isOpen,
  onClose,
}: ConversationParticipantsPanelProps) {
  // 参与者管理状态（暂时使用静态数据，后续可接入接口）
  const [participants, setParticipants] = useState<Participant[]>([
    {
      id: '1',
      name: '张三',
      avatar: '/avatars/user1.png',
      role: 'customer',
      isOnline: true,
    },
    {
      id: '2',
      name: 'AI助手',
      avatar: '/avatars/ai.png',
      role: 'ai',
      isOnline: true,
    },
  ]);

  const [searchParticipant, setSearchParticipant] = useState('');
  const [showAddParticipant, setShowAddParticipant] = useState(false);

  // 获取角色颜色
  const getRoleColor = (role: Participant['role']) => {
    switch (role) {
      case 'ai':
        return 'bg-blue-100 text-blue-800';
      case 'consultant':
        return 'bg-green-100 text-green-800';
      case 'customer':
        return 'bg-gray-100 text-gray-800';
      case 'admin':
        return 'bg-purple-100 text-purple-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  // 获取角色名称
  const getRoleName = (role: Participant['role']) => {
    switch (role) {
      case 'ai':
        return 'AI助手';
      case 'consultant':
        return '顾问';
      case 'customer':
        return '客户';
      case 'admin':
        return '管理员';
      default:
        return '用户';
    }
  };

  // 移除参与者
  const removeParticipant = (participantId: string) => {
    setParticipants(prev => prev.filter(p => p.id !== participantId));
  };

  // 筛选参与者
  const filteredParticipants = participants.filter(p =>
    p.name.toLowerCase().includes(searchParticipant.toLowerCase())
  );

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
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowAddParticipant(!showAddParticipant)}
              className="h-8"
            >
              <UserPlus className="w-3 h-3 mr-1" />
              添加
            </Button>
          </div>

          {/* 搜索参与者 */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <Input
              type="text"
              value={searchParticipant}
              onChange={(e) => setSearchParticipant(e.target.value)}
              placeholder="搜索参与者..."
              className="pl-10"
            />
          </div>

          {/* 添加参与者表单 */}
          {showAddParticipant && (
            <div className="p-3 bg-gray-50 rounded-md space-y-2">
              <Input
                type="text"
                placeholder="输入用户名或邮箱"
                className="text-sm"
              />
              <div className="flex items-center justify-end space-x-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowAddParticipant(false)}
                >
                  取消
                </Button>
                <Button size="sm">
                  添加
                </Button>
              </div>
            </div>
          )}

          {/* 参与者列表 */}
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {filteredParticipants.map((participant) => (
              <div
                key={participant.id}
                className="flex items-center justify-between p-2 bg-gray-50 rounded-md hover:bg-gray-100"
              >
                <div className="flex items-center space-x-3">
                  <div className="relative">
                    <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center">
                      <span className="text-xs font-medium">
                        {participant.name.charAt(0)}
                      </span>
                    </div>
                    {participant.isOnline && (
                      <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-green-400 rounded-full border-2 border-white" />
                    )}
                  </div>

                  <div>
                    <div className="text-sm font-medium">
                      {participant.name}
                    </div>
                    <Badge
                      variant="secondary"
                      className={`text-xs ${getRoleColor(participant.role)}`}
                    >
                      {getRoleName(participant.role)}
                    </Badge>
                  </div>
                </div>

                {participant.role !== 'ai' && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removeParticipant(participant.id)}
                    className="h-6 w-6 p-0 text-gray-400 hover:text-red-500"
                  >
                    <X className="w-3 h-3" />
                  </Button>
                )}
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}


