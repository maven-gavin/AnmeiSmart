// 可治理任务中枢（M1/M2）前端类型

import type { PendingTask } from '@/types/task'

export type TaskQueueRotationStrategy = 'fixed' | 'round_robin'
export type TaskRuleMatchType = 'contains' | 'regex'
export type SensitiveCategory = 'pricing' | 'commitment' | 'confidential' | 'destructive'

export interface TaskQueue {
  id: string
  name: string
  scene_key: string
  description?: string | null
  rotation_strategy: TaskQueueRotationStrategy
  config?: Record<string, unknown> | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface TaskRoutingRule {
  id: string
  scene_key: string
  keyword: string
  match_type: TaskRuleMatchType
  priority: number
  target?: string | null
  task_templates?: Array<Record<string, unknown>> | null
  description?: string | null
  enabled: boolean
  created_at: string
  updated_at: string
}

export interface TaskSensitiveRule {
  id: string
  category: SensitiveCategory
  pattern: string
  match_type: TaskRuleMatchType
  priority: number
  suggestion_templates?: Array<Record<string, unknown>> | null
  description?: string | null
  enabled: boolean
  created_at: string
  updated_at: string
}

export interface RouteTaskRequest {
  scene_key: string
  text: string
  digital_human_id?: string
  conversation_id?: string
  message_id?: string
  create_fallback_task?: boolean
}

export interface RouteTaskResponse {
  route_type: 'routing' | 'sensitive' | 'none'
  matched_rule_id?: string | null
  matched_sensitive_rule_id?: string | null
  sensitive_category?: SensitiveCategory | null
  suggestions?: Array<Record<string, unknown>> | null
  created_tasks: PendingTask[]
}

export interface TaskGovernanceSceneMetrics {
  scene_key: string
  tasks_created: number
  tasks_completed: number
  routing_tasks_created: number
  sensitive_tasks_created: number
  config_required_tasks_created: number
  overdue_open_tasks: number
  sla_tasks_total: number
  sla_tasks_on_time: number
  median_cycle_time_minutes?: number | null
  avg_cycle_time_minutes?: number | null
}

export interface TaskGovernanceMetricsResponse {
  start_at: string
  end_at: string
  scene_key?: string | null

  tasks_created: number
  tasks_completed: number

  routing_tasks_created: number
  sensitive_tasks_created: number
  config_required_tasks_created: number

  overdue_open_tasks: number

  sla_tasks_total: number
  sla_tasks_on_time: number

  median_cycle_time_minutes?: number | null
  avg_cycle_time_minutes?: number | null

  scenes: TaskGovernanceSceneMetrics[]
}


