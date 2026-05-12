import { apiClient, handleApiError } from '@/service/apiClient'
import type {
  DatahubDatasetInfo,
  DatahubJobRunInfo,
  DatahubJobTaskInfo,
  DatahubObjectIndexInfo,
  DatahubQualityReportInfo,
  DatahubWorkerHeartbeatInfo,
  TriggerBackfillPayload,
  TriggerDailyIncrementalPayload,
} from '@/types/datahub'

export const datahubService = {
  async seedDatasets(): Promise<number> {
    try {
      const resp = await apiClient.post<number>('/datahub/datasets/seed')
      return resp.data
    } catch (err) {
      handleApiError(err, '初始化数据集目录失败')
      throw err
    }
  },

  async listDatasets(): Promise<DatahubDatasetInfo[]> {
    try {
      const resp = await apiClient.get<DatahubDatasetInfo[]>('/datahub/datasets')
      return resp.data
    } catch (err) {
      handleApiError(err, '获取数据集失败')
      throw err
    }
  },

  async runBackfill(payload: TriggerBackfillPayload): Promise<DatahubJobRunInfo> {
    try {
      const resp = await apiClient.post<DatahubJobRunInfo>('/datahub/jobs/backfill/run', payload)
      return resp.data
    } catch (err) {
      handleApiError(err, '执行回填失败')
      throw err
    }
  },

  async runDailyIncremental(payload: TriggerDailyIncrementalPayload): Promise<DatahubJobRunInfo> {
    try {
      const resp = await apiClient.post<DatahubJobRunInfo>('/datahub/jobs/daily-incremental/run', payload)
      return resp.data
    } catch (err) {
      handleApiError(err, '执行增量失败')
      throw err
    }
  },

  async listJobRuns(limit = 50): Promise<DatahubJobRunInfo[]> {
    try {
      const resp = await apiClient.get<DatahubJobRunInfo[]>(`/datahub/jobs/runs?limit=${limit}`)
      return resp.data
    } catch (err) {
      handleApiError(err, '获取作业列表失败')
      throw err
    }
  },

  async listJobTasks(runId: string): Promise<DatahubJobTaskInfo[]> {
    try {
      const resp = await apiClient.get<DatahubJobTaskInfo[]>(`/datahub/jobs/runs/${runId}/tasks`)
      return resp.data
    } catch (err) {
      handleApiError(err, '获取作业任务失败')
      throw err
    }
  },

  async listQualityReports(params?: { dataset?: string; symbol?: string; limit?: number }): Promise<DatahubQualityReportInfo[]> {
    try {
      const search = new URLSearchParams()
      if (params?.dataset) search.set('dataset', params.dataset)
      if (params?.symbol) search.set('symbol', params.symbol)
      search.set('limit', String(params?.limit ?? 100))
      const resp = await apiClient.get<DatahubQualityReportInfo[]>(`/datahub/quality/reports?${search.toString()}`)
      return resp.data
    } catch (err) {
      handleApiError(err, '获取质量报告失败')
      throw err
    }
  },

  async listObjectIndexes(params?: { dataset?: string; symbol?: string; limit?: number }): Promise<DatahubObjectIndexInfo[]> {
    try {
      const search = new URLSearchParams()
      if (params?.dataset) search.set('dataset', params.dataset)
      if (params?.symbol) search.set('symbol', params.symbol)
      search.set('limit', String(params?.limit ?? 100))
      const resp = await apiClient.get<DatahubObjectIndexInfo[]>(`/datahub/objects/indexes?${search.toString()}`)
      return resp.data
    } catch (err) {
      handleApiError(err, '获取对象索引失败')
      throw err
    }
  },

  async getWorkerHeartbeat(workerName = 'datahub-default-worker'): Promise<DatahubWorkerHeartbeatInfo | null> {
    try {
      const query = new URLSearchParams({
        worker_name: workerName,
        offline_threshold_seconds: '30',
      })
      const resp = await apiClient.get<DatahubWorkerHeartbeatInfo | null>(`/datahub/worker/heartbeat?${query.toString()}`)
      return resp.data
    } catch (err) {
      handleApiError(err, '获取 Worker 心跳失败')
      throw err
    }
  },
}
