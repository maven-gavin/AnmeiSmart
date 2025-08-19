'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  Clock, 
  AlertCircle, 
  User, 
  Calendar,
  ArrowRight,
  CheckCircle,
  XCircle
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { zhCN } from 'date-fns/locale';

import type { PendingTask, TASK_TYPE_LABELS, TASK_STATUS_LABELS, TASK_PRIORITY_LABELS } from '@/types/task';

interface TaskListProps {
  tasks: PendingTask[];
  onTaskSelect: (taskId: string) => void;
  onTaskClaim: (taskId: string) => void;
  currentUserId?: string;
}

export default function TaskList({
  tasks,
  onTaskSelect,
  onTaskClaim,
  currentUserId
}: TaskListProps) {
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
    return TASK_TYPE_LABELS[taskType] || taskType;
  };

  const isOverdue = (dueDate?: string) => {
    if (!dueDate) return false;
    return new Date(dueDate) < new Date();
  };

  const canClaim = (task: PendingTask) => {
    return task.status === 'pending' && !task.assignedTo;
  };

  const isAssignedToCurrentUser = (task: PendingTask) => {
    return task.assignedTo?.id === currentUserId;
  };

  if (tasks.length === 0) {
    return (
      <div className="p-8 text-center">
        <CheckCircle className="h-16 w-16 mx-auto text-gray-400 mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">暂无待办任务</h3>
        <p className="text-gray-500">所有任务都已处理完成</p>
      </div>
    );
  }

  return (
    <div className="divide-y divide-gray-200">
      {tasks.map((task) => (
        <div
          key={task.id}
          className={`p-6 hover:bg-gray-50 transition-colors ${
            isOverdue(task.dueDate) ? 'border-l-4 border-red-500' : ''
          }`}
        >
          <div className="flex items-start justify-between">
            <div className="flex-1">
              {/* 任务标题和类型 */}
              <div className="flex items-start justify-between mb-2">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-1">
                    {task.title}
                  </h3>
                  <div className="flex items-center space-x-2 mb-2">
                    <Badge variant="outline" className="text-xs">
                      {getTaskTypeLabel(task.taskType)}
                    </Badge>
                    <Badge className={getStatusColor(task.status)}>
                      {getStatusLabel(task.status)}
                    </Badge>
                    <Badge className={getPriorityColor(task.priority)}>
                      {getPriorityLabel(task.priority)}
                    </Badge>
                  </div>
                </div>
              </div>

              {/* 任务描述 */}
              {task.description && (
                <p className="text-gray-600 mb-3 line-clamp-2">
                  {task.description}
                </p>
              )}

              {/* 任务信息 */}
              <div className="flex items-center space-x-6 text-sm text-gray-500">
                <div className="flex items-center space-x-1">
                  <Calendar className="h-4 w-4" />
                  <span>
                    创建于 {formatDistanceToNow(new Date(task.createdAt), { 
                      addSuffix: true, 
                      locale: zhCN 
                    })}
                  </span>
                </div>

                {task.createdBy && (
                  <div className="flex items-center space-x-1">
                    <User className="h-4 w-4" />
                    <span>创建人: {task.createdBy.name}</span>
                  </div>
                )}

                {task.assignedTo && (
                  <div className="flex items-center space-x-1">
                    <User className="h-4 w-4" />
                    <span>负责人: {task.assignedTo.name}</span>
                  </div>
                )}

                {task.dueDate && (
                  <div className={`flex items-center space-x-1 ${
                    isOverdue(task.dueDate) ? 'text-red-600' : ''
                  }`}>
                    <Clock className="h-4 w-4" />
                    <span>
                      截止: {formatDistanceToNow(new Date(task.dueDate), { 
                        addSuffix: true, 
                        locale: zhCN 
                      })}
                      {isOverdue(task.dueDate) && (
                        <AlertCircle className="h-4 w-4 inline ml-1" />
                      )}
                    </span>
                  </div>
                )}
              </div>
            </div>

            {/* 操作按钮 */}
            <div className="flex items-center space-x-2 ml-4">
              <Button
                variant="outline"
                size="sm"
                onClick={() => onTaskSelect(task.id)}
                className="flex items-center space-x-1"
              >
                <span>查看详情</span>
                <ArrowRight className="h-3 w-3" />
              </Button>

              {canClaim(task) && (
                <Button
                  size="sm"
                  onClick={() => onTaskClaim(task.id)}
                  className="flex items-center space-x-1"
                >
                  <User className="h-3 w-3" />
                  <span>认领任务</span>
                </Button>
              )}

              {isAssignedToCurrentUser(task) && task.status === 'assigned' && (
                <Badge className="bg-blue-100 text-blue-800">
                  已分配给您
                </Badge>
              )}
            </div>
          </div>

          {/* 关联对象信息 */}
          {task.relatedObjectType && task.relatedObjectId && (
            <div className="mt-3 pt-3 border-t border-gray-100">
              <div className="flex items-center space-x-2 text-sm text-gray-500">
                <span>关联对象:</span>
                <Badge variant="outline" className="text-xs">
                  {task.relatedObjectType}
                </Badge>
                <span className="font-mono text-xs">{task.relatedObjectId}</span>
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
