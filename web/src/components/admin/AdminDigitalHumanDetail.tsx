'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { 
  ArrowLeft, 
  User, 
  Building, 
  Zap,
  Shield,
  Bot,
  Calendar,
  MessageCircle,
  Activity,
  Settings,
  ToggleLeft,
  ToggleRight,
  AlertTriangle
} from 'lucide-react';
import { format } from 'date-fns';
import { zhCN } from 'date-fns/locale';
import toast from 'react-hot-toast';
import { AvatarCircle } from '@/components/ui/AvatarCircle';

interface DigitalHuman {
  id: string;
  name: string;
  avatar?: string;
  description?: string;
  type: 'personal' | 'business' | 'specialized' | 'system';
  status: 'active' | 'inactive' | 'maintenance';
  isSystemCreated: boolean;
  user: {
    id: string;
    username: string;
    email: string;
    phone?: string;
  };
  personality?: {
    tone?: string;
    style?: string;
    specialization?: string;
  };
  greetingMessage?: string;
  welcomeMessage?: string;
  lastActiveAt?: string;
  agentConfigs?: Array<{
    id: string;
    priority: number;
    isActive: boolean;
    agentConfig: {
      appName: string;
      description?: string;
    };
  }>;
  createdAt: string;
  updatedAt: string;
}

interface AdminDigitalHumanDetailProps {
  digitalHumanId: string;
  onBack: () => void;
  onStatusToggle: (digitalHumanId: string, newStatus: string) => void;
  currentUserId?: string;
}

export default function AdminDigitalHumanDetail({
  digitalHumanId,
  onBack,
  onStatusToggle,
  currentUserId
}: AdminDigitalHumanDetailProps) {
  const [digitalHuman, setDigitalHuman] = useState<DigitalHuman | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadDigitalHumanDetail();
  }, [digitalHumanId]);

  const loadDigitalHumanDetail = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`/api/admin/digital-humans/${digitalHumanId}`);
      const data = await response.json();
      
      if (data.success) {
        setDigitalHuman(data.data);
      } else {
        toast.error('加载数字人详情失败');
      }
    } catch (error) {
      console.error('加载数字人详情失败:', error);
      toast.error('加载数字人详情失败');
    } finally {
      setIsLoading(false);
    }
  };

  const handleStatusToggle = async (newStatus: string) => {
    if (!digitalHuman) return;
    
    try {
      await onStatusToggle(digitalHuman.id, newStatus);
      // 重新加载数据
      await loadDigitalHumanDetail();
      toast.success('状态更新成功');
    } catch (error) {
      console.error('状态更新失败:', error);
      toast.error('状态更新失败');
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'personal':
        return <User className="h-5 w-5" />;
      case 'business':
        return <Building className="h-5 w-5" />;
      case 'specialized':
        return <Zap className="h-5 w-5" />;
      case 'system':
        return <Shield className="h-5 w-5" />;
      default:
        return <Bot className="h-5 w-5" />;
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

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="w-8 h-8 border-2 border-orange-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-gray-600">加载数字人详情...</p>
          </div>
        </div>
      </div>
    );
  }

  if (!digitalHuman) {
    return (
      <div className="p-6">
        <div className="text-center">
          <Bot className="h-16 w-16 mx-auto text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">数字人不存在</h3>
          <p className="text-gray-500 mb-4">请检查数字人ID是否正确</p>
          <Button onClick={onBack}>返回列表</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* 头部 */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={onBack}
            className="flex items-center space-x-2"
          >
            <ArrowLeft className="h-4 w-4" />
            <span>返回列表</span>
          </Button>
          <div className="flex items-center space-x-3">
            <AvatarCircle
              name={digitalHuman.name}
              avatar={digitalHuman.avatar}
              sizeClassName="w-12 h-12"
            />
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-xl font-bold text-gray-900">{digitalHuman.name}</h2>
                {digitalHuman.isSystemCreated && (
                  <Shield className="h-5 w-5 text-blue-500" aria-label="系统创建" />
                )}
              </div>
              <p className="text-gray-600">{digitalHuman.description || '暂无描述'}</p>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <Badge className={getStatusColor(digitalHuman.status)}>
            {getStatusLabel(digitalHuman.status)}
          </Badge>
          <div className="flex items-center space-x-1">
            {getTypeIcon(digitalHuman.type)}
            <span className="text-sm text-gray-600">{getTypeLabel(digitalHuman.type)}</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 主要信息 */}
        <div className="lg:col-span-2 space-y-6">
          {/* 基础信息 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <User className="h-5 w-5" />
                <span>基础信息</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-gray-500">数字人名称</label>
                  <p className="text-gray-900">{digitalHuman.name}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">类型</label>
                  <div className="flex items-center space-x-2">
                    {getTypeIcon(digitalHuman.type)}
                    <span>{getTypeLabel(digitalHuman.type)}</span>
                  </div>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">状态</label>
                  <Badge className={getStatusColor(digitalHuman.status)}>
                    {getStatusLabel(digitalHuman.status)}
                  </Badge>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">创建方式</label>
                  <span>{digitalHuman.isSystemCreated ? '系统创建' : '用户创建'}</span>
                </div>
              </div>
              
              {digitalHuman.description && (
                <div>
                  <label className="text-sm font-medium text-gray-500">描述</label>
                  <p className="text-gray-900 mt-1">{digitalHuman.description}</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* 所属用户信息 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <User className="h-5 w-5" />
                <span>所属用户</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-gray-500">用户名</label>
                  <p className="text-gray-900">{digitalHuman.user.username}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">邮箱</label>
                  <p className="text-gray-900">{digitalHuman.user.email}</p>
                </div>
                {digitalHuman.user.phone && (
                  <div>
                    <label className="text-sm font-medium text-gray-500">手机号</label>
                    <p className="text-gray-900">{digitalHuman.user.phone}</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* 个性化配置 */}
          {digitalHuman.personality && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Settings className="h-5 w-5" />
                  <span>个性化配置</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="text-sm font-medium text-gray-500">语调风格</label>
                    <p className="text-gray-900">{digitalHuman.personality.tone || '未设置'}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-500">交流风格</label>
                    <p className="text-gray-900">{digitalHuman.personality.style || '未设置'}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-500">专业领域</label>
                    <p className="text-gray-900">{digitalHuman.personality.specialization || '未设置'}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* 消息配置 */}
          {(digitalHuman.greetingMessage || digitalHuman.welcomeMessage) && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <MessageCircle className="h-5 w-5" />
                  <span>消息配置</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {digitalHuman.greetingMessage && (
                  <div>
                    <label className="text-sm font-medium text-gray-500">打招呼消息</label>
                    <p className="text-gray-900 mt-1 p-3 bg-gray-50 rounded">
                      {digitalHuman.greetingMessage}
                    </p>
                  </div>
                )}
                {digitalHuman.welcomeMessage && (
                  <div>
                    <label className="text-sm font-medium text-gray-500">欢迎消息</label>
                    <p className="text-gray-900 mt-1 p-3 bg-gray-50 rounded">
                      {digitalHuman.welcomeMessage}
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>

        {/* 侧边栏 */}
        <div className="space-y-6">
          {/* 统计信息 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Activity className="h-5 w-5" />
                <span>统计信息</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-gray-500">智能体数量</span>
                <span className="font-semibold">{digitalHuman.agentConfigs?.length || 0}</span>
              </div>
            </CardContent>
          </Card>

          {/* 时间信息 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Calendar className="h-5 w-5" />
                <span>时间信息</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium text-gray-500">创建时间</label>
                <p className="text-gray-900">
                  {format(new Date(digitalHuman.createdAt), 'yyyy-MM-dd HH:mm:ss', { locale: zhCN })}
                </p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">更新时间</label>
                <p className="text-gray-900">
                  {format(new Date(digitalHuman.updatedAt), 'yyyy-MM-dd HH:mm:ss', { locale: zhCN })}
                </p>
              </div>
              {digitalHuman.lastActiveAt && (
                <div>
                  <label className="text-sm font-medium text-gray-500">最后活跃</label>
                  <p className="text-gray-900">
                    {format(new Date(digitalHuman.lastActiveAt), 'yyyy-MM-dd HH:mm:ss', { locale: zhCN })}
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* 管理操作 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Settings className="h-5 w-5" />
                <span>管理操作</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {digitalHuman.status !== 'active' && (
                <Button
                  onClick={() => handleStatusToggle('active')}
                  className="w-full flex items-center justify-center space-x-2"
                >
                  <ToggleRight className="h-4 w-4" />
                  <span>激活数字人</span>
                </Button>
              )}

              {digitalHuman.status !== 'inactive' && (
                <Button
                  variant="outline"
                  onClick={() => handleStatusToggle('inactive')}
                  className="w-full flex items-center justify-center space-x-2 text-red-600 hover:text-red-700"
                >
                  <ToggleLeft className="h-4 w-4" />
                  <span>停用数字人</span>
                </Button>
              )}

              {digitalHuman.status !== 'maintenance' && (
                <Button
                  variant="outline"
                  onClick={() => handleStatusToggle('maintenance')}
                  className="w-full flex items-center justify-center space-x-2 text-yellow-600 hover:text-yellow-700"
                >
                  <AlertTriangle className="h-4 w-4" />
                  <span>设为维护</span>
                </Button>
              )}
            </CardContent>
          </Card>

          {/* 智能体配置 */}
          {digitalHuman.agentConfigs && digitalHuman.agentConfigs.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Bot className="h-5 w-5" />
                  <span>智能体配置</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {digitalHuman.agentConfigs.map((config, index) => (
                    <div key={config.id} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                      <div className="flex items-center space-x-3">
                        <span className="w-6 h-6 bg-orange-100 text-orange-600 rounded-full flex items-center justify-center text-sm font-medium">
                          {config.priority}
                        </span>
                        <div>
                          <p className="font-medium text-gray-900">{config.agentConfig.appName}</p>
                          {config.agentConfig.description && (
                            <p className="text-sm text-gray-600">{config.agentConfig.description}</p>
                          )}
                        </div>
                      </div>
                      <Badge variant={config.isActive ? 'default' : 'secondary'}>
                        {config.isActive ? '启用' : '停用'}
                      </Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
