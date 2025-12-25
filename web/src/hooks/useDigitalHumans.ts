import { useEffect, useState } from 'react';
import { apiClient, handleApiError } from '@/service/apiClient';
import toast from 'react-hot-toast';
import type {
  CreateDigitalHumanRequest,
  DigitalHuman,
  DigitalHumanStats,
  UpdateDigitalHumanRequest,
} from '@/types/digital-human';

export function useDigitalHumans() {
  const [digitalHumans, setDigitalHumans] = useState<DigitalHuman[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 获取数字人列表
  const fetchDigitalHumans = async (): Promise<DigitalHuman[]> => {
    try {
      const response = await apiClient.get<DigitalHuman[]>('/digital-humans');
      return response.data ?? [];
    } catch (err) {
      handleApiError(err, '获取数字人列表失败');
      throw err;
    }
  };

  // 创建数字人
  const createDigitalHuman = async (data: CreateDigitalHumanRequest): Promise<DigitalHuman> => {
    try {
      const response = await apiClient.post<DigitalHuman>('/digital-humans', data);
      const newDigitalHuman = response.data;
      if (newDigitalHuman) {
        setDigitalHumans(prev => [...prev, newDigitalHuman]);
      }
      return newDigitalHuman;
    } catch (err) {
      handleApiError(err, '创建数字人失败');
      throw err;
    }
  };

  // 更新数字人
  const updateDigitalHuman = async (
    id: string,
    data: UpdateDigitalHumanRequest,
  ): Promise<DigitalHuman> => {
    try {
      const response = await apiClient.put<DigitalHuman>(`/digital-humans/${id}`, data);
      const updatedDigitalHuman = response.data;

      if (updatedDigitalHuman) {
        setDigitalHumans(prev => prev.map(dh => (dh.id === id ? updatedDigitalHuman : dh)));
      }

      return updatedDigitalHuman;
    } catch (err) {
      handleApiError(err, '更新数字人失败');
      throw err;
    }
  };

  // 删除数字人
  const deleteDigitalHuman = async (id: string): Promise<void> => {
    try {
      await apiClient.delete<null>(`/digital-humans/${id}`);
      setDigitalHumans(prev => prev.filter(dh => dh.id !== id));
      toast.success('数字人删除成功');
    } catch (err) {
      handleApiError(err, '删除数字人失败');
      throw err;
    }
  };

  // 获取单个数字人详情
  const getDigitalHuman = async (id: string): Promise<DigitalHuman> => {
    try {
      const response = await apiClient.get<DigitalHuman>(`/digital-humans/${id}`);
      return response.data;
    } catch (err) {
      handleApiError(err, '获取数字人详情失败');
      throw err;
    }
  };

  // 获取并写入本地状态（用于保存后回填）
  const fetchAndSetDigitalHuman = async (id: string): Promise<DigitalHuman> => {
    const dh = await getDigitalHuman(id);
    if (dh) {
      setDigitalHumans(prev => prev.map(item => (item.id === id ? dh : item)));
    }
    return dh;
  };

  // 刷新数字人列表
  const refreshDigitalHumans = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const data = await fetchDigitalHumans();
      setDigitalHumans(data);
    } catch (err) {
      const message = handleApiError(err, '获取数字人列表失败');
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  // 初始化加载
  useEffect(() => {
    void refreshDigitalHumans();
  }, []);

  // 统计信息
  const stats: DigitalHumanStats = {
    total: digitalHumans.length,
    active: digitalHumans.filter(dh => dh.status === 'active').length,
    inactive: digitalHumans.filter(dh => dh.status === 'inactive').length,
    maintenance: digitalHumans.filter(dh => dh.status === 'maintenance').length,
    system: digitalHumans.filter(dh => dh.is_system_created).length,
    user: digitalHumans.filter(dh => !dh.is_system_created).length,
  };

  return {
    digitalHumans,
    isLoading,
    error,
    stats,
    createDigitalHuman,
    updateDigitalHuman,
    deleteDigitalHuman,
    getDigitalHuman,
    fetchAndSetDigitalHuman,
    refreshDigitalHumans,
  };
}
