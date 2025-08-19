'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  Edit, 
  Trash2, 
  Settings, 
  Bot, 
  User, 
  Building, 
  Zap,
  MoreVertical,
  Shield
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';

import type { DigitalHuman } from '@/types/digital-human';

interface DigitalHumanListProps {
  digitalHumans: DigitalHuman[];
  onEdit: (id: string) => void;
  onDelete: (id: string) => void;
  onConfigureAgents: (id: string) => void;
}

export default function DigitalHumanList({
  digitalHumans,
  onEdit,
  onDelete,
  onConfigureAgents
}: DigitalHumanListProps) {
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedDigitalHuman, setSelectedDigitalHuman] = useState<DigitalHuman | null>(null);

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'personal':
        return <User className="h-4 w-4" />;
      case 'business':
        return <Building className="h-4 w-4" />;
      case 'specialized':
        return <Zap className="h-4 w-4" />;
      case 'system':
        return <Shield className="h-4 w-4" />;
      default:
        return <Bot className="h-4 w-4" />;
    }
  };

  const getTypeLabel = (type: string) => {
    switch (type) {
      case 'personal':
        return '个人助手';
      case 'business':
        return '商务助手';
      case 'specialized':
        return '专业助手';
      case 'system':
        return '系统助手';
      default:
        return '未知类型';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'inactive':
        return 'bg-gray-100 text-gray-800';
      case 'maintenance':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'active':
        return '活跃';
      case 'inactive':
        return '停用';
      case 'maintenance':
        return '维护中';
      default:
        return '未知';
    }
  };

  const handleDeleteClick = (digitalHuman: DigitalHuman) => {
    setSelectedDigitalHuman(digitalHuman);
    setDeleteDialogOpen(true);
  };

  const handleConfirmDelete = () => {
    if (selectedDigitalHuman) {
      onDelete(selectedDigitalHuman.id);
    }
    setDeleteDialogOpen(false);
    setSelectedDigitalHuman(null);
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return '从未';
    return new Date(dateString).toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (digitalHumans.length === 0) {
    return (
      <div className="p-8 text-center">
        <Bot className="h-16 w-16 mx-auto text-gray-400 mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">还没有数字人</h3>
        <p className="text-gray-500 mb-6">创建您的第一个数字人助手，开始智能对话体验</p>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {digitalHumans.map((digitalHuman) => (
          <div
            key={digitalHuman.id}
            className="border rounded-lg p-6 hover:shadow-md transition-shadow"
          >
            {/* 头部信息 */}
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center space-x-3">
                <div className="w-12 h-12 rounded-full bg-gradient-to-br from-orange-400 to-orange-600 flex items-center justify-center text-white font-semibold">
                  {digitalHuman.avatar ? (
                    <img
                      src={digitalHuman.avatar}
                      alt={digitalHuman.name}
                      className="w-full h-full rounded-full object-cover"
                    />
                  ) : (
                    digitalHuman.name.charAt(0).toUpperCase()
                  )}
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900 flex items-center space-x-2">
                    <span>{digitalHuman.name}</span>
                    {digitalHuman.is_system_created && (
                      <Shield className="h-4 w-4 text-blue-500" title="系统创建" />
                    )}
                  </h3>
                  <div className="flex items-center space-x-2 mt-1">
                    {getTypeIcon(digitalHuman.type)}
                    <span className="text-sm text-gray-600">
                      {getTypeLabel(digitalHuman.type)}
                    </span>
                  </div>
                </div>
              </div>

              {/* 操作菜单 */}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                    <MoreVertical className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onClick={() => onEdit(digitalHuman.id)}>
                    <Edit className="h-4 w-4 mr-2" />
                    编辑
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => onConfigureAgents(digitalHuman.id)}>
                    <Settings className="h-4 w-4 mr-2" />
                    智能体配置
                  </DropdownMenuItem>
                  {!digitalHuman.is_system_created && (
                    <DropdownMenuItem 
                      onClick={() => handleDeleteClick(digitalHuman)}
                      className="text-red-600"
                    >
                      <Trash2 className="h-4 w-4 mr-2" />
                      删除
                    </DropdownMenuItem>
                  )}
                </DropdownMenuContent>
              </DropdownMenu>
            </div>

            {/* 描述 */}
            {digitalHuman.description && (
              <p className="text-sm text-gray-600 mb-4 line-clamp-2">
                {digitalHuman.description}
              </p>
            )}

            {/* 状态和统计 */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500">状态</span>
                <Badge className={getStatusColor(digitalHuman.status)}>
                  {getStatusLabel(digitalHuman.status)}
                </Badge>
              </div>

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-500">会话数</span>
                  <div className="font-semibold">{digitalHuman.conversation_count}</div>
                </div>
                <div>
                  <span className="text-gray-500">消息数</span>
                  <div className="font-semibold">{digitalHuman.message_count}</div>
                </div>
              </div>

              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-500">智能体</span>
                <span className="font-semibold">{digitalHuman.agent_count || 0} 个</span>
              </div>

              <div className="text-sm">
                <span className="text-gray-500">最后活跃</span>
                <div className="font-medium">{formatDate(digitalHuman.last_active_at)}</div>
              </div>
            </div>

            {/* 快速操作按钮 */}
            <div className="mt-6 flex space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => onEdit(digitalHuman.id)}
                className="flex-1"
              >
                <Edit className="h-4 w-4 mr-1" />
                编辑
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => onConfigureAgents(digitalHuman.id)}
                className="flex-1"
              >
                <Settings className="h-4 w-4 mr-1" />
                配置
              </Button>
            </div>
          </div>
        ))}
      </div>

      {/* 删除确认对话框 */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>确认删除</AlertDialogTitle>
            <AlertDialogDescription>
              您确定要删除数字人 "{selectedDigitalHuman?.name}" 吗？
              此操作不可撤销，相关的会话记录将被保留，但数字人将无法再使用。
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>取消</AlertDialogCancel>
            <AlertDialogAction onClick={handleConfirmDelete} className="bg-red-600 hover:bg-red-700">
              删除
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
