import { authService } from './authService';
import { apiClient, ApiClientError } from './apiClient';
import { Message } from '@/types/chat';

// 客户信息接口，匹配后端响应格式
interface CustomerInfo {
  id: string;
  user_id: string;
  username: string;
  email: string;
  phone?: string;
  avatar?: string;
  created_at: string;
  updated_at: string;
  profile?: CustomerProfile;
}

// 客户画像洞察（时间流条目）
interface CustomerInsight {
  id: string;
  profile_id?: string;
  category: string;
  content: string;
  source?: string;
  created_by_name?: string;
  status?: string;
  confidence?: number;
  created_at?: string;
}

// 客户档案接口（去医疗化 + 画像流）
interface CustomerProfile {
  id: string;
  customer_id: string;
  life_cycle_stage?: string;
  industry?: string;
  company_scale?: string;
  ai_summary?: string;
  extra_data?: Record<string, any>;
  active_insights?: CustomerInsight[];
  created_at?: string;
  updated_at?: string;
}

// 客户列表项接口，匹配后端响应格式
interface CustomerListItem {
  id: string;
  name: string;
  avatar: string;
  is_online: boolean;
  last_message?: {
    content: string;
    created_at?: string;
  };
  unread_count: number;
  life_cycle_stage?: string;
  updated_at?: string;
}

class CustomerService {
  // 获取客户列表（仅限企业内部用户）
  async getCustomerList(): Promise<CustomerListItem[]> {
    try {
      const response = await apiClient.get<CustomerListItem[]>('/customers');
      return response.data ?? [];
    } catch (error) {
      console.error('获取客户列表失败:', error);
      throw error;
    }
  }

  // 获取客户详细信息
  async getCustomerById(customerId: string): Promise<CustomerInfo | null> {
    try {
      const response = await apiClient.get<CustomerInfo>(`/customers/${customerId}`);
      return response.data;
    } catch (error) {
      if (error instanceof ApiClientError && error.status === 404) {
        return null;
      }
      console.error('获取客户信息失败:', error);
      throw error;
    }
  }

  // 获取客户档案
  async getCustomerProfile(customerId: string): Promise<CustomerProfile | null> {
    try {
      const response = await apiClient.get<CustomerProfile>(`/customers/${customerId}/profile`);
      return response.data;
    } catch (error) {
      if (error instanceof ApiClientError && error.status === 404) {
        return null;
      }
      console.error('获取客户档案失败:', error);
      throw error;
    }
  }

  // 新增客户洞察（人工录入 or AI写入）
  async addCustomerInsight(
    customerId: string,
    payload: { category: string; content: string; confidence?: number; source?: string; created_by_name?: string }
  ): Promise<CustomerInsight> {
    const response = await apiClient.post<CustomerInsight>(`/customers/${customerId}/insights`, payload);
    if (!response.data) {
      throw new Error('新增客户洞察失败：响应数据为空');
    }
    return response.data;
  }

  // 归档客户洞察（用于“覆盖旧事实”的人工操作）
  async archiveCustomerInsight(customerId: string, insightId: string): Promise<void> {
    await apiClient.delete(`/customers/${customerId}/insights/${insightId}`);
  }

  // 获取系统消息/通知
  async getSystemMessages(): Promise<Message[]> {
    const currentUser = authService.getCurrentUser();
    if (!currentUser || currentUser.currentRole !== 'customer') {
      return [];
    }
    
    try {
      // 注意：可能需要通过chat service获取系统消息
      // 或者后端提供专门的notifications endpoint
      const { getConversationMessages } = await import('./chatService');
      
      // 获取与系统的会话消息
      // 这里需要根据实际业务逻辑调整
      return [];
    } catch (error) {
      console.error('获取系统消息失败:', error);
      return [];
    }
  }
}

export const customerService = new CustomerService();
export type { CustomerInfo, CustomerProfile, CustomerListItem, CustomerInsight }; 