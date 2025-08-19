import { useState, useEffect } from 'react';
import { apiClient } from '@/service/apiClient';
import toast from 'react-hot-toast';
import type { 
  DigitalHuman, 
  CreateDigitalHumanRequest, 
  UpdateDigitalHumanRequest,
  DigitalHumanStats
} from '@/types/digital-human';

export function useDigitalHumans() {
  const [digitalHumans, setDigitalHumans] = useState<DigitalHuman[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 获取数字人列表
  const fetchDigitalHumans = async (): Promise<DigitalHuman[]> => {
    try {
      const response = await apiClient.get<{
        success: boolean;
        data: DigitalHuman[];
        message?: string;
      }>('/digital-humans');
      
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

  // 创建数字人
  const createDigitalHuman = async (data: CreateDigitalHumanRequest): Promise<DigitalHuman> => {
    try {
      const response = await apiClient.post<{
        success: boolean;
        data: DigitalHuman;
        message?: string;
      }>('/digital-humans', data);
      
      if (response.data.success) {
        const newDigitalHuman = response.data.data;
        setDigitalHumans(prev => [...prev, newDigitalHuman]);
        return newDigitalHuman;
      } else {
        throw new Error(response.data.message || '创建数字人失败');
      }
    } catch (error) {
      console.error('创建数字人失败:', error);
      throw error;
    }
  };

  // 更新数字人
  const updateDigitalHuman = async (
    id: string, 
    data: UpdateDigitalHumanRequest
  ): Promise<DigitalHuman> => {
    try {
      const response = await apiClient.put<{
        success: boolean;
        data: DigitalHuman;
        message?: string;
      }>(`/digital-humans/${id}`, data);
      
      if (response.data.success) {
        const updatedDigitalHuman = response.data.data;
        setDigitalHumans(prev => 
          prev.map(dh => dh.id === id ? updatedDigitalHuman : dh)
        );
        return updatedDigitalHuman;
      } else {
        throw new Error(response.data.message || '更新数字人失败');
      }
    } catch (error) {
      console.error('更新数字人失败:', error);
      throw error;
    }
  };

  // 删除数字人
  const deleteDigitalHuman = async (id: string): Promise<void> => {
    try {
      const response = await apiClient.delete<{
        success: boolean;
        message?: string;
      }>(`/digital-humans/${id}`);
      
      if (response.data.success) {
        setDigitalHumans(prev => prev.filter(dh => dh.id !== id));
        toast.success('数字人删除成功');
      } else {
        throw new Error(response.data.message || '删除数字人失败');
      }
    } catch (error) {
      console.error('删除数字人失败:', error);
      toast.error('删除数字人失败');
      throw error;
    }
  };

  // 获取单个数字人详情
  const getDigitalHuman = async (id: string): Promise<DigitalHuman> => {
    try {
      const response = await apiClient.get<{
        success: boolean;
        data: DigitalHuman;
        message?: string;
      }>(`/digital-humans/${id}`);
      
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

  // 刷新数字人列表
  const refreshDigitalHumans = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const data = await fetchDigitalHumans();
      setDigitalHumans(data);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '获取数字人列表失败';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  // 初始化加载
  useEffect(() => {
    refreshDigitalHumans();
  }, []);

  // 统计信息
  const stats: DigitalHumanStats = {
    total: digitalHumans.length,
    active: digitalHumans.filter(dh => dh.status === 'active').length,
    inactive: digitalHumans.filter(dh => dh.status === 'inactive').length,
    maintenance: digitalHumans.filter(dh => dh.status === 'maintenance').length,
    system: digitalHumans.filter(dh => dh.isSystemCreated).length,
    user: digitalHumans.filter(dh => !dh.isSystemCreated).length,
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
    refreshDigitalHumans,
  };
}
