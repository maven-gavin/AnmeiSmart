import { authService } from './authService';
import { mockTreatments, mockTreatmentPlans, mockAppointments, mockCustomerMessages } from './customerMockData';
import { CustomerAppointment, Treatment, TreatmentPlan } from '@/types/customer';
import { Message } from '@/types/chat';
import { getConversationMessages, sendTextMessage } from './chatService';

class CustomerService {
  // 获取当前顾客的治疗记录
  async getTreatments(): Promise<Treatment[]> {
    const currentUser = authService.getCurrentUser();
    if (!currentUser || currentUser.currentRole !== 'customer') {
      return [];
    }
    
    return mockTreatments[currentUser.id] || [];
  }
  
  // 获取特定治疗记录详情
  async getTreatmentById(id: string): Promise<Treatment | null> {
    const currentUser = authService.getCurrentUser();
    if (!currentUser || currentUser.currentRole !== 'customer') {
      return null;
    }
    
    const treatments = mockTreatments[currentUser.id] || [];
    return treatments.find(treatment => treatment.id === id) || null;
  }
  
  // 获取当前顾客的治疗方案
  async getTreatmentPlans(): Promise<TreatmentPlan[]> {
    const currentUser = authService.getCurrentUser();
    if (!currentUser || currentUser.currentRole !== 'customer') {
      return [];
    }
    
    return mockTreatmentPlans[currentUser.id] || [];
  }
  
  // 获取特定治疗方案详情
  async getTreatmentPlanById(id: string): Promise<TreatmentPlan | null> {
    const currentUser = authService.getCurrentUser();
    if (!currentUser || currentUser.currentRole !== 'customer') {
      return null;
    }
    
    const plans = mockTreatmentPlans[currentUser.id] || [];
    return plans.find(plan => plan.id === id) || null;
  }
  
  // 获取当前顾客的预约
  async getAppointments(): Promise<CustomerAppointment[]> {
    const currentUser = authService.getCurrentUser();
    if (!currentUser || currentUser.currentRole !== 'customer') {
      return [];
    }
    
    return mockAppointments[currentUser.id] || [];
  }
  
  
  // 获取系统消息/通知
  async getSystemMessages(): Promise<Message[]> {
    const currentUser = authService.getCurrentUser();
    if (!currentUser || currentUser.currentRole !== 'customer') {
      return [];
    }
    
    return mockCustomerMessages[currentUser.id] || [];
  }
}

export const customerService = new CustomerService(); 