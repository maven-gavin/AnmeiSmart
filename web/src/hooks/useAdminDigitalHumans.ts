import { useEffect, useState } from 'react';
import { apiClient, handleApiError } from '@/service/apiClient';
import toast from 'react-hot-toast';
import type {
  AdminDigitalHuman,
  DigitalHumanFilters as AdminDigitalHumanFilters,
  DigitalHumanStats as AdminDigitalHumanStats,
} from '@/types/digital-human';

export function useAdminDigitalHumans() {
  const [digitalHumans, setDigitalHumans] = useState<AdminDigitalHuman[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<AdminDigitalHumanFilters>({});

  // 获取数字人列表
  const fetchDigitalHumans = async (
    currentFilters: AdminDigitalHumanFilters = {},
  ): Promise<AdminDigitalHuman[]> => {
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

      const response = await apiClient.get<AdminDigitalHuman[]>(
        `/admin/digital-humans?${params.toString()}`,
      );

      return response.data ?? [];
    } catch (err) {
      handleApiError(err, '获取数字人列表失败');
      throw err;
    }
  };

  // 切换数字人状态
  const toggleDigitalHumanStatus = async (
    digitalHumanId: string,
    newStatus: string,
  ): Promise<AdminDigitalHuman> => {
    try {
      const response = await apiClient.put<AdminDigitalHuman>(
        `/admin/digital-humans/${digitalHumanId}/status`,
        {
          status: newStatus,
        },
      );

      const updatedDigitalHuman = response.data;

      if (updatedDigitalHuman) {
        setDigitalHumans(prev =>
          prev.map(dh => (dh.id === digitalHumanId ? updatedDigitalHuman : dh)),
        );
      }

      toast.success('数字人状态更新成功');
      return updatedDigitalHuman;
    } catch (err) {
      handleApiError(err, '更新数字人状态失败');
      throw err;
    }
  };

  // 获取数字人详情
  const getDigitalHuman = async (digitalHumanId: string): Promise<AdminDigitalHuman> => {
    try {
      const response = await apiClient.get<AdminDigitalHuman>(
        `/admin/digital-humans/${digitalHumanId}`,
      );
      return response.data;
    } catch (err) {
      handleApiError(err, '获取数字人详情失败');
      throw err;
    }
  };

  // 批量操作数字人
  const batchUpdateDigitalHumans = async (
    digitalHumanIds: string[],
    action: string,
    data?: unknown,
  ): Promise<void> => {
    try {
      const response = await apiClient.post<{ results: unknown[] }>(
        '/admin/digital-humans/batch',
        {
          digitalHumanIds,
          action,
          data,
        },
      );

      if (response.data) {
        await refreshDigitalHumans();
        toast.success('批量操作成功');
      }
    } catch (err) {
      handleApiError(err, '批量操作失败');
      throw err;
    }
  };

  // 刷新数字人列表
  const refreshDigitalHumans = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const data = await fetchDigitalHumans(filters);
      setDigitalHumans(data);
    } catch (err) {
      const message = handleApiError(err, '获取数字人列表失败');
      setError(message);
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
    } catch (err) {
      const message = handleApiError(err, '获取数字人列表失败');
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  // 计算统计信息
  const calculateStats = (
    digitalHumanList: AdminDigitalHuman[],
  ): AdminDigitalHumanStats => {
    const stats: AdminDigitalHumanStats = {
      total: digitalHumanList.length,
      active: 0,
      inactive: 0,
      maintenance: 0,
      system: 0,
      user: 0,
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

      // 统计创建方式（后端字段为 snake_case）
      if (dh.is_system_created) {
        stats.system++;
      } else {
        stats.user++;
      }
    });

    return stats;
  };

  // 初始化加载
  useEffect(() => {
    void refreshDigitalHumans();
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
