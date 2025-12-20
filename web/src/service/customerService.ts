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
  medical_history?: string;
  allergies?: string;
  preferences?: string;
  profile?: CustomerProfile;
}

// 客户档案接口
interface CustomerProfile {
  id: string;
  basicInfo: {
    name: string;
    age?: number;
    gender?: string;
    phone?: string;
  };
  medical_history?: string;
  allergies?: string;
  preferences?: string;
  tags: string[];
  riskNotes: any[];
  created_at: string;
  updated_at: string;
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
  tags: string[];
  priority: string;
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
export type { CustomerInfo, CustomerProfile, CustomerListItem }; 