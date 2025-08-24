'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { 
  X, 
  Settings, 
  UserPlus, 
  Search, 
  Bell, 
  BellOff,
  Pin,
  Users,
  MessageSquare,
  Volume2,
  VolumeX,
  Shield,
  Clock
} from 'lucide-react';

interface ConversationSettingsPanelProps {
  conversationId: string;
  isOpen: boolean;
  onClose: () => void;
  onSettingsChange?: (settings: ConversationSettings) => void;
}

interface ConversationSettings {
  isPinned: boolean;
  isNotificationMuted: boolean;
  isSoundMuted: boolean;
  isPrivate: boolean;
  autoDeleteDays: number | null;
}

interface Participant {
  id: string;
  name: string;
  avatar?: string;
  role: 'customer' | 'consultant' | 'ai' | 'admin';
  isOnline: boolean;
  lastSeen?: string;
}

export function ConversationSettingsPanel({ 
  conversationId, 
  isOpen, 
  onClose,
  onSettingsChange
}: ConversationSettingsPanelProps) {
  // 设置状态
  const [settings, setSettings] = useState<ConversationSettings>({
    isPinned: false,
    isNotificationMuted: false,
    isSoundMuted: false,
    isPrivate: false,
    autoDeleteDays: null
  });

  // 参与者管理状态
  const [participants, setParticipants] = useState<Participant[]>([
    {
      id: '1',
      name: '张三',
      avatar: '/avatars/user1.png',
      role: 'customer',
      isOnline: true
    },
    {
      id: '2',
      name: 'AI助手',
      avatar: '/avatars/ai.png',
      role: 'ai',
      isOnline: true
    }
  ]);

  const [searchParticipant, setSearchParticipant] = useState('');
  const [showAddParticipant, setShowAddParticipant] = useState(false);

  // 更新设置
  const updateSetting = <K extends keyof ConversationSettings>(
    key: K, 
    value: ConversationSettings[K]
  ) => {
    const newSettings = { ...settings, [key]: value };
    setSettings(newSettings);
    if (onSettingsChange) {
      onSettingsChange(newSettings);
    }
  };

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
    <Card className="w-96 h-[600px] flex flex-col shadow-lg">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-medium flex items-center">
            <Settings className="w-5 h-5 mr-2" />
            会话设置
          </CardTitle>
          <Button variant="ghost" size="sm" onClick={onClose} className="h-8 w-8 p-0">
            <X className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      
      <CardContent className="flex-1 overflow-y-auto space-y-6">
        {/* 基本设置 */}
        <div className="space-y-4">
          <h3 className="text-sm font-medium text-gray-700 flex items-center">
            <MessageSquare className="w-4 h-4 mr-2" />
            基本设置
          </h3>
          
          {/* 置顶聊天 */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Pin className="w-4 h-4 text-gray-500" />
              <span className="text-sm">置顶聊天</span>
            </div>
            <Switch
              checked={settings.isPinned}
              onCheckedChange={(checked) => updateSetting('isPinned', checked)}
            />
          </div>
          
          {/* 私密会话 */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Shield className="w-4 h-4 text-gray-500" />
              <span className="text-sm">私密会话</span>
            </div>
            <Switch
              checked={settings.isPrivate}
              onCheckedChange={(checked) => updateSetting('isPrivate', checked)}
            />
          </div>
        </div>

        {/* 通知设置 */}
        <div className="space-y-4">
          <h3 className="text-sm font-medium text-gray-700 flex items-center">
            <Bell className="w-4 h-4 mr-2" />
            通知设置
          </h3>
          
          {/* 消息免打扰 */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              {settings.isNotificationMuted ? (
                <BellOff className="w-4 h-4 text-gray-500" />
              ) : (
                <Bell className="w-4 h-4 text-gray-500" />
              )}
              <span className="text-sm">消息免打扰</span>
            </div>
            <Switch
              checked={settings.isNotificationMuted}
              onCheckedChange={(checked) => updateSetting('isNotificationMuted', checked)}
            />
          </div>
          
          {/* 声音提醒 */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              {settings.isSoundMuted ? (
                <VolumeX className="w-4 h-4 text-gray-500" />
              ) : (
                <Volume2 className="w-4 h-4 text-gray-500" />
              )}
              <span className="text-sm">声音提醒</span>
            </div>
            <Switch
              checked={!settings.isSoundMuted}
              onCheckedChange={(checked) => updateSetting('isSoundMuted', !checked)}
            />
          </div>
        </div>

        {/* 自动清理设置 */}
        <div className="space-y-4">
          <h3 className="text-sm font-medium text-gray-700 flex items-center">
            <Clock className="w-4 h-4 mr-2" />
            自动清理
          </h3>
          
          <div className="space-y-2">
            <label className="text-sm text-gray-600">自动删除消息（天）</label>
            <select
              value={settings.autoDeleteDays || ''}
              onChange={(e) => updateSetting('autoDeleteDays', 
                e.target.value ? parseInt(e.target.value) : null
              )}
              className="w-full p-2 border border-gray-200 rounded-md text-sm"
            >
              <option value="">不自动删除</option>
              <option value="7">7天</option>
              <option value="30">30天</option>
              <option value="90">90天</option>
              <option value="365">1年</option>
            </select>
          </div>
        </div>

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
          <div className="space-y-2 max-h-48 overflow-y-auto">
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
                      <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-green-400 rounded-full border-2 border-white"></div>
                    )}
                  </div>
                  
                  <div>
                    <div className="text-sm font-medium">{participant.name}</div>
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

        {/* 危险操作 */}
        <div className="space-y-4 pt-4 border-t border-gray-200">
          <h3 className="text-sm font-medium text-red-600">危险操作</h3>
          
          <div className="space-y-2">
            <Button variant="destructive" size="sm" className="w-full">
              清空聊天记录
            </Button>
            <Button variant="outline" size="sm" className="w-full text-red-600 border-red-200 hover:bg-red-50">
              退出会话
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
