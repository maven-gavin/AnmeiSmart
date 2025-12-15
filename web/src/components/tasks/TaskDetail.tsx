'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { apiClient, handleApiError } from '@/service/apiClient';
import { 
  ArrowLeft, 
  Clock, 
  User, 
  Calendar,
  AlertCircle,
  CheckCircle,
  XCircle,
  FileText,
  Play,
  Pause,
  Check
} from 'lucide-react';
import { formatDistanceToNow, format } from 'date-fns';
import { zhCN } from 'date-fns/locale';
import toast from 'react-hot-toast';

import type { PendingTask } from '@/types/task';

interface TaskDetailProps {
  taskId: string;
  onBack: () => void;
  onStatusUpdate: (taskId: string, status: string, result?: any) => void;
  currentUserId?: string;
}

export default function TaskDetail({
  taskId,
  onBack,
  onStatusUpdate,
  currentUserId
}: TaskDetailProps) {
  const [task, setTask] = useState<PendingTask | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isUpdating, setIsUpdating] = useState(false);
  const [notes, setNotes] = useState('');
  const [result, setResult] = useState('');

  useEffect(() => {
    loadTaskDetail();
  }, [taskId]);

  const loadTaskDetail = async () => {
    setIsLoading(true);
    try {
      const response = await apiClient.get<PendingTask>(`/tasks/${taskId}`);
      setTask(response.data);
      setNotes(response.data.notes || '');
      setResult(response.data.result ? JSON.stringify(response.data.result, null, 2) : '');
    } catch (error) {
      console.error('加载任务详情失败:', error);
      handleApiError(error, '加载任务详情失败');
    } finally {
      setIsLoading(false);
    }
  };

  const handleStatusUpdate = async (newStatus: string) => {
    if (!task) return;
    
    setIsUpdating(true);
    try {
      const updateData: any = {
        status: newStatus,
        notes: notes.trim() || undefined
      };

      if (newStatus === 'completed' && result.trim()) {
        try {
          updateData.result = JSON.parse(result);
        } catch {
          updateData.result = { message: result.trim() };
        }
      }

      await onStatusUpdate(task.id, newStatus, updateData);
      toast.success('任务状态更新成功');
    } catch (error) {
      console.error('更新任务状态失败:', error);
      toast.error('更新任务状态失败');
    } finally {
      setIsUpdating(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'assigned':
        return 'bg-blue-100 text-blue-800';
      case 'in_progress':
        return 'bg-orange-100 text-orange-800';
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'cancelled':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'pending':
        return '待认领';
      case 'assigned':
        return '已分配';
      case 'in_progress':
        return '进行中';
      case 'completed':
        return '已完成';
      case 'cancelled':
        return '已取消';
      default:
        return '未知';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent':
        return 'bg-red-100 text-red-800';
      case 'high':
        return 'bg-orange-100 text-orange-800';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800';
      case 'low':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getPriorityLabel = (priority: string) => {
    switch (priority) {
      case 'urgent':
        return '紧急';
      case 'high':
        return '高';
      case 'medium':
        return '中';
      case 'low':
        return '低';
      default:
        return '未知';
    }
  };

  const getTaskTypeLabel = (taskType: string) => {
    switch (taskType) {
      case 'new_user_reception':
        return '新用户接待';
      case 'consultation_upgrade':
        return '咨询升级';
      case 'system_exception':
        return '系统异常';
      case 'periodic_followup':
        return '定期回访';
      default:
        return taskType;
    }
  };

  const isOverdue = (dueDate?: string) => {
    if (!dueDate) return false;
    return new Date(dueDate) < new Date();
  };

  const canStart = (task: PendingTask) => {
    return (task.status === 'assigned' || task.status === 'pending') && 
           (task.assigned_to?.id === currentUserId || !task.assigned_to);
  };

  const canComplete = (task: PendingTask) => {
    return task.status === 'in_progress' && task.assigned_to?.id === currentUserId;
  };

  const canCancel = (task: PendingTask) => {
    return task.status !== 'completed' && task.status !== 'cancelled';
  };

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="w-8 h-8 border-2 border-orange-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-gray-600">加载任务详情...</p>
          </div>
        </div>
      </div>
    );
  }

  if (!task) {
    return (
      <div className="p-6">
        <div className="text-center">
          <XCircle className="h-16 w-16 mx-auto text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">任务不存在</h3>
          <p className="text-gray-500 mb-4">请检查任务ID是否正确</p>
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
          <div>
            <h2 className="text-xl font-bold text-gray-900">{task.title}</h2>
            <p className="text-gray-600 mt-1">{getTaskTypeLabel(task.task_type)}</p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <Badge className={getStatusColor(task.status)}>
            {getStatusLabel(task.status)}
          </Badge>
          <Badge className={getPriorityColor(task.priority)}>
            {getPriorityLabel(task.priority)}
          </Badge>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 主要内容 */}
        <div className="lg:col-span-2 space-y-6">
          {/* 任务描述 */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="font-semibold text-gray-900 mb-2">任务描述</h3>
            <p className="text-gray-700 whitespace-pre-wrap">
              {task.description || '暂无描述'}
            </p>
          </div>

          {/* 任务数据 */}
          {task.task_data && (
            <div className="bg-gray-50 rounded-lg p-4">
              <h3 className="font-semibold text-gray-900 mb-2">任务数据</h3>
              <pre className="text-sm text-gray-700 bg-white p-3 rounded border overflow-auto">
                {JSON.stringify(task.task_data, null, 2)}
              </pre>
            </div>
          )}

          {/* 处理记录 */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="font-semibold text-gray-900 mb-4">处理记录</h3>
            
            <div className="space-y-4">
              <div>
                <Label htmlFor="notes">处理备注</Label>
                <Textarea
                  id="notes"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="记录处理过程和备注信息..."
                  rows={4}
                  disabled={task.status === 'completed' || task.status === 'cancelled'}
                />
              </div>

              {canComplete(task) && (
                <div>
                  <Label htmlFor="result">处理结果</Label>
                  <Textarea
                    id="result"
                    value={result}
                    onChange={(e) => setResult(e.target.value)}
                    placeholder="输入处理结果（支持JSON格式）..."
                    rows={3}
                  />
                </div>
              )}

              {task.result && (
                <div>
                  <Label>已有处理结果</Label>
                  <pre className="text-sm text-gray-700 bg-white p-3 rounded border overflow-auto mt-1">
                    {typeof task.result === 'string' ? task.result : JSON.stringify(task.result, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* 侧边栏 */}
        <div className="space-y-6">
          {/* 任务信息 */}
          <div className="bg-white border rounded-lg p-4">
            <h3 className="font-semibold text-gray-900 mb-4">任务信息</h3>
            
            <div className="space-y-3 text-sm">
              <div className="flex items-center justify-between">
                <span className="text-gray-500">任务ID</span>
                <span className="font-mono text-xs">{task.id}</span>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-gray-500">创建时间</span>
                <span>{format(new Date(task.created_at), 'yyyy-MM-dd HH:mm', { locale: zhCN })}</span>
              </div>

              {task.due_date && (
                <div className="flex items-center justify-between">
                  <span className="text-gray-500">截止时间</span>
                  <span className={isOverdue(task.due_date) ? 'text-red-600' : ''}>
                    {format(new Date(task.due_date), 'yyyy-MM-dd HH:mm', { locale: zhCN })}
                    {isOverdue(task.due_date) && (
                      <AlertCircle className="h-4 w-4 inline ml-1" />
                    )}
                  </span>
                </div>
              )}

              {task.completed_at && (
                <div className="flex items-center justify-between">
                  <span className="text-gray-500">完成时间</span>
                  <span>{format(new Date(task.completed_at), 'yyyy-MM-dd HH:mm', { locale: zhCN })}</span>
                </div>
              )}

              {task.created_by && (
                <div className="flex items-center justify-between">
                  <span className="text-gray-500">创建人</span>
                  <span>{task.created_by.username}</span>
                </div>
              )}

              {task.assigned_to && (
                <div className="flex items-center justify-between">
                  <span className="text-gray-500">负责人</span>
                  <span>{task.assigned_to.username}</span>
                </div>
              )}

              {task.related_object_type && (
                <div className="flex items-center justify-between">
                  <span className="text-gray-500">关联对象</span>
                  <div className="text-right">
                    <Badge variant="outline" className="text-xs mb-1">
                      {task.related_object_type}
                    </Badge>
                    <div className="font-mono text-xs text-gray-600">
                      {task.related_object_id}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* 操作按钮 */}
          <div className="bg-white border rounded-lg p-4">
            <h3 className="font-semibold text-gray-900 mb-4">任务操作</h3>
            
            <div className="space-y-2">
              {canStart(task) && (
                <Button
                  onClick={() => handleStatusUpdate('in_progress')}
                  disabled={isUpdating}
                  className="w-full flex items-center justify-center space-x-2"
                >
                  <Play className="h-4 w-4" />
                  <span>开始处理</span>
                </Button>
              )}

              {canComplete(task) && (
                <Button
                  onClick={() => handleStatusUpdate('completed')}
                  disabled={isUpdating}
                  className="w-full flex items-center justify-center space-x-2"
                >
                  <Check className="h-4 w-4" />
                  <span>完成任务</span>
                </Button>
              )}

              {canCancel(task) && (
                <Button
                  variant="outline"
                  onClick={() => handleStatusUpdate('cancelled')}
                  disabled={isUpdating}
                  className="w-full flex items-center justify-center space-x-2"
                >
                  <XCircle className="h-4 w-4" />
                  <span>取消任务</span>
                </Button>
              )}

              {task.status === 'in_progress' && task.assigned_to?.id === currentUserId && (
                <Button
                  variant="outline"
                  onClick={() => handleStatusUpdate('assigned')}
                  disabled={isUpdating}
                  className="w-full flex items-center justify-center space-x-2"
                >
                  <Pause className="h-4 w-4" />
                  <span>暂停处理</span>
                </Button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
