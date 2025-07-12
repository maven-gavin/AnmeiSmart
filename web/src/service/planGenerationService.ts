/**
 * AI辅助方案生成服务
 * 提供方案生成相关的API调用函数
 */

import { apiClient } from './apiClient';

// 类型定义
export interface PlanGenerationSession {
  id: string;
  conversation_id: string;
  customer_id: string;
  consultant_id: string;
  status: 'collecting' | 'generating' | 'optimizing' | 'reviewing' | 'completed' | 'failed' | 'cancelled';
  extracted_info?: any;
  performance_metrics?: any;
  created_at: string;
  updated_at: string;
}

export interface PlanGenerationSessionCreate {
  conversation_id: string;
  customer_id: string;
  consultant_id: string;
  session_metadata?: any;
}

export interface InfoAnalysis {
  session_id: string;
  completeness_score: number;
  missing_categories: string[];
  suggestions: string[];
  can_generate_plan: boolean;
  guidance_questions?: GuidanceQuestions;
}

export interface GuidanceQuestions {
  basic_info: GuidanceQuestion[];
  concerns: GuidanceQuestion[];
  budget: GuidanceQuestion[];
  timeline: GuidanceQuestion[];
  expectations: GuidanceQuestion[];
  total_questions: number;
}

export interface GuidanceQuestion {
  question: string;
  type: 'text' | 'choice' | 'number' | 'date';
  options?: string[];
  required: boolean;
  context?: string;
}

export interface PlanDraft {
  id: string;
  session_id: string;
  version: number;
  content: any;
  status: 'draft' | 'reviewing' | 'approved' | 'rejected';
  created_at: string;
  updated_at: string;
  generation_info?: any;
}

export interface GeneratePlanRequest {
  conversation_id: string;
  force_generation?: boolean;
  generation_options?: {
    template_type?: string;
    include_timeline?: boolean;
    include_cost_breakdown?: boolean;
    [key: string]: any;
  };
}

export interface PlanGenerationResponse {
  session_id: string;
  draft_id: string;
  status: string;
  draft_status: string;
  message: string;
  needs_review: boolean;
  next_steps: string[];
}

export interface OptimizePlanRequest {
  draft_id: string;
  optimization_type: 'cost' | 'timeline' | 'content';
  requirements: any;
  feedback?: any;
}

export interface AnalyzeInfoRequest {
  conversation_id: string;
  force_analysis?: boolean;
}

export interface GenerateGuidanceRequest {
  conversation_id: string;
  missing_categories: string[];
  context?: any;
}

// API调用函数

/**
 * 创建方案生成会话
 */
export async function createPlanGenerationSession(
  data: PlanGenerationSessionCreate
): Promise<PlanGenerationSession> {
  try {
    const response = await apiClient.post('/plan-generation/sessions', data);
    return response.data as PlanGenerationSession;
  } catch (error) {
    console.error('创建方案生成会话失败:', error);
    throw error;
  }
}

/**
 * 获取方案生成会话
 */
export async function getPlanGenerationSession(
  sessionId: string
): Promise<PlanGenerationSession> {
  try {
    const response = await apiClient.get(`/plan-generation/sessions/${sessionId}`);
    return response.data as PlanGenerationSession;
  } catch (error) {
    console.error('获取方案生成会话失败:', error);
    throw error;
  }
}

/**
 * 根据对话ID获取方案生成会话
 */
export async function getPlanGenerationSessionByConversation(
  conversationId: string
): Promise<PlanGenerationSession | null> {
  try {
    const response = await apiClient.get(`/plan-generation/sessions/conversation/${conversationId}`);
    return response.data as PlanGenerationSession;
  } catch (error: any) {
    if (error.response?.status === 404) {
      return null;
    }
    console.error('根据对话ID获取方案生成会话失败:', error);
    throw error;
  }
}

/**
 * 分析对话信息
 */
export async function analyzeConversationInfo(
  request: AnalyzeInfoRequest
): Promise<InfoAnalysis> {
  try {
    const response = await apiClient.post('/plan-generation/analyze-info', request);
    return response.data as InfoAnalysis;
  } catch (error) {
    console.error('分析对话信息失败:', error);
    throw error;
  }
}

/**
 * 生成引导问题
 */
export async function generateGuidanceQuestions(
  request: GenerateGuidanceRequest
): Promise<{ guidance_questions: GuidanceQuestions }> {
  try {
    const response = await apiClient.post('/plan-generation/generate-guidance', request);
    return response.data as { guidance_questions: GuidanceQuestions };
  } catch (error) {
    console.error('生成引导问题失败:', error);
    throw error;
  }
}

/**
 * 生成方案
 */
export async function generatePlan(
  request: GeneratePlanRequest
): Promise<PlanGenerationResponse> {
  try {
    const response = await apiClient.post('/plan-generation/generate', request);
    return response.data as PlanGenerationResponse;
  } catch (error) {
    console.error('生成方案失败:', error);
    throw error;
  }
}

/**
 * 优化方案
 */
export async function optimizePlan(
  request: OptimizePlanRequest
): Promise<PlanDraft> {
  try {
    const response = await apiClient.post('/plan-generation/optimize', request);
    return response.data as PlanDraft;
  } catch (error) {
    console.error('优化方案失败:', error);
    throw error;
  }
}

/**
 * 获取会话的所有草稿
 */
export async function getSessionDrafts(
  sessionId: string
): Promise<PlanDraft[]> {
  try {
    const response = await apiClient.get(`/plan-generation/sessions/${sessionId}/drafts`);
    return response.data as PlanDraft[];
  } catch (error) {
    console.error('获取会话草稿失败:', error);
    throw error;
  }
}

/**
 * 获取草稿详情
 */
export async function getDraft(
  draftId: string
): Promise<PlanDraft> {
  try {
    const response = await apiClient.get(`/plan-generation/drafts/${draftId}`);
    return response.data as PlanDraft;
  } catch (error) {
    console.error('获取草稿详情失败:', error);
    throw error;
  }
}

/**
 * 获取会话的所有版本
 */
export async function getSessionVersions(
  sessionId: string
): Promise<PlanDraft[]> {
  try {
    const response = await apiClient.get(`/plan-generation/sessions/${sessionId}/versions`);
    return response.data as PlanDraft[];
  } catch (error) {
    console.error('获取会话版本失败:', error);
    throw error;
  }
}

/**
 * 比较会话版本
 */
export async function compareSessionVersions(
  sessionId: string,
  versionNumbers: [number, number]
): Promise<any> {
  try {
    const response = await apiClient.post(`/plan-generation/sessions/${sessionId}/compare`, {
      version_numbers: versionNumbers
    });
    return response.data;
  } catch (error) {
    console.error('比较会话版本失败:', error);
    throw error;
  }
}

/**
 * 获取生成统计信息
 */
export async function getGenerationStats(): Promise<any> {
  try {
    const response = await apiClient.get('/plan-generation/stats');
    return response.data;
  } catch (error) {
    console.error('获取生成统计信息失败:', error);
    throw error;
  }
}

// 工具函数

/**
 * 获取状态显示文本
 */
export function getStatusText(status: string): string {
  switch (status) {
    case 'collecting': return '收集信息中';
    case 'generating': return '生成中';
    case 'optimizing': return '优化中';
    case 'reviewing': return '审核中';
    case 'completed': return '已完成';
    case 'failed': return '失败';
    case 'cancelled': return '已取消';
    default: return '未知状态';
  }
}

/**
 * 获取状态颜色类
 */
export function getStatusColor(status: string): string {
  switch (status) {
    case 'collecting': return 'bg-yellow-100 text-yellow-800';
    case 'generating': return 'bg-blue-100 text-blue-800';
    case 'optimizing': return 'bg-purple-100 text-purple-800';
    case 'reviewing': return 'bg-orange-100 text-orange-800';
    case 'completed': return 'bg-green-100 text-green-800';
    case 'failed': return 'bg-red-100 text-red-800';
    case 'cancelled': return 'bg-gray-100 text-gray-800';
    default: return 'bg-gray-100 text-gray-800';
  }
}

/**
 * 获取类别图标
 */
export function getCategoryIcon(category: string): string {
  switch (category) {
    case 'basic_info': return '📋';
    case 'concerns': return '🎯';
    case 'budget': return '💰';
    case 'timeline': return '📅';
    case 'expectations': return '❤️';
    default: return '💬';
  }
}

/**
 * 获取类别名称
 */
export function getCategoryName(category: string): string {
  switch (category) {
    case 'basic_info': return '基本信息';
    case 'concerns': return '关注问题';
    case 'budget': return '预算范围';
    case 'timeline': return '时间计划';
    case 'expectations': return '期望效果';
    default: return category;
  }
}

/**
 * 格式化完整性得分
 */
export function formatCompletenessScore(score: number): string {
  return `${Math.round(score * 100)}%`;
}

/**
 * 判断是否可以生成方案
 */
export function canGeneratePlan(analysis: InfoAnalysis): boolean {
  return analysis.can_generate_plan && analysis.completeness_score >= 0.7;
}

/**
 * 格式化草稿版本
 */
export function formatDraftVersion(draft: PlanDraft): string {
  return `v${draft.version} - ${new Date(draft.created_at).toLocaleDateString()}`;
}

/**
 * 获取优化类型显示文本
 */
export function getOptimizationTypeText(type: string): string {
  switch (type) {
    case 'cost': return '费用优化';
    case 'timeline': return '时间优化';
    case 'content': return '内容优化';
    default: return '未知类型';
  }
}

/**
 * 获取草稿状态显示文本
 */
export function getDraftStatusText(status: string): string {
  switch (status) {
    case 'draft': return '草稿';
    case 'reviewing': return '审核中';
    case 'approved': return '已批准';
    case 'rejected': return '已拒绝';
    default: return '未知状态';
  }
}

/**
 * 获取草稿状态颜色类
 */
export function getDraftStatusColor(status: string): string {
  switch (status) {
    case 'draft': return 'bg-gray-100 text-gray-800';
    case 'reviewing': return 'bg-blue-100 text-blue-800';
    case 'approved': return 'bg-green-100 text-green-800';
    case 'rejected': return 'bg-red-100 text-red-800';
    default: return 'bg-gray-100 text-gray-800';
  }
}

export default {
  createPlanGenerationSession,
  getPlanGenerationSession,
  getPlanGenerationSessionByConversation,
  analyzeConversationInfo,
  generateGuidanceQuestions,
  generatePlan,
  optimizePlan,
  getSessionDrafts,
  getDraft,
  getSessionVersions,
  compareSessionVersions,
  getGenerationStats,
  getStatusText,
  getStatusColor,
  getCategoryIcon,
  getCategoryName,
  formatCompletenessScore,
  canGeneratePlan,
  formatDraftVersion,
  getOptimizationTypeText,
  getDraftStatusText,
  getDraftStatusColor
}; 