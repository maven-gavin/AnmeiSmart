export interface DatahubDatasetInfo {
  id: string
  dataset_key: string
  layer: string
  schema_version: string
  description?: string | null
  is_active: string
  updated_at: string
}

export interface DatahubJobRunInfo {
  id: string
  job_type: string
  dataset?: string | null
  status: string
  trigger_source?: string | null
  started_at?: string | null
  finished_at?: string | null
  task_total: number
  task_success: number
  task_failed: number
  error_message?: string | null
  created_at: string
  updated_at: string
}

export interface DatahubJobTaskInfo {
  id: string
  job_run_id: string
  dataset: string
  symbol?: string | null
  start_date?: string | null
  end_date?: string | null
  status: string
  attempts: number
  last_error?: string | null
  locked_at?: string | null
  created_at: string
  updated_at: string
}

export interface DatahubQualityReportInfo {
  id: string
  dataset: string
  symbol?: string | null
  biz_date?: string | null
  quality_score: number
  severity: string
  issues?: Array<Record<string, unknown>> | null
  object_key?: string | null
  checked_at: string
  created_at: string
}

export interface DatahubObjectIndexInfo {
  id: string
  bucket: string
  object_key: string
  dataset: string
  layer: string
  provider?: string | null
  symbol?: string | null
  start_date?: string | null
  end_date?: string | null
  row_count: number
  schema_version: string
  content_hash?: string | null
  quality_score?: number | null
  created_at: string
}

export interface DatahubWorkerHeartbeatInfo {
  worker_name: string
  status: string
  last_heartbeat_at: string
  last_run_id?: string | null
  processed_count: number
  last_error?: string | null
  is_online: boolean
  offline_threshold_seconds: number
}

export interface TriggerBackfillPayload {
  dataset: string
  start_date: string
  end_date: string
  symbol?: string
}

export interface TriggerDailyIncrementalPayload {
  dataset: string
  symbol?: string
  window_days: number
}

export interface PurgeJobRunsPayload {
  status: string
  limit?: number
}

export interface PurgeJobRunsResult {
  deleted_count: number
}

export interface DatahubFailureGroupInfo {
  error_message: string
  count: number
  symbols: string[]
}

export interface DatahubRunFailureDetailInfo {
  run_id: string
  failed_count: number
  groups: DatahubFailureGroupInfo[]
  tasks: DatahubJobTaskInfo[]
}

export interface RetryFailedTasksPayload {
  strategy: 'immediate' | 'by_error'
  max_retry_attempts: number
}

export interface RetryFailedTasksResult {
  created_runs: number
  skipped_tasks: number
  retried_tasks: number
  retried_symbols: string[]
}

export interface MarketDailyMissingScanResult {
  dataset: string
  start_date: string
  end_date: string
  reference_date: string
  expected_count: number
  existing_count: number
  missing_count: number
  missing_symbols: string[]
}

export interface FillMarketDailyMissingPayload {
  start_date: string
  end_date: string
  reference_date?: string
  max_symbols: number
  batch_size: number
}

export interface FillMarketDailyMissingResult {
  created_runs: number
  filled_symbols: number
  symbols: string[]
}
