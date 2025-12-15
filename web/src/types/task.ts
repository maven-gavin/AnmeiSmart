// 任务相关类型定义（与后端 /api/v1/tasks 字段命名保持一致：snake_case）

export interface Task {
  id: string;
  title: string;
  description?: string;
  task_type: string;
  status: 'pending' | 'assigned' | 'in_progress' | 'completed' | 'cancelled';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  created_by?: {
    id: string;
    username: string;
    email: string;
  };
  assigned_to?: {
    id: string;
    username: string;
    email: string;
  };
  assigned_at?: string;
  related_object_type?: string;
  related_object_id?: string;
  task_data?: unknown;
  due_date?: string;
  completed_at?: string;
  result?: any;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface CreateTaskRequest {
  title: string;
  description?: string;
  task_type: string;
  priority?: 'low' | 'medium' | 'high' | 'urgent';
  due_date?: string;
  related_object_type?: string;
  related_object_id?: string;
  task_data?: unknown;
  assigned_to?: string;
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
  task_type?: string;
  assigned_to?: string;
  created_by?: string;
  search?: string;
  date_range?: {
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
  user_feedback: '用户反馈',
  // MVP：可治理任务中枢（制造业销售视角）
  create_ticket: '创建工单',
  assign: '分派',
  transfer: '转派',
  set_sla: '设置SLA/提醒',
  create_followup: '创建跟进任务',
  sensitive_guard: '敏感拦截（待确认）',
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
