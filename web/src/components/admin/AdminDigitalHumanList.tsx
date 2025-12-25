'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  Eye, 
  ToggleLeft,
  ToggleRight,
  User, 
  Building, 
  Zap,
  Shield,
  Bot,
  MoreVertical,
  AlertTriangle
} from 'lucide-react';
import { normalizeAvatarUrl } from '@/utils/avatarUrl';
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
import { formatDistanceToNow } from 'date-fns';
import { zhCN } from 'date-fns/locale';

interface DigitalHuman {
  id: string;
  name: string;
  avatar?: string;
  description?: string;
  type: 'personal' | 'business' | 'specialized' | 'system';
  status: 'active' | 'inactive' | 'maintenance';
  is_system_created: boolean;
  user?: {
    id: string;
    username: string;
    email: string;
  } | null;
  last_active_at?: string;
  agent_count?: number;
  created_at: string;
  updated_at: string;
}

interface AdminDigitalHumanListProps {
  digitalHumans: DigitalHuman[];
  onSelect: (digitalHumanId: string) => void;
  onStatusToggle: (digitalHumanId: string, newStatus: string) => void;
  currentUserId?: string;
}

export default function AdminDigitalHumanList({
  digitalHumans,
  onSelect,
  onStatusToggle,
  currentUserId
}: AdminDigitalHumanListProps) {
  const [statusDialogOpen, setStatusDialogOpen] = useState(false);
  const [selectedDigitalHuman, setSelectedDigitalHuman] = useState<DigitalHuman | null>(null);
  const [targetStatus, setTargetStatus] = useState<string>('');

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

  const handleStatusToggleClick = (digitalHuman: DigitalHuman, newStatus: string) => {
    setSelectedDigitalHuman(digitalHuman);
    setTargetStatus(newStatus);
    setStatusDialogOpen(true);
  };

  const handleConfirmStatusToggle = () => {
    if (selectedDigitalHuman && targetStatus) {
      onStatusToggle(selectedDigitalHuman.id, targetStatus);
    }
    setStatusDialogOpen(false);
    setSelectedDigitalHuman(null);
    setTargetStatus('');
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return '从未';
    return formatDistanceToNow(new Date(dateString), { 
      addSuffix: true, 
      locale: zhCN 
    });
  };

  const getStatusToggleOptions = (currentStatus: string) => {
    const options = [];
    if (currentStatus !== 'active') {
      options.push({ status: 'active', label: '激活', color: 'text-green-600' });
    }
    if (currentStatus !== 'inactive') {
      options.push({ status: 'inactive', label: '停用', color: 'text-red-600' });
    }
    if (currentStatus !== 'maintenance') {
      options.push({ status: 'maintenance', label: '维护', color: 'text-yellow-600' });
    }
    return options;
  };

  if (digitalHumans.length === 0) {
    return (
      <div className="p-8 text-center">
        <Bot className="h-16 w-16 mx-auto text-gray-400 mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">暂无数字人</h3>
        <p className="text-gray-500">系统中还没有任何数字人</p>
      </div>
    );
  }

  return (
    <div className="overflow-hidden">
      {/* 表格头部 */}
      <div className="bg-gray-50 px-6 py-3 border-b">
        <div className="grid grid-cols-12 gap-4 text-sm font-medium text-gray-500">
          <div className="col-span-3">数字人信息</div>
          <div className="col-span-2">所属用户</div>
          <div className="col-span-2">类型/状态</div>
          <div className="col-span-2">统计数据</div>
          <div className="col-span-2">最后活跃</div>
          <div className="col-span-1">操作</div>
        </div>
      </div>

      {/* 表格内容 */}
      <div className="divide-y divide-gray-200">
        {digitalHumans.map((digitalHuman) => (
          <div
            key={digitalHuman.id}
            className="px-6 py-4 hover:bg-gray-50 transition-colors"
          >
            <div className="grid grid-cols-12 gap-4 items-center">
              {/* 数字人信息 */}
              <div className="col-span-3">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-orange-400 to-orange-600 flex items-center justify-center text-white font-semibold relative overflow-hidden">
                    {(() => {
                      const avatarUrl = normalizeAvatarUrl(digitalHuman.avatar);
                      // 业务规则：只看 avatarUrl 是否为空
                      // - 有 avatarUrl：只显示图片（即使加载失败出现碎图也接受）
                      // - 无 avatarUrl：显示名字首字母
                      return avatarUrl ? (
                        <img
                          src={avatarUrl}
                          alt={digitalHuman.name}
                          className="w-full h-full rounded-full object-cover"
                        />
                      ) : (
                        digitalHuman.name.charAt(0).toUpperCase()
                      );
                    })()}
                  </div>
                  <div className="min-w-0">
                    <div className="flex items-center space-x-2">
                      <h3 className="font-semibold text-gray-900 truncate">
                        {digitalHuman.name}
                      </h3>
                      {digitalHuman.is_system_created && (
                        <Shield className="h-4 w-4 text-blue-500" aria-label="系统创建" />
                      )}
                    </div>
                    <p className="text-sm text-gray-600 truncate">
                      {digitalHuman.description || '暂无描述'}
                    </p>
                  </div>
                </div>
              </div>

              {/* 所属用户 */}
              <div className="col-span-2">
                <div className="text-sm">
                  <div className="font-medium text-gray-900">{digitalHuman.user?.username || '-'}</div>
                  <div className="text-gray-500 truncate">{digitalHuman.user?.email || '-'}</div>
                </div>
              </div>

              {/* 类型/状态 */}
              <div className="col-span-2">
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    {getTypeIcon(digitalHuman.type)}
                    <span className="text-sm text-gray-600">
                      {getTypeLabel(digitalHuman.type)}
                    </span>
                  </div>
                  <Badge className={getStatusColor(digitalHuman.status)}>
                    {getStatusLabel(digitalHuman.status)}
                  </Badge>
                </div>
              </div>

              {/* 统计数据 */}
              <div className="col-span-2">
                <div className="text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-500">智能体:</span>
                    <span className="font-medium">{digitalHuman.agent_count || 0}</span>
                  </div>
                </div>
              </div>

              {/* 最后活跃 */}
              <div className="col-span-2">
                <div className="text-sm text-gray-600">
                  {formatDate(digitalHuman.last_active_at)}
                </div>
              </div>

              {/* 操作 */}
              <div className="col-span-1">
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                      <MoreVertical className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem onClick={() => onSelect(digitalHuman.id)}>
                      <Eye className="h-4 w-4 mr-2" />
                      查看详情
                    </DropdownMenuItem>
                    
                    {getStatusToggleOptions(digitalHuman.status).map((option) => (
                      <DropdownMenuItem 
                        key={option.status}
                        onClick={() => handleStatusToggleClick(digitalHuman, option.status)}
                        className={option.color}
                      >
                        {digitalHuman.status === 'active' ? (
                          <ToggleLeft className="h-4 w-4 mr-2" />
                        ) : (
                          <ToggleRight className="h-4 w-4 mr-2" />
                        )}
                        {option.label}
                      </DropdownMenuItem>
                    ))}
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* 状态切换确认对话框 */}
      <AlertDialog open={statusDialogOpen} onOpenChange={setStatusDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center space-x-2">
              <AlertTriangle className="h-5 w-5 text-orange-500" />
              <span>确认状态变更</span>
            </AlertDialogTitle>
            <AlertDialogDescription>
              您确定要将数字人 "{selectedDigitalHuman?.name}" 的状态更改为 "
              {getStatusLabel(targetStatus)}" 吗？
              <br />
              <br />
              {targetStatus === 'inactive' && (
                <span className="text-red-600">
                  ⚠️ 停用后，该数字人将无法响应用户消息，相关功能将被禁用。
                </span>
              )}
              {targetStatus === 'maintenance' && (
                <span className="text-yellow-600">
                  ⚠️ 维护模式下，数字人功能将受限，仅管理员可以访问。
                </span>
              )}
              {targetStatus === 'active' && (
                <span className="text-green-600">
                  ✅ 激活后，数字人将恢复正常功能。
                </span>
              )}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>取消</AlertDialogCancel>
            <AlertDialogAction 
              onClick={handleConfirmStatusToggle}
              className={
                targetStatus === 'inactive' ? 'bg-red-600 hover:bg-red-700' : 
                targetStatus === 'maintenance' ? 'bg-yellow-600 hover:bg-yellow-700' : 
                'bg-green-600 hover:bg-green-700'
              }
            >
              确认变更
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
