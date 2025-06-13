/**
 * 咨询总结服务
 * 处理与后端API的交互，管理咨询总结的创建、更新、查询等功能
 */

import { apiClient } from '@/service/apiClient';

// 咨询总结数据结构
export interface ConsultationSummaryData {
  main_issues: string[];
  solutions: string[];
  follow_up_plan: string[];
  satisfaction_rating?: number;
  additional_notes?: string;
  tags: string[];
}

// API响应类型
export interface ConsultationSummaryResponse {
  id: string;
  title: string;
  consultation_type?: string;
  consultation_summary?: {
    basic_info: {
      start_time: string;
      end_time: string;
      duration_minutes: number;
      type: string;
      consultant_id: string;
      customer_id: string;
    };
    main_issues: string[];
    solutions: string[];
    follow_up_plan: string[];
    satisfaction_rating?: number;
    additional_notes?: string;
    tags: string[];
    ai_generated: boolean;
    created_at: string;
    updated_at: string;
    version: number;
  };
  summary?: string;
  has_summary: boolean;
  customer_name: string;
  consultant_name?: string;
  created_at: string;
  updated_at: string;
}

export interface ConsultationSummaryInfo {
  id: string;
  title: string;
  consultation_type?: string;
  summary_text?: string;
  has_summary: boolean;
  customer_name: string;
  date: string;
  duration_minutes?: number;
  satisfaction_rating?: number;
}

class ConsultationSummaryService {
  private baseUrl = '/consultation';

  /**
   * 获取会话的咨询总结
   */
  async getConsultationSummary(conversationId: string): Promise<ConsultationSummaryResponse> {
    const response = await apiClient.get<ConsultationSummaryResponse>(`${this.baseUrl}/conversation/${conversationId}/summary`);
    return response.data!;
  }

  /**
   * 创建咨询总结
   */
  async createConsultationSummary(
    conversationId: string, 
    summaryData: ConsultationSummaryData
  ): Promise<ConsultationSummaryResponse> {
    const requestData = {
      conversation_id: conversationId,
      ...summaryData
    };
    
    const response = await apiClient.post<ConsultationSummaryResponse>(
      `${this.baseUrl}/conversation/${conversationId}/summary`, 
      requestData
    );
    return response.data!;
  }

  /**
   * 更新咨询总结
   */
  async updateConsultationSummary(
    conversationId: string, 
    summaryData: Partial<ConsultationSummaryData>
  ): Promise<ConsultationSummaryResponse> {
    const response = await apiClient.put<ConsultationSummaryResponse>(
      `${this.baseUrl}/conversation/${conversationId}/summary`, 
      summaryData
    );
    return response.data!;
  }

  /**
   * 删除咨询总结
   */
  async deleteConsultationSummary(conversationId: string): Promise<void> {
    await apiClient.delete(`${this.baseUrl}/conversation/${conversationId}/summary`);
  }

  /**
   * AI生成咨询总结
   */
  async generateAISummary(
    conversationId: string, 
    options: {
      include_suggestions?: boolean;
      focus_areas?: string[];
    } = {}
  ): Promise<ConsultationSummaryData> {
    const requestData = {
      conversation_id: conversationId,
      include_suggestions: options.include_suggestions ?? true,
      focus_areas: options.focus_areas ?? []
    };
    
    const response = await apiClient.post<ConsultationSummaryData>(
      `${this.baseUrl}/conversation/${conversationId}/summary/ai-generate`,
      requestData
    );
    return response.data!;
  }

  /**
   * 保存AI生成的咨询总结
   */
  async saveAIGeneratedSummary(
    conversationId: string, 
    aiSummary: ConsultationSummaryData
  ): Promise<ConsultationSummaryResponse> {
    const response = await apiClient.post<ConsultationSummaryResponse>(
      `${this.baseUrl}/conversation/${conversationId}/summary/ai-save`,
      aiSummary
    );
    return response.data!;
  }

  /**
   * 获取客户的咨询历史总结
   */
  async getCustomerConsultationHistory(
    customerId: string, 
    limit: number = 10
  ): Promise<ConsultationSummaryInfo[]> {
    // 构建查询参数
    const params = new URLSearchParams();
    params.append('limit', limit.toString());
    
    const response = await apiClient.get<ConsultationSummaryInfo[]>(
      `${this.baseUrl}/customer/${customerId}/consultation-history?${params.toString()}`
    );
    return response.data!;
  }

  /**
   * 检查会话是否有总结
   */
  async checkHasSummary(conversationId: string): Promise<boolean> {
    try {
      const summary = await this.getConsultationSummary(conversationId);
      return summary.has_summary;
    } catch (error) {
      // 如果获取失败（比如404），认为没有总结
      return false;
    }
  }

  /**
   * 获取总结的简化信息（用于显示在客户资料中）
   */
  async getSummaryInfo(conversationId: string): Promise<ConsultationSummaryInfo | null> {
    try {
      const response = await this.getConsultationSummary(conversationId);
      if (!response.has_summary) {
        return null;
      }

      return {
        id: response.id,
        title: response.title,
        consultation_type: response.consultation_type,
        summary_text: response.summary,
        has_summary: response.has_summary,
        customer_name: response.customer_name,
        date: new Date(response.created_at).toLocaleDateString(),
        duration_minutes: response.consultation_summary?.basic_info.duration_minutes,
        satisfaction_rating: response.consultation_summary?.satisfaction_rating
      };
    } catch (error) {
      console.error('获取总结信息失败:', error);
      return null;
    }
  }

  /**
   * 格式化咨询类型显示名称
   */
  formatConsultationType(type?: string): string {
    const typeMap: Record<string, string> = {
      'initial': '初次咨询',
      'follow_up': '复诊咨询',
      'emergency': '紧急咨询',
      'specialized': '专项咨询',
      'other': '其他'
    };
    
    return typeMap[type || ''] || type || '未知类型';
  }

  /**
   * 验证总结数据的完整性
   */
  validateSummaryData(data: ConsultationSummaryData): string[] {
    const errors: string[] = [];
    
    if (!data.main_issues || data.main_issues.length === 0) {
      errors.push('至少需要填写一个主要问题');
    }
    
    if (!data.solutions || data.solutions.length === 0) {
      errors.push('至少需要填写一个解决方案');
    }
    
    if (data.satisfaction_rating && (data.satisfaction_rating < 1 || data.satisfaction_rating > 5)) {
      errors.push('满意度评分必须在1-5之间');
    }
    
    // 检查是否有空的条目
    const hasEmptyIssues = data.main_issues.some(issue => !issue.trim());
    const hasEmptySolutions = data.solutions.some(solution => !solution.trim());
    const hasEmptyPlans = data.follow_up_plan.some(plan => !plan.trim());
    
    if (hasEmptyIssues) {
      errors.push('主要问题中不能有空白条目');
    }
    
    if (hasEmptySolutions) {
      errors.push('解决方案中不能有空白条目');
    }
    
    if (hasEmptyPlans) {
      errors.push('跟进计划中不能有空白条目');
    }
    
    return errors;
  }
}

// 导出单例实例
export const consultationSummaryService = new ConsultationSummaryService(); 