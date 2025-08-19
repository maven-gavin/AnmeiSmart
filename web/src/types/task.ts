/**
 * 待办任务相关类型定义
 */

export interface PendingTask {
  id: string;
  title: string;
  description?: string;
  taskType: string;
  status: 'pending' | 'assigned' | 'in_progress' | 'completed' | 'cancelled';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  createdBy?: {
    id: string;
    username: string;
    email: string;
  };
  assignedTo?: {
    id: string;
    username: string;
    email: string;
  };
  assignedAt?: string;
  relatedObjectType?: string;
  relatedObjectId?: string;
  taskData?: any;
  dueDate?: string;
  completedAt?: string;
  result?: any;
  notes?: string;
  createdAt: string;
  updatedAt: string;
}

export interface CreateTaskRequest {
  title: string;
  description?: string;
  taskType: string;
  priority?: 'low' | 'medium' | 'high' | 'urgent';
  dueDate?: string;
  relatedObjectType?: string;
  relatedObjectId?: string;
  taskData?: any;
  assignedTo?: string;
}

export interface UpdateTaskRequest {
  title?: string;
  description?: string;
  status?: 'pending' | 'assigned' | 'in_progress' | 'completed' | 'cancelled';
  priority?: 'low' | 'medium' | 'high' | 'urgent';
  notes?: string;
  result?: any;
}

export interface TaskFilters {
  status?: string;
  priority?: string;
  taskType?: string;
  assignedTo?: string;
  createdBy?: string;
  search?: string;
  dateRange?: {
    start?: string;
    end?: string;
  };
}

export interface TaskStats {
  total: number;
  pending: number;
  assigned: number;
  inProgress: number;
  completed: number;
  cancelled: number;
  urgent: number;
}

// 任务类型标签映射
export const TASK_TYPE_LABELS: Record<string, string> = {
  new_user_reception: '新用户接待',
  consultation_upgrade: '咨询升级',
  system_exception: '系统异常',
  periodic_followup: '定期回访',
  prescription_review: '处方审核',
  medical_consultation: '医疗咨询',
  system_maintenance: '系统维护',
  user_feedback: '用户反馈'
};

// 任务状态标签映射
export const TASK_STATUS_LABELS: Record<string, string> = {
  pending: '待认领',
  assigned: '已分配',
  in_progress: '进行中',
  completed: '已完成',
  cancelled: '已取消'
};

// 任务优先级标签映射
export const TASK_PRIORITY_LABELS: Record<string, string> = {
  low: '低',
  medium: '中',
  high: '高',
  urgent: '紧急'
};
