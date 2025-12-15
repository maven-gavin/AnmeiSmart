import { useState, useEffect } from 'react';
import { apiClient } from '@/service/apiClient';
import toast from 'react-hot-toast';
import { handleApiError } from '@/service/apiClient';
import type { 
  PendingTask, 
  TaskFilters, 
  TaskStats, 
  CreateTaskRequest,
  UpdateTaskRequest
} from '@/types/task';

export function usePendingTasks(userRole?: string) {
  const [tasks, setTasks] = useState<PendingTask[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<TaskFilters>({});

  // 获取任务列表
  const fetchTasks = async (currentFilters: TaskFilters = {}): Promise<PendingTask[]> => {
    try {
      const params = new URLSearchParams();
      
      // 根据用户角色添加默认筛选
      if (userRole) {
        params.append('user_role', userRole);
      }
      
      // 添加筛选参数
      Object.entries(currentFilters).forEach(([key, value]) => {
        if (value && value !== '') {
          if (key === 'date_range' && typeof value === 'object') {
            // TODO: 后端当前未实现日期范围筛选，先不发送
            // if (value.start) params.append('start_date', value.start)
            // if (value.end) params.append('end_date', value.end)
          } else {
            params.append(key, String(value));
          }
        }
      });

      const response = await apiClient.get<PendingTask[]>(`/tasks?${params.toString()}`);
      return response.data;
    } catch (error) {
      console.error('获取任务列表失败:', error);
      throw error;
    }
  };

  // 认领任务
  const claimTask = async (taskId: string): Promise<PendingTask> => {
    try {
      const response = await apiClient.post<PendingTask>(`/tasks/${taskId}/claim`);
      const updatedTask = response.data;
      setTasks(prev => prev.map(task => task.id === taskId ? updatedTask : task));
      toast.success('任务认领成功');
      return updatedTask;
    } catch (error) {
      console.error('认领任务失败:', error);
      handleApiError(error, '认领任务失败');
      throw error;
    }
  };

  // 更新任务状态
  const updateTaskStatus = async (
    taskId: string, 
    status: string, 
    updateData?: any
  ): Promise<PendingTask> => {
    try {
      const response = await apiClient.put<PendingTask>(`/tasks/${taskId}`, {
        status,
        ...updateData
      });
      
      const updatedTask = response.data;
      setTasks(prev => prev.map(task => task.id === taskId ? updatedTask : task));
      return updatedTask;
    } catch (error) {
      console.error('更新任务状态失败:', error);
      handleApiError(error, '更新任务状态失败');
      throw error;
    }
  };

  // 获取任务详情
  const getTask = async (taskId: string): Promise<PendingTask> => {
    try {
      const response = await apiClient.get<PendingTask>(`/tasks/${taskId}`);
      return response.data;
    } catch (error) {
      console.error('获取任务详情失败:', error);
      throw error;
    }
  };

  // 刷新任务列表
  const refreshTasks = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const data = await fetchTasks(filters);
      setTasks(data);
    } catch (error) {
      const errorMessage = handleApiError(error, '获取任务列表失败');
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  // 应用筛选条件
  const applyFilters = async (newFilters: TaskFilters) => {
    setFilters(newFilters);
    setIsLoading(true);
    setError(null);
    
    try {
      const data = await fetchTasks(newFilters);
      setTasks(data);
    } catch (error) {
      const errorMessage = handleApiError(error, '获取任务列表失败');
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  // 计算统计信息
  const calculateStats = (taskList: PendingTask[]): TaskStats => {
    const stats = {
      total: taskList.length,
      pending: 0,
      assigned: 0,
      inProgress: 0,
      completed: 0,
      cancelled: 0,
      urgent: 0
    };

    taskList.forEach(task => {
      switch (task.status) {
        case 'pending':
          stats.pending++;
          break;
        case 'assigned':
          stats.assigned++;
          break;
        case 'in_progress':
          stats.inProgress++;
          break;
        case 'completed':
          stats.completed++;
          break;
        case 'cancelled':
          stats.cancelled++;
          break;
      }

      if (task.priority === 'urgent') {
        stats.urgent++;
      }
    });

    return stats;
  };

  // 监听筛选条件变化
  useEffect(() => {
    applyFilters(filters);
  }, []);

  const stats = calculateStats(tasks);

  return {
    tasks,
    isLoading,
    error,
    stats,
    filters,
    setFilters: applyFilters,
    claimTask,
    updateTaskStatus,
    getTask,
    refreshTasks,
  };
}
