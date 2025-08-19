import { useState, useEffect } from 'react';
import { apiClient } from '@/service/apiClient';
import toast from 'react-hot-toast';
import type { 
  AdminDigitalHuman, 
  DigitalHumanFilters as AdminDigitalHumanFilters,
  DigitalHumanStats as AdminDigitalHumanStats,
  UpdateDigitalHumanStatusRequest
} from '@/types/digital-human';

export function useAdminDigitalHumans() {
  const [digitalHumans, setDigitalHumans] = useState<AdminDigitalHuman[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<AdminDigitalHumanFilters>({});

  // 获取数字人列表
  const fetchDigitalHumans = async (currentFilters: AdminDigitalHumanFilters = {}): Promise<AdminDigitalHuman[]> => {
    try {
      const params = new URLSearchParams();
      
      // 添加筛选参数
      Object.entries(currentFilters).forEach(([key, value]) => {
        if (value !== undefined && value !== '') {
          if (key === 'dateRange' && typeof value === 'object') {
            if (value.start) params.append('startDate', value.start);
            if (value.end) params.append('endDate', value.end);
          } else {
            params.append(key, String(value));
          }
        }
      });

      const response = await apiClient.get<{
        success: boolean;
        data: AdminDigitalHuman[];
        message?: string;
      }>(`/admin/digital-humans?${params.toString()}`);
      
      if (response.data.success) {
        return response.data.data;
      } else {
        throw new Error(response.data.message || '获取数字人列表失败');
      }
    } catch (error) {
      console.error('获取数字人列表失败:', error);
      throw error;
    }
  };

  // 切换数字人状态
  const toggleDigitalHumanStatus = async (
    digitalHumanId: string, 
    newStatus: string
  ): Promise<AdminDigitalHuman> => {
    try {
      const response = await apiClient.put<{
        success: boolean;
        data: AdminDigitalHuman;
        message?: string;
      }>(`/admin/digital-humans/${digitalHumanId}/status`, {
        status: newStatus
      });
      
      if (response.data.success) {
        const updatedDigitalHuman = response.data.data;
        setDigitalHumans(prev => 
          prev.map(dh => dh.id === digitalHumanId ? updatedDigitalHuman : dh)
        );
        toast.success('数字人状态更新成功');
        return updatedDigitalHuman;
      } else {
        throw new Error(response.data.message || '更新数字人状态失败');
      }
    } catch (error) {
      console.error('更新数字人状态失败:', error);
      toast.error('更新数字人状态失败');
      throw error;
    }
  };

  // 获取数字人详情
  const getDigitalHuman = async (digitalHumanId: string): Promise<AdminDigitalHuman> => {
    try {
      const response = await apiClient.get<{
        success: boolean;
        data: AdminDigitalHuman;
        message?: string;
      }>(`/admin/digital-humans/${digitalHumanId}`);
      
      if (response.data.success) {
        return response.data.data;
      } else {
        throw new Error(response.data.message || '获取数字人详情失败');
      }
    } catch (error) {
      console.error('获取数字人详情失败:', error);
      throw error;
    }
  };

  // 批量操作数字人
  const batchUpdateDigitalHumans = async (
    digitalHumanIds: string[], 
    action: string, 
    data?: any
  ): Promise<void> => {
    try {
      const response = await apiClient.post<{
        success: boolean;
        message?: string;
      }>('/admin/digital-humans/batch', {
        digitalHumanIds,
        action,
        data
      });
      
      if (response.data.success) {
        // 重新加载数据
        await refreshDigitalHumans();
        toast.success('批量操作成功');
      } else {
        throw new Error(response.data.message || '批量操作失败');
      }
    } catch (error) {
      console.error('批量操作失败:', error);
      toast.error('批量操作失败');
      throw error;
    }
  };

  // 刷新数字人列表
  const refreshDigitalHumans = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const data = await fetchDigitalHumans(filters);
      setDigitalHumans(data);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '获取数字人列表失败';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  // 应用筛选条件
  const applyFilters = async (newFilters: AdminDigitalHumanFilters) => {
    setFilters(newFilters);
    setIsLoading(true);
    setError(null);
    
    try {
      const data = await fetchDigitalHumans(newFilters);
      setDigitalHumans(data);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '获取数字人列表失败';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  // 计算统计信息
  const calculateStats = (digitalHumanList: AdminDigitalHuman[]): AdminDigitalHumanStats => {
    const stats = {
      total: digitalHumanList.length,
      active: 0,
      inactive: 0,
      maintenance: 0,
      system: 0,
      user: 0
    };

    digitalHumanList.forEach(dh => {
      // 统计状态
      switch (dh.status) {
        case 'active':
          stats.active++;
          break;
        case 'inactive':
          stats.inactive++;
          break;
        case 'maintenance':
          stats.maintenance++;
          break;
      }

      // 统计创建方式
      if (dh.isSystemCreated) {
        stats.system++;
      } else {
        stats.user++;
      }
    });

    return stats;
  };

  // 初始化加载
  useEffect(() => {
    refreshDigitalHumans();
  }, []);

  const stats = calculateStats(digitalHumans);

  return {
    digitalHumans,
    isLoading,
    error,
    stats,
    filters,
    setFilters: applyFilters,
    toggleDigitalHumanStatus,
    getDigitalHuman,
    batchUpdateDigitalHumans,
    refreshDigitalHumans,
  };
}
