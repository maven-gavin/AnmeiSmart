'use client'

import { useEffect, useMemo, useState } from 'react'
import { useRouter } from 'next/navigation'
import toast from 'react-hot-toast'
import {
  RefreshCw,
  ListChecks,
  ShieldAlert,
  PackageSearch,
  Activity,
  Trash2,
} from 'lucide-react'

import AppLayout from '@/components/layout/AppLayout'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'
import { EnhancedPagination } from '@/components/ui/pagination'
import { Progress } from '@/components/ui/progress'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { useAuthContext } from '@/contexts/AuthContext'
import { usePermission } from '@/hooks/usePermission'
import { datahubService } from '@/service/datahubService'
import { formatDatasetLabel } from '@/lib/datahub/datasetLabels'
import type {
  DatahubRunFailureDetailInfo,
  DatahubJobRunInfo,
  DatahubJobTaskInfo,
  DatahubObjectIndexInfo,
  DatahubQualityReportInfo,
  RetryFailedTasksPayload,
  DatahubWorkerHeartbeatInfo,
  DatahubProviderHealthInfo,
  DatahubMetricsSummaryInfo,
  DatahubDatasetInfo,
} from '@/types/datahub'

export default function DatahubMonitorPage() {
  const { user } = useAuthContext()
  const { isAdmin } = usePermission()
  const router = useRouter()

  const [loading, setLoading] = useState(true)

  const [runs, setRuns] = useState<DatahubJobRunInfo[]>([])
  const [selectedRunId, setSelectedRunId] = useState<string>('')
  const [tasks, setTasks] = useState<DatahubJobTaskInfo[]>([])
  const [qualityReports, setQualityReports] = useState<DatahubQualityReportInfo[]>([])
  const [objectIndexes, setObjectIndexes] = useState<DatahubObjectIndexInfo[]>([])
  const [datasetCatalog, setDatasetCatalog] = useState<DatahubDatasetInfo[]>([])
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [workerHeartbeat, setWorkerHeartbeat] = useState<DatahubWorkerHeartbeatInfo | null>(null)
  const [providerHealthRows, setProviderHealthRows] = useState<DatahubProviderHealthInfo[]>([])
  const [metricsSummary, setMetricsSummary] = useState<DatahubMetricsSummaryInfo | null>(null)
  const [purgeFailedDialogOpen, setPurgeFailedDialogOpen] = useState(false)
  const [purgeFailedLoading, setPurgeFailedLoading] = useState(false)
  const [deleteRunDialogOpen, setDeleteRunDialogOpen] = useState(false)
  const [deleteRunLoading, setDeleteRunLoading] = useState(false)
  const [runToDelete, setRunToDelete] = useState<DatahubJobRunInfo | null>(null)
  const [failureDetailOpen, setFailureDetailOpen] = useState(false)
  const [failureDetailLoading, setFailureDetailLoading] = useState(false)
  const [retryFailedLoading, setRetryFailedLoading] = useState(false)
  const [failureDetail, setFailureDetail] = useState<DatahubRunFailureDetailInfo | null>(null)
  const [retryStrategy, setRetryStrategy] = useState<RetryFailedTasksPayload['strategy']>('immediate')
  const [retryMaxAttempts, setRetryMaxAttempts] = useState(3)

  const [runFilter, setRunFilter] = useState({ dataset: '', status: '', keyword: '', page: 1, pageSize: 10 })
  const [taskFilter, setTaskFilter] = useState({ status: '', symbol: '', page: 1, pageSize: 10 })
  const [qualityFilter, setQualityFilter] = useState({ dataset: '', symbol: '', severity: '', page: 1, pageSize: 10 })
  const [objectFilter, setObjectFilter] = useState({ dataset: '', symbol: '', page: 1, pageSize: 10 })

  useEffect(() => {
    if (user && !isAdmin) {
      router.push('/unauthorized')
    }
  }, [user, isAdmin, router])

  const loadAll = async () => {
    setLoading(true)
    try {
      const [jobRuns, reports, indexes, heartbeat] = await Promise.all([
        datahubService.listJobRuns(100),
        datahubService.listQualityReports({ limit: 100 }),
        datahubService.listObjectIndexes({ limit: 100 }),
        datahubService.getWorkerHeartbeat().catch(() => null),
      ])
      const providerHealth = await datahubService.listProviderHealth({ limit: 100 })
      const metrics = await datahubService.getMetricsSummary(7)
      const datasets = await datahubService.listDatasets()
      setDatasetCatalog(datasets)
      setRuns(jobRuns)
      setQualityReports(reports)
      setObjectIndexes(indexes)
      setWorkerHeartbeat(heartbeat)
      setProviderHealthRows(providerHealth)
      setMetricsSummary(metrics)

      if (jobRuns.length > 0) {
        const runStillExists = selectedRunId !== '' && jobRuns.some((r) => r.id === selectedRunId)
        const runId = runStillExists ? selectedRunId : jobRuns[0].id
        setSelectedRunId(runId)
        const runTasks = await datahubService.listJobTasks(runId)
        setTasks(runTasks)
      } else {
        setSelectedRunId('')
        setTasks([])
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadAll()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    if (!autoRefresh) return
    const timer = window.setInterval(() => {
      loadAll()
    }, 10000)
    return () => window.clearInterval(timer)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoRefresh])

  const selectedRun = useMemo(() => runs.find((item) => item.id === selectedRunId), [runs, selectedRunId])

  const onSelectRun = async (runId: string) => {
    setSelectedRunId(runId)
    const runTasks = await datahubService.listJobTasks(runId)
    setTasks(runTasks)
  }

  const datasetLabelMap = useMemo(() => {
    const map: Record<string, string | null | undefined> = {}
    datasetCatalog.forEach((item) => {
      map[item.dataset_key] = item.label_zh
    })
    return map
  }, [datasetCatalog])

  const formatDataset = (key?: string | null) => {
    if (!key) return '-'
    return formatDatasetLabel(key, datasetLabelMap[key])
  }

  const runStats = useMemo(() => {
    return {
      total: runs.length,
      success: runs.filter((r) => r.status === 'success').length,
      failed: runs.filter((r) => r.status === 'failed').length,
      running: runs.filter((r) => r.status === 'running').length,
    }
  }, [runs])

  const getRunProgress = (run: DatahubJobRunInfo) => {
    if (run.task_total <= 0) {
      if (run.status === 'success') return 100
      if (run.status === 'failed') return 100
      return 0
    }
    const completed = run.task_success + run.task_failed
    return Math.min(100, Math.round((completed / run.task_total) * 100))
  }

  const failedRunsCount = useMemo(() => runs.filter((r) => r.status === 'failed').length, [runs])

  const confirmPurgeFailedRuns = async () => {
    setPurgeFailedLoading(true)
    try {
      let total = 0
      for (let i = 0; i < 50; i += 1) {
        const { deleted_count } = await datahubService.purgeJobRuns({ status: 'failed', limit: 500 })
        total += deleted_count
        if (deleted_count === 0) break
      }
      toast.success(`已删除 ${total} 条失败作业记录`)
      setPurgeFailedDialogOpen(false)
      await loadAll()
    } finally {
      setPurgeFailedLoading(false)
    }
  }

  const confirmDeleteSingleRun = async () => {
    if (!runToDelete) return
    setDeleteRunLoading(true)
    try {
      if (selectedRunId === runToDelete.id) {
        setSelectedRunId('')
      }
      await datahubService.deleteJobRun(runToDelete.id)
      toast.success('作业记录已删除')
      setDeleteRunDialogOpen(false)
      setRunToDelete(null)
      await loadAll()
    } finally {
      setDeleteRunLoading(false)
    }
  }

  const openFailureDetail = async (runId: string) => {
    setFailureDetailLoading(true)
    setFailureDetailOpen(true)
    try {
      const detail = await datahubService.getRunFailureDetail(runId, 500)
      setFailureDetail(detail)
    } finally {
      setFailureDetailLoading(false)
    }
  }

  const retryFailedTasks = async () => {
    if (!failureDetail?.run_id) return
    setRetryFailedLoading(true)
    try {
      const result = await datahubService.retryFailedTasks(failureDetail.run_id, {
        strategy: retryStrategy,
        max_retry_attempts: retryMaxAttempts,
      })
      toast.success(
        `已提交重试：新建 ${result.created_runs} 个run，重试 ${result.retried_tasks} 条，跳过 ${result.skipped_tasks} 条`,
      )
      const detail = await datahubService.getRunFailureDetail(failureDetail.run_id, 500)
      setFailureDetail(detail)
      await loadAll()
    } finally {
      setRetryFailedLoading(false)
    }
  }

  const getRunStatusLabel = (run: DatahubJobRunInfo) => {
    if (run.status === 'failed' && run.task_success > 0) return 'partial_failed'
    return run.status
  }

  const filteredRuns = useMemo(() => {
    return runs.filter((run) => {
      if (runFilter.dataset && run.dataset !== runFilter.dataset) return false
      if (runFilter.status && run.status !== runFilter.status) return false
      if (runFilter.keyword) {
        const keyword = runFilter.keyword.toLowerCase()
        const hit = `${run.id} ${run.job_type} ${run.dataset || ''} ${run.error_message || ''}`.toLowerCase().includes(keyword)
        if (!hit) return false
      }
      return true
    })
  }, [runs, runFilter])

  const pagedRuns = useMemo(() => {
    const start = (runFilter.page - 1) * runFilter.pageSize
    return filteredRuns.slice(start, start + runFilter.pageSize)
  }, [filteredRuns, runFilter.page, runFilter.pageSize])

  const filteredTasks = useMemo(() => {
    return tasks.filter((task) => {
      if (taskFilter.status && task.status !== taskFilter.status) return false
      if (taskFilter.symbol && !(task.symbol || '').toLowerCase().includes(taskFilter.symbol.toLowerCase())) return false
      return true
    })
  }, [tasks, taskFilter])

  const pagedTasks = useMemo(() => {
    const start = (taskFilter.page - 1) * taskFilter.pageSize
    return filteredTasks.slice(start, start + taskFilter.pageSize)
  }, [filteredTasks, taskFilter.page, taskFilter.pageSize])

  const filteredQualityReports = useMemo(() => {
    return qualityReports.filter((report) => {
      if (qualityFilter.dataset && report.dataset !== qualityFilter.dataset) return false
      if (qualityFilter.symbol && !(report.symbol || '').toLowerCase().includes(qualityFilter.symbol.toLowerCase())) return false
      if (qualityFilter.severity && report.severity !== qualityFilter.severity) return false
      return true
    })
  }, [qualityReports, qualityFilter])

  const pagedQualityReports = useMemo(() => {
    const start = (qualityFilter.page - 1) * qualityFilter.pageSize
    return filteredQualityReports.slice(start, start + qualityFilter.pageSize)
  }, [filteredQualityReports, qualityFilter.page, qualityFilter.pageSize])

  const filteredObjectIndexes = useMemo(() => {
    return objectIndexes.filter((row) => {
      if (objectFilter.dataset && row.dataset !== objectFilter.dataset) return false
      if (objectFilter.symbol && !(row.symbol || '').toLowerCase().includes(objectFilter.symbol.toLowerCase())) return false
      return true
    })
  }, [objectIndexes, objectFilter])

  const pagedObjectIndexes = useMemo(() => {
    const start = (objectFilter.page - 1) * objectFilter.pageSize
    return filteredObjectIndexes.slice(start, start + objectFilter.pageSize)
  }, [filteredObjectIndexes, objectFilter.page, objectFilter.pageSize])

  return (
    <AppLayout requiredRole={user?.currentRole}>
      <div className="am-page">
        <div className="am-container space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="am-page-title">运行监控</h1>
              <p className="text-sm text-gray-500">查看作业运行、Worker 状态、质量报告与 Provider 健康</p>
            </div>
            <div className="flex gap-2">
              <div className="flex items-center gap-2 rounded border border-gray-200 bg-white px-3">
                <span className="text-xs text-gray-600">自动轮询</span>
                <Switch checked={autoRefresh} onCheckedChange={setAutoRefresh} />
              </div>
              <Button className="am-btn-reset" onClick={loadAll} disabled={loading}>
                <RefreshCw className="mr-1 h-4 w-4" />
                刷新
              </Button>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
            <Card className="am-card">
              <CardHeader className="pb-2"><CardTitle className="text-sm">作业总数</CardTitle></CardHeader>
              <CardContent className="text-2xl font-bold">{runStats.total}</CardContent>
            </Card>
            <Card className="am-card">
              <CardHeader className="pb-2"><CardTitle className="text-sm">成功</CardTitle></CardHeader>
              <CardContent className="text-2xl font-bold text-green-700">{runStats.success}</CardContent>
            </Card>
            <Card className="am-card">
              <CardHeader className="pb-2"><CardTitle className="text-sm">失败</CardTitle></CardHeader>
              <CardContent className="text-2xl font-bold text-red-600">{runStats.failed}</CardContent>
            </Card>
            <Card className="am-card">
              <CardHeader className="pb-2"><CardTitle className="text-sm">运行中</CardTitle></CardHeader>
              <CardContent className="text-2xl font-bold text-brand-primaryHover">{runStats.running}</CardContent>
            </Card>
          </div>

          {metricsSummary && (
            <Card className="am-card">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">近 {metricsSummary.window_days} 天运行指标</CardTitle>
              </CardHeader>
              <CardContent className="grid grid-cols-1 gap-2 text-sm text-gray-700 md:grid-cols-3">
                <div>成功率：{(metricsSummary.success_rate * 100).toFixed(2)}%</div>
                <div>平均耗时：{metricsSummary.avg_duration_seconds.toFixed(2)}s</div>
                <div>P95 耗时：{metricsSummary.p95_duration_seconds.toFixed(2)}s</div>
                <div>平均质量分：{metricsSummary.avg_quality_score.toFixed(2)}</div>
                <div>P0 质量问题：{metricsSummary.p0_quality_count}</div>
                <div>Provider 冷却/降级：{metricsSummary.provider_cooldown_count}/{metricsSummary.provider_degraded_count}</div>
              </CardContent>
            </Card>
          )}

          <Card className="am-card">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Worker 心跳</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              {workerHeartbeat ? (
                <>
                  <div className="grid grid-cols-1 gap-2 md:grid-cols-3">
                    <div className="flex items-center gap-2 md:col-span-3">
                      <Badge className={workerHeartbeat.is_online ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-700'}>
                        {workerHeartbeat.is_online ? '在线' : '离线'}
                      </Badge>
                      <span className="text-gray-600">{workerHeartbeat.worker_name}</span>
                    </div>
                    <div className="text-gray-600">状态：{workerHeartbeat.status}</div>
                    <div className="text-gray-600">最近心跳：{workerHeartbeat.last_heartbeat_at}</div>
                    <div className="text-gray-600">累计处理：{workerHeartbeat.processed_count}</div>
                    {workerHeartbeat.last_run_id ? (
                      <div className="text-gray-600 md:col-span-2">最近作业：{workerHeartbeat.last_run_id}</div>
                    ) : (
                      <div />
                    )}
                    {workerHeartbeat.last_error ? (
                      <div className="text-red-600 md:col-span-2">最近错误：{workerHeartbeat.last_error}</div>
                    ) : (
                      <div />
                    )}
                  </div>
                </>
              ) : (
                <div className="text-gray-500">尚未检测到心跳，请确认 worker 已启动。</div>
              )}
            </CardContent>
          </Card>

          <Tabs defaultValue="runs" className="space-y-4">
            <TabsList className="grid w-full grid-cols-5">
              <TabsTrigger value="runs">作业运行</TabsTrigger>
              <TabsTrigger value="tasks">作业任务</TabsTrigger>
              <TabsTrigger value="quality">质量报告</TabsTrigger>
              <TabsTrigger value="objects">对象索引</TabsTrigger>
              <TabsTrigger value="providers">Provider 健康</TabsTrigger>
            </TabsList>

            <TabsContent value="runs">
              <Card className="am-card">
                <CardHeader className="flex flex-row items-center justify-between space-y-0">
                  <CardTitle className="flex items-center gap-2">
                    <ListChecks className="h-4 w-4" />
                    作业运行记录
                  </CardTitle>
                  <Button
                    type="button"
                    className="text-red-600 hover:bg-red-50 hover:text-red-700 border-red-300"
                    variant="outline"
                    disabled={purgeFailedLoading || failedRunsCount === 0}
                    onClick={() => setPurgeFailedDialogOpen(true)}
                  >
                    清理全部失败记录
                  </Button>
                </CardHeader>
                <CardContent>
                  <div className="mb-3 grid grid-cols-1 gap-2 md:grid-cols-4">
                    <Input placeholder="筛选数据集" value={runFilter.dataset} className="am-field" onChange={(e) => setRunFilter((p) => ({ ...p, dataset: e.target.value, page: 1 }))} />
                    <Input placeholder="筛选 status" value={runFilter.status} className="am-field" onChange={(e) => setRunFilter((p) => ({ ...p, status: e.target.value, page: 1 }))} />
                    <Input placeholder="关键词（id/错误）" value={runFilter.keyword} className="am-field" onChange={(e) => setRunFilter((p) => ({ ...p, keyword: e.target.value, page: 1 }))} />
                    <Button className="am-btn-reset" onClick={() => setRunFilter({ dataset: '', status: '', keyword: '', page: 1, pageSize: runFilter.pageSize })}>重置筛选</Button>
                  </div>
                  <div className="space-y-2">
                    {pagedRuns.map((run) => (
                      <div
                        key={run.id}
                        role="presentation"
                        className={`rounded border p-3 text-left ${selectedRunId === run.id ? 'border-brand-primary bg-brand-soft' : 'border-gray-200 bg-white'}`}
                      >
                        <div className="flex items-start gap-2">
                          <button
                            type="button"
                            onClick={() => onSelectRun(run.id)}
                            className="min-w-0 flex-1 text-left hover:opacity-90"
                          >
                            <div className="flex items-center justify-between gap-2">
                              <div className="text-sm font-medium text-gray-900">
                                {run.job_type} · {formatDataset(run.dataset)}
                              </div>
                              <Badge
                                className={
                                  getRunStatusLabel(run) === 'success'
                                    ? 'bg-green-100 text-green-800'
                                    : getRunStatusLabel(run) === 'partial_failed'
                                      ? 'bg-yellow-100 text-yellow-800'
                                      : getRunStatusLabel(run) === 'failed'
                                        ? 'bg-red-100 text-red-700'
                                        : 'bg-brand-soft text-brand-primaryHover'
                                }
                              >
                                {getRunStatusLabel(run)}
                              </Badge>
                            </div>
                            <div className="mt-1 text-xs text-gray-500">
                              {run.id} · success {run.task_success}/{run.task_total} · failed {run.task_failed}
                            </div>
                            <div className="mt-2">
                              <div className="mb-1 flex items-center justify-between text-[11px] text-gray-500">
                                <span>进度</span>
                                <span>{getRunProgress(run)}%</span>
                              </div>
                              <Progress value={getRunProgress(run)} />
                            </div>
                            {(run.error_message || run.task_failed > 0) && (
                              <div className="mt-2 flex items-center justify-between gap-2">
                                <div className="truncate text-xs text-red-600">{run.error_message || `failed=${run.task_failed}`}</div>
                                <span
                                  role="button"
                                  tabIndex={0}
                                  className="shrink-0 cursor-pointer rounded border border-brand-primary px-2 py-1 text-xs text-brand-primaryHover hover:bg-brand-soft"
                                  onClick={(e) => {
                                    e.preventDefault()
                                    e.stopPropagation()
                                    void openFailureDetail(run.id)
                                  }}
                                  onKeyDown={(e) => {
                                    if (e.key === 'Enter' || e.key === ' ') {
                                      e.preventDefault()
                                      e.stopPropagation()
                                      void openFailureDetail(run.id)
                                    }
                                  }}
                                >
                                  查看失败({run.task_failed})
                                </span>
                              </div>
                            )}
                          </button>
                          <Button
                            type="button"
                            variant="outline"
                            size="icon"
                            title={run.status === 'running' ? '运行中的作业不可删除' : '删除此条记录'}
                            disabled={run.status === 'running' || deleteRunLoading}
                            className="shrink-0 text-red-600 hover:bg-red-50 hover:text-red-700 border-red-300"
                            onClick={() => {
                              setRunToDelete(run)
                              setDeleteRunDialogOpen(true)
                            }}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    ))}
                    {filteredRuns.length === 0 && <div className="text-sm text-gray-500">暂无作业记录</div>}
                  </div>
                  <div className="mt-4">
                    <EnhancedPagination
                      currentPage={runFilter.page}
                      totalPages={Math.ceil(filteredRuns.length / runFilter.pageSize) || 1}
                      totalItems={filteredRuns.length}
                      itemsPerPage={runFilter.pageSize}
                      onPageChange={(page) => setRunFilter((p) => ({ ...p, page }))}
                      onItemsPerPageChange={(pageSize) => setRunFilter((p) => ({ ...p, pageSize, page: 1 }))}
                    />
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="tasks">
              <Card className="am-card">
                <CardHeader><CardTitle>作业任务明细 {selectedRun ? `(${selectedRun.id})` : ''}</CardTitle></CardHeader>
                <CardContent className="space-y-2">
                  <div className="mb-3 grid grid-cols-1 gap-2 md:grid-cols-3">
                    <Input placeholder="筛选 status" value={taskFilter.status} className="am-field" onChange={(e) => setTaskFilter((p) => ({ ...p, status: e.target.value, page: 1 }))} />
                    <Input placeholder="筛选 symbol" value={taskFilter.symbol} className="am-field" onChange={(e) => setTaskFilter((p) => ({ ...p, symbol: e.target.value, page: 1 }))} />
                    <Button className="am-btn-reset" onClick={() => setTaskFilter({ status: '', symbol: '', page: 1, pageSize: taskFilter.pageSize })}>重置筛选</Button>
                  </div>
                  {pagedTasks.map((task) => (
                    <div key={task.id} className="rounded border border-gray-200 p-3">
                      <div className="flex items-center justify-between">
                        <div className="text-sm font-medium">{task.symbol || '-'}</div>
                        <Badge className={task.status === 'success' ? 'bg-green-100 text-green-800' : task.status === 'failed' ? 'bg-red-100 text-red-700' : 'bg-brand-soft text-brand-primaryHover'}>
                          {task.status}
                        </Badge>
                      </div>
                      <div className="mt-1 text-xs text-gray-500">
                        {formatDataset(task.dataset)} · {task.start_date || '-'} ~ {task.end_date || '-'} · attempts={task.attempts}
                      </div>
                      {task.last_error && <div className="mt-1 text-xs text-red-600">{task.last_error}</div>}
                    </div>
                  ))}
                  {filteredTasks.length === 0 && <div className="text-sm text-gray-500">暂无任务明细，请先选择一个作业。</div>}
                  <div className="mt-4">
                    <EnhancedPagination
                      currentPage={taskFilter.page}
                      totalPages={Math.ceil(filteredTasks.length / taskFilter.pageSize) || 1}
                      totalItems={filteredTasks.length}
                      itemsPerPage={taskFilter.pageSize}
                      onPageChange={(page) => setTaskFilter((p) => ({ ...p, page }))}
                      onItemsPerPageChange={(pageSize) => setTaskFilter((p) => ({ ...p, pageSize, page: 1 }))}
                    />
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="quality">
              <Card className="am-card">
                <CardHeader><CardTitle className="flex items-center gap-2"><ShieldAlert className="h-4 w-4" />质量报告</CardTitle></CardHeader>
                <CardContent className="space-y-2">
                  <div className="mb-3 grid grid-cols-1 gap-2 md:grid-cols-4">
                    <Input placeholder="筛选数据集" value={qualityFilter.dataset} className="am-field" onChange={(e) => setQualityFilter((p) => ({ ...p, dataset: e.target.value, page: 1 }))} />
                    <Input placeholder="筛选 symbol" value={qualityFilter.symbol} className="am-field" onChange={(e) => setQualityFilter((p) => ({ ...p, symbol: e.target.value, page: 1 }))} />
                    <Input placeholder="筛选 severity" value={qualityFilter.severity} className="am-field" onChange={(e) => setQualityFilter((p) => ({ ...p, severity: e.target.value, page: 1 }))} />
                    <Button className="am-btn-reset" onClick={() => setQualityFilter({ dataset: '', symbol: '', severity: '', page: 1, pageSize: qualityFilter.pageSize })}>重置筛选</Button>
                  </div>
                  {pagedQualityReports.map((report) => (
                    <div key={report.id} className="rounded border border-gray-200 p-3">
                      <div className="flex items-center justify-between">
                        <div className="text-sm font-medium">{formatDataset(report.dataset)} · {report.symbol || '-'}</div>
                        <Badge className={report.severity === 'p0' ? 'bg-red-100 text-red-700' : report.severity === 'p1' ? 'bg-yellow-100 text-yellow-800' : 'bg-blue-100 text-blue-800'}>
                          {report.severity}
                        </Badge>
                      </div>
                      <div className="mt-1 text-xs text-gray-500">
                        score={report.quality_score.toFixed(2)} · {report.checked_at}
                      </div>
                      {report.object_key && <div className="mt-1 text-xs text-gray-600 break-all">{report.object_key}</div>}
                    </div>
                  ))}
                  {filteredQualityReports.length === 0 && <div className="text-sm text-gray-500">暂无质量报告</div>}
                  <div className="mt-4">
                    <EnhancedPagination
                      currentPage={qualityFilter.page}
                      totalPages={Math.ceil(filteredQualityReports.length / qualityFilter.pageSize) || 1}
                      totalItems={filteredQualityReports.length}
                      itemsPerPage={qualityFilter.pageSize}
                      onPageChange={(page) => setQualityFilter((p) => ({ ...p, page }))}
                      onItemsPerPageChange={(pageSize) => setQualityFilter((p) => ({ ...p, pageSize, page: 1 }))}
                    />
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="objects">
              <Card className="am-card">
                <CardHeader><CardTitle className="flex items-center gap-2"><PackageSearch className="h-4 w-4" />对象索引</CardTitle></CardHeader>
                <CardContent className="space-y-2">
                  <div className="mb-3 grid grid-cols-1 gap-2 md:grid-cols-3">
                    <Input placeholder="筛选数据集" value={objectFilter.dataset} className="am-field" onChange={(e) => setObjectFilter((p) => ({ ...p, dataset: e.target.value, page: 1 }))} />
                    <Input placeholder="筛选 symbol" value={objectFilter.symbol} className="am-field" onChange={(e) => setObjectFilter((p) => ({ ...p, symbol: e.target.value, page: 1 }))} />
                    <Button className="am-btn-reset" onClick={() => setObjectFilter({ dataset: '', symbol: '', page: 1, pageSize: objectFilter.pageSize })}>重置筛选</Button>
                  </div>
                  {pagedObjectIndexes.map((row) => (
                    <div key={row.id} className="rounded border border-gray-200 p-3">
                      <div className="flex items-center justify-between">
                        <div className="text-sm font-medium">{formatDataset(row.dataset)} · {row.symbol || '-'}</div>
                        <Badge variant="outline">{row.layer}</Badge>
                      </div>
                      <div className="mt-1 text-xs text-gray-500">
                        provider={row.provider || '-'} · rows={row.row_count} · {row.start_date || '-'} ~ {row.end_date || '-'}
                      </div>
                      <div className="mt-1 text-xs text-gray-600 break-all">{row.object_key}</div>
                    </div>
                  ))}
                  {filteredObjectIndexes.length === 0 && <div className="text-sm text-gray-500">暂无对象索引</div>}
                  <div className="mt-4">
                    <EnhancedPagination
                      currentPage={objectFilter.page}
                      totalPages={Math.ceil(filteredObjectIndexes.length / objectFilter.pageSize) || 1}
                      totalItems={filteredObjectIndexes.length}
                      itemsPerPage={objectFilter.pageSize}
                      onPageChange={(page) => setObjectFilter((p) => ({ ...p, page }))}
                      onItemsPerPageChange={(pageSize) => setObjectFilter((p) => ({ ...p, pageSize, page: 1 }))}
                    />
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="providers">
              <Card className="am-card">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Activity className="h-4 w-4" />
                    Provider 健康状态
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {providerHealthRows.map((row) => (
                    <div key={`${row.provider}-${row.dataset}`} className="rounded border border-gray-200 p-3">
                      <div className="flex items-center justify-between">
                        <div className="text-sm font-medium">{row.provider} · {formatDataset(row.dataset)}</div>
                        <Badge className={row.is_available ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-700'}>
                          {row.is_available ? row.status : 'cooldown'}
                        </Badge>
                      </div>
                      <div className="mt-1 text-xs text-gray-600">
                        success={row.success_count} · failure={row.failure_count} · failure_rate={(row.failure_rate * 100).toFixed(2)}%
                      </div>
                      {row.cooldown_until && (
                        <div className="mt-1 text-xs text-amber-700">cooldown_until: {row.cooldown_until}</div>
                      )}
                      {row.last_error && (
                        <div className="mt-1 break-all text-xs text-red-600">{row.last_error}</div>
                      )}
                    </div>
                  ))}
                  {providerHealthRows.length === 0 && <div className="text-sm text-gray-500">暂无 Provider 健康记录</div>}
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </div>
      <Dialog open={failureDetailOpen} onOpenChange={setFailureDetailOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>失败明细 {failureDetail?.run_id ? `(${failureDetail.run_id})` : ''}</DialogTitle>
          </DialogHeader>
          {failureDetailLoading ? (
            <div className="py-8 text-center text-sm text-gray-500">加载中...</div>
          ) : failureDetail ? (
            <div className="space-y-3">
              <div className="grid grid-cols-1 gap-2 rounded border border-gray-200 bg-gray-50 p-3 text-sm md:grid-cols-3">
                <div>失败任务：{failureDetail.failed_count}</div>
                <div>
                  <Label className="text-xs text-gray-500">重试策略</Label>
                  <select
                    className="am-field mt-1 h-9 w-full rounded border px-2 text-sm"
                    value={retryStrategy}
                    onChange={(e) => setRetryStrategy(e.target.value as RetryFailedTasksPayload['strategy'])}
                  >
                    <option value="immediate">立即重试</option>
                    <option value="by_error">按错误分组重试</option>
                  </select>
                </div>
                <div>
                  <Label className="text-xs text-gray-500">最大重试次数</Label>
                  <Input
                    type="number"
                    min={1}
                    max={10}
                    className="am-field mt-1 h-9"
                    value={retryMaxAttempts}
                    onChange={(e) => setRetryMaxAttempts(Number(e.target.value || 3))}
                  />
                </div>
              </div>
              <Button className="am-btn-primary w-full" disabled={retryFailedLoading} onClick={retryFailedTasks}>
                {retryFailedLoading ? '提交重试中...' : `重试失败项 (${failureDetail.failed_count})`}
              </Button>
              <div className="max-h-[40vh] space-y-2 overflow-auto">
                {failureDetail.groups.map((group, idx) => (
                  <div key={`${group.error_message}-${idx}`} className="rounded border border-gray-200 p-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-medium text-red-600">失败 {group.count} 条</span>
                      <span className="text-xs text-gray-500">{group.symbols.slice(0, 3).join(', ')}</span>
                    </div>
                    <div className="mt-1 whitespace-pre-wrap text-xs text-gray-700">{group.error_message}</div>
                  </div>
                ))}
                {failureDetail.groups.length === 0 && (
                  <div className="py-6 text-center text-sm text-gray-500">当前无失败任务</div>
                )}
              </div>
            </div>
          ) : (
            <div className="py-8 text-center text-sm text-gray-500">暂无失败明细</div>
          )}
        </DialogContent>
      </Dialog>

      <AlertDialog
        open={purgeFailedDialogOpen}
        onOpenChange={(open) => {
          if (open) {
            setPurgeFailedDialogOpen(true)
          } else if (!purgeFailedLoading) {
            setPurgeFailedDialogOpen(false)
          }
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>清理全部失败记录</AlertDialogTitle>
            <AlertDialogDescription>
              将按批次从数据库删除状态为 failed 的作业运行记录（含关联子任务）。此操作不可恢复。当前约有 {failedRunsCount} 条失败记录。
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={purgeFailedLoading}>取消</AlertDialogCancel>
            <AlertDialogAction
              className="bg-red-600 hover:bg-red-700"
              disabled={purgeFailedLoading}
              onClick={(e) => {
                e.preventDefault()
                void confirmPurgeFailedRuns()
              }}
            >
              {purgeFailedLoading ? '清理中…' : '确认清理'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <AlertDialog
        open={deleteRunDialogOpen}
        onOpenChange={(open) => {
          if (open) {
            setDeleteRunDialogOpen(true)
          } else if (!deleteRunLoading) {
            setDeleteRunDialogOpen(false)
            setRunToDelete(null)
          }
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>删除作业记录</AlertDialogTitle>
            <AlertDialogDescription>
              删除后无法恢复。
              {runToDelete ? (
                <span className="mt-2 block font-mono text-xs text-gray-700">{runToDelete.id}</span>
              ) : null}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={deleteRunLoading}>取消</AlertDialogCancel>
            <AlertDialogAction
              className="bg-red-600 hover:bg-red-700"
              disabled={deleteRunLoading}
              onClick={(e) => {
                e.preventDefault()
                void confirmDeleteSingleRun()
              }}
            >
              {deleteRunLoading ? '删除中…' : '确认删除'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </AppLayout>
  )
}
