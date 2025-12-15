import { apiClient, handleApiError } from '@/service/apiClient'
import type {
  RouteTaskRequest,
  RouteTaskResponse,
  TaskQueue,
  TaskRoutingRule,
  TaskSensitiveRule,
  TaskGovernanceMetricsResponse,
} from '@/types/task-governance'

export const taskGovernanceService = {
  // Queues
  async listQueues(params?: { scene_key?: string; only_active?: boolean }): Promise<TaskQueue[]> {
    try {
      const search = new URLSearchParams()
      if (params?.scene_key) search.set('scene_key', params.scene_key)
      if (params?.only_active !== undefined) search.set('only_active', String(params.only_active))
      const qs = search.toString()
      const resp = await apiClient.get<TaskQueue[]>(`/tasks/queues${qs ? `?${qs}` : ''}`)
      return resp.data
    } catch (err) {
      handleApiError(err, '获取队列列表失败')
      throw err
    }
  },

  async createQueue(payload: Omit<TaskQueue, 'id' | 'created_at' | 'updated_at'>): Promise<TaskQueue> {
    try {
      const resp = await apiClient.post<TaskQueue>('/tasks/queues', payload)
      return resp.data
    } catch (err) {
      handleApiError(err, '创建队列失败')
      throw err
    }
  },

  async updateQueue(queueId: string, payload: Partial<Omit<TaskQueue, 'id' | 'created_at' | 'updated_at'>>): Promise<TaskQueue> {
    try {
      const resp = await apiClient.put<TaskQueue>(`/tasks/queues/${queueId}`, payload)
      return resp.data
    } catch (err) {
      handleApiError(err, '更新队列失败')
      throw err
    }
  },

  async deleteQueue(queueId: string): Promise<void> {
    try {
      await apiClient.delete(`/tasks/queues/${queueId}`)
    } catch (err) {
      handleApiError(err, '删除队列失败')
      throw err
    }
  },

  // Routing rules
  async listRoutingRules(params?: { scene_key?: string; enabled_only?: boolean }): Promise<TaskRoutingRule[]> {
    try {
      const search = new URLSearchParams()
      if (params?.scene_key) search.set('scene_key', params.scene_key)
      if (params?.enabled_only !== undefined) search.set('enabled_only', String(params.enabled_only))
      const qs = search.toString()
      const resp = await apiClient.get<TaskRoutingRule[]>(`/tasks/routing-rules${qs ? `?${qs}` : ''}`)
      return resp.data
    } catch (err) {
      handleApiError(err, '获取路由规则失败')
      throw err
    }
  },

  async createRoutingRule(payload: Omit<TaskRoutingRule, 'id' | 'created_at' | 'updated_at'>): Promise<TaskRoutingRule> {
    try {
      const resp = await apiClient.post<TaskRoutingRule>('/tasks/routing-rules', payload)
      return resp.data
    } catch (err) {
      handleApiError(err, '创建路由规则失败')
      throw err
    }
  },

  async updateRoutingRule(ruleId: string, payload: Partial<Omit<TaskRoutingRule, 'id' | 'created_at' | 'updated_at'>>): Promise<TaskRoutingRule> {
    try {
      const resp = await apiClient.put<TaskRoutingRule>(`/tasks/routing-rules/${ruleId}`, payload)
      return resp.data
    } catch (err) {
      handleApiError(err, '更新路由规则失败')
      throw err
    }
  },

  async deleteRoutingRule(ruleId: string): Promise<void> {
    try {
      await apiClient.delete(`/tasks/routing-rules/${ruleId}`)
    } catch (err) {
      handleApiError(err, '删除路由规则失败')
      throw err
    }
  },

  // Sensitive rules
  async listSensitiveRules(params?: { category?: string; enabled_only?: boolean }): Promise<TaskSensitiveRule[]> {
    try {
      const search = new URLSearchParams()
      if (params?.category) search.set('category', params.category)
      if (params?.enabled_only !== undefined) search.set('enabled_only', String(params.enabled_only))
      const qs = search.toString()
      const resp = await apiClient.get<TaskSensitiveRule[]>(`/tasks/sensitive-rules${qs ? `?${qs}` : ''}`)
      return resp.data
    } catch (err) {
      handleApiError(err, '获取敏感规则失败')
      throw err
    }
  },

  async createSensitiveRule(payload: Omit<TaskSensitiveRule, 'id' | 'created_at' | 'updated_at'>): Promise<TaskSensitiveRule> {
    try {
      const resp = await apiClient.post<TaskSensitiveRule>('/tasks/sensitive-rules', payload)
      return resp.data
    } catch (err) {
      handleApiError(err, '创建敏感规则失败')
      throw err
    }
  },

  async updateSensitiveRule(ruleId: string, payload: Partial<Omit<TaskSensitiveRule, 'id' | 'created_at' | 'updated_at'>>): Promise<TaskSensitiveRule> {
    try {
      const resp = await apiClient.put<TaskSensitiveRule>(`/tasks/sensitive-rules/${ruleId}`, payload)
      return resp.data
    } catch (err) {
      handleApiError(err, '更新敏感规则失败')
      throw err
    }
  },

  async deleteSensitiveRule(ruleId: string): Promise<void> {
    try {
      await apiClient.delete(`/tasks/sensitive-rules/${ruleId}`)
    } catch (err) {
      handleApiError(err, '删除敏感规则失败')
      throw err
    }
  },

  // Route tester
  async route(payload: RouteTaskRequest): Promise<RouteTaskResponse> {
    try {
      const resp = await apiClient.post<RouteTaskResponse>('/tasks/route', payload)
      return resp.data
    } catch (err) {
      handleApiError(err, '路由执行失败')
      throw err
    }
  },

  // M4: Governance metrics
  async getMetrics(params?: { start_at?: string; end_at?: string; scene_key?: string }): Promise<TaskGovernanceMetricsResponse> {
    try {
      const search = new URLSearchParams()
      if (params?.start_at) search.set('start_at', params.start_at)
      if (params?.end_at) search.set('end_at', params.end_at)
      if (params?.scene_key) search.set('scene_key', params.scene_key)
      const qs = search.toString()
      const resp = await apiClient.get<TaskGovernanceMetricsResponse>(`/tasks/metrics${qs ? `?${qs}` : ''}`)
      return resp.data
    } catch (err) {
      handleApiError(err, '获取任务治理指标失败')
      throw err
    }
  },
}


