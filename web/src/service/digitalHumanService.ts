/**
 * 数字人管理服务
 * 与后端API交互，管理数字人及其关联的智能体配置
 */

import { apiClient } from './apiClient';
import { DigitalHuman } from '@/types/digital-human';

/**
 * 获取用户可用的数字人列表
 * @returns Promise<DigitalHuman[]>
 */
export const getDigitalHumans = async (): Promise<DigitalHuman[]> => {
  try {
    // 优先获取当前用户可见的活跃数字人
    const response = await apiClient.get<DigitalHuman[]>('/digital-humans/');
    return response.data || [];
  } catch (error) {
    console.error('获取数字人列表失败:', error);
    // 如果普通接口报错，尝试管理员接口作为兜底（如果是管理员的话）
    try {
      const adminResponse = await apiClient.get<DigitalHuman[]>('/admin/digital-humans/');
      return adminResponse.data || [];
    } catch (adminError) {
      console.error('获取管理员数字人列表也失败了:', adminError);
      return [];
    }
  }
};

/**
 * 获取数字人详情及其关联的智能体
 * @param id 数字人ID
 * @returns Promise<DigitalHuman>
 */
export const getDigitalHumanDetail = async (id: string): Promise<DigitalHuman | null> => {
  try {
    const response = await apiClient.get<DigitalHuman>(`/digital-humans/${id}`);
    return response.data;
  } catch (error) {
    console.error(`获取数字人 ${id} 详情失败:`, error);
    return null;
  }
};

const digitalHumanService = {
  getDigitalHumans,
  getDigitalHumanDetail,
};

export default digitalHumanService;

