import { authService } from './authService';
import { apiClient } from './apiClient';
import { CustomerAppointment, Treatment, TreatmentPlan } from '@/types/customer';
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
      const response = await apiClient.get('/customers');
      if (!response.ok) {
        throw new Error(`获取客户列表失败: ${response.status}`);
      }
      return response.data || [];
    } catch (error) {
      console.error('获取客户列表失败:', error);
      throw error;
    }
  }

  // 获取客户详细信息
  async getCustomerById(customerId: string): Promise<CustomerInfo | null> {
    try {
      const response = await apiClient.get(`/customers/${customerId}`);
      if (!response.ok) {
        if (response.status === 404) {
          return null;
        }
        throw new Error(`获取客户信息失败: ${response.status}`);
      }
      return response.data;
    } catch (error) {
      console.error('获取客户信息失败:', error);
      throw error;
    }
  }

  // 获取客户档案
  async getCustomerProfile(customerId: string): Promise<CustomerProfile | null> {
    try {
      const response = await apiClient.get(`/customers/${customerId}/profile`);
      if (!response.ok) {
        if (response.status === 404) {
          return null;
        }
        throw new Error(`获取客户档案失败: ${response.status}`);
      }
      return response.data;
    } catch (error) {
      console.error('获取客户档案失败:', error);
      throw error;
    }
  }

  // 获取当前顾客的治疗记录
  async getTreatments(): Promise<Treatment[]> {
    const currentUser = authService.getCurrentUser();
    if (!currentUser || currentUser.currentRole !== 'customer') {
      return [];
    }
    
    try {
      // 注意：这里需要后端提供对应的treatment endpoints
      // 目前使用客户信息作为基础，实际可能需要专门的treatment API
      const customerInfo = await this.getCustomerById(currentUser.id);
      
      // 如果后端有专门的treatment endpoints，应该调用类似：
      // const response = await apiClient.get(`/customers/${currentUser.id}/treatments`);
      
      // 临时返回空数组，等待后端提供treatment endpoints
      return [];
    } catch (error) {
      console.error('获取治疗记录失败:', error);
      return [];
    }
  }
  
  // 获取特定治疗记录详情
  async getTreatmentById(id: string): Promise<Treatment | null> {
    const currentUser = authService.getCurrentUser();
    if (!currentUser || currentUser.currentRole !== 'customer') {
      return null;
    }
    
    try {
      // 注意：需要后端提供treatment详情endpoint
      // const response = await apiClient.get(`/treatments/${id}`);
      
      // 临时返回null，等待后端提供treatment endpoints
      return null;
    } catch (error) {
      console.error('获取治疗记录详情失败:', error);
      return null;
    }
  }
  
  // 获取当前顾客的治疗方案
  async getTreatmentPlans(): Promise<TreatmentPlan[]> {
    const currentUser = authService.getCurrentUser();
    if (!currentUser || currentUser.currentRole !== 'customer') {
      return [];
    }
    
    try {
      // 注意：需要后端提供treatment plan endpoints
      // const response = await apiClient.get(`/customers/${currentUser.id}/treatment-plans`);
      
      // 临时返回空数组，等待后端提供treatment plan endpoints
      return [];
    } catch (error) {
      console.error('获取治疗方案失败:', error);
      return [];
    }
  }
  
  // 获取特定治疗方案详情
  async getTreatmentPlanById(id: string): Promise<TreatmentPlan | null> {
    const currentUser = authService.getCurrentUser();
    if (!currentUser || currentUser.currentRole !== 'customer') {
      return null;
    }
    
    try {
      // 注意：需要后端提供treatment plan详情endpoint
      // const response = await apiClient.get(`/treatment-plans/${id}`);
      
      // 临时返回null，等待后端提供treatment plan endpoints
      return null;
    } catch (error) {
      console.error('获取治疗方案详情失败:', error);
      return null;
    }
  }
  
  // 获取当前顾客的预约
  async getAppointments(): Promise<CustomerAppointment[]> {
    const currentUser = authService.getCurrentUser();
    if (!currentUser || currentUser.currentRole !== 'customer') {
      return [];
    }
    
    try {
      // 注意：需要后端提供appointment endpoints
      // const response = await apiClient.get(`/customers/${currentUser.id}/appointments`);
      
      // 临时返回空数组，等待后端提供appointment endpoints
      return [];
    } catch (error) {
      console.error('获取预约信息失败:', error);
      return [];
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