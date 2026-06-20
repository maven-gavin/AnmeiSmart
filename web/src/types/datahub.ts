export interface DatahubDatasetInfo {
  id: string
  dataset_key: string
  label_zh?: string | null
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

export interface DatahubProviderHealthInfo {
  provider: string
  dataset: string
  status: string
  success_count: number
  failure_count: number
  failure_rate: number
  last_success_at?: string | null
  last_failure_at?: string | null
  last_error?: string | null
  cooldown_until?: string | null
  is_available: boolean
}

export interface DatahubMetricsSummaryInfo {
  window_days: number
  total_runs: number
  success_runs: number
  failed_runs: number
  running_runs: number
  success_rate: number
  avg_duration_seconds: number
  p95_duration_seconds: number
  avg_quality_score: number
  p0_quality_count: number
  provider_cooldown_count: number
  provider_degraded_count: number
}

export interface TriggerBackfillPayload {
  dataset: string
  start_date: string
  end_date: string
  symbol?: string
  symbols?: string[]
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

export interface DatahubWatchlistInfo {
  id: string
  symbol: string
  name?: string | null
  sort_order: number
  note?: string | null
  backfill_start_date?: string | null
  backfill_end_date?: string | null
  window_days?: number | null
  created_at: string
  updated_at: string
}

export interface DatahubWatchlistUpdatePayload {
  name?: string
  note?: string
}

export interface MarketDailyBarInfo {
  symbol: string
  trade_date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  amount: number
  turnover_rate?: number | null
}

export interface WatchlistBoardRow {
  id: string
  symbol: string
  name?: string | null
  sector_name?: string | null
  trade_date?: string | null
  open?: number | null
  high?: number | null
  low?: number | null
  close?: number | null
  change_amount?: number | null
  change_pct?: number | null
  sector_change_pct?: number | null
  volume?: number | null
  turnover_rate?: number | null
  has_data: boolean
}

export interface WatchlistBoardResponse {
  limit_days: number
  rows: WatchlistBoardRow[]
}

export interface DatahubWatchlistWatermarkInfo {
  dataset: string
  dataset_label: string
  last_success_date?: string | null
  last_quality_score?: number | null
}

export interface DatahubWatchlistSymbolSummary {
  symbol: string
  name?: string | null
  backfill_start_date?: string | null
  backfill_end_date?: string | null
  window_days?: number | null
  market_daily_start_date?: string | null
  market_daily_end_date?: string | null
  market_daily_row_count: number
  market_daily_quality_score?: number | null
  latest_quality_score?: number | null
  latest_quality_severity?: string | null
  watermarks: DatahubWatchlistWatermarkInfo[]
  object_indexes: Array<{
    dataset: string
    dataset_label: string
    start_date?: string | null
    end_date?: string | null
    row_count: number
    quality_score?: number | null
    object_key: string
  }>
  quality_reports: Array<{
    dataset: string
    dataset_label: string
    biz_date?: string | null
    quality_score: number
    severity: string
    checked_at?: string | null
  }>
}

export interface DailyBriefReadinessInfo {
  as_of_date: string
  status: string
  latest_trade_date?: string | null
  watchlist_count: number
  missing_count: number
  worker_online: boolean
  warnings: string[]
}

export interface DailyBriefMarketInfo {
  indices: Array<Record<string, unknown>>
  five_day_trend: string
  turnover_summary?: Record<string, unknown> | null
  breadth?: Record<string, unknown> | null
}

export interface DailyBriefSectorInfo {
  sector_name: string
  stock_count: number
  avg_stock_change_pct?: number | null
  sector_change_pct?: number | null
}

export interface DailyBriefWatchlistItemInfo {
  symbol: string
  name?: string | null
  sector_name?: string | null
  trade_date?: string | null
  close?: number | null
  change_pct?: number | null
  sector_change_pct?: number | null
  volume?: number | null
  turnover_rate?: number | null
  has_data: boolean
  data_status: string
}

export interface DailyBriefRiskFlagInfo {
  level: string
  source: string
  message: string
  symbol?: string | null
}

export interface DailyBriefContextInfo {
  as_of_date: string
  readiness: DailyBriefReadinessInfo
  market: DailyBriefMarketInfo
  related_sectors: DailyBriefSectorInfo[]
  watchlist: DailyBriefWatchlistItemInfo[]
  portfolio?: Record<string, unknown> | null
  observations: Array<Record<string, unknown>>
  risk_flags: DailyBriefRiskFlagInfo[]
  data_quality: Record<string, string>
}

export interface DailyBriefPrepareResultInfo {
  created_runs: number
  runs: DatahubJobRunInfo[]
  message: string
}
