import { apiClient } from '@/service/apiClient';

interface SystemSettings {
  siteName: string;
  logoUrl: string;
  userRegistrationEnabled: boolean;
}

const systemService = {
  /**
   * 获取系统设置
   */
  async getSystemSettings(): Promise<SystemSettings> {
    try {
      const response = await apiClient.get<{success: boolean, data: SystemSettings, message: string}>('/system/settings');
      const responseData = response.data as any;
      return responseData.data || responseData; // 兼容两种响应格式
    } catch (error) {
      console.error('获取系统设置失败:', error);
      throw error;
    }
  },

  /**
   * 更新系统设置
   */
  async updateSystemSettings(settings: Partial<SystemSettings>): Promise<SystemSettings> {
    try {
      const response = await apiClient.put<{success: boolean, data: SystemSettings, message: string}>('/system/settings', settings);
      const responseData = response.data as any;
      return responseData.data || responseData; // 兼容两种响应格式
    } catch (error) {
      console.error('更新系统设置失败:', error);
      throw error;
    }
  },
};

export default systemService;
export type { SystemSettings}; 