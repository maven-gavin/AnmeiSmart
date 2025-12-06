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

  if (!isOpen) return null;

  return (
    <Card className="w-full h-[600px] flex flex-col shadow-lg">
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
