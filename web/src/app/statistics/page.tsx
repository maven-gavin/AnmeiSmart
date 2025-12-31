'use client'

import { useEffect, useMemo, useState } from 'react'
import AppLayout from '@/components/layout/AppLayout'
import { useAuthContext } from '@/contexts/AuthContext'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { RefreshCw } from 'lucide-react'
import toast from 'react-hot-toast'
import { taskGovernanceService } from '@/service/taskGovernanceService'
import type { TaskGovernanceMetricsResponse, TaskQueue } from '@/types/task-governance'

function toIso(dt: Date): string {
  return dt.toISOString()
}

function toDateInputValue(dt: Date): string {
  // yyyy-mm-dd
  const yyyy = dt.getFullYear()
  const mm = String(dt.getMonth() + 1).padStart(2, '0')
  const dd = String(dt.getDate()).padStart(2, '0')
  return `${yyyy}-${mm}-${dd}`
}

function parseDateInputValue(value: string): Date | null {
  if (!value) return null
  const dt = new Date(`${value}T00:00:00.000Z`)
  if (Number.isNaN(dt.getTime())) return null
  return dt
}

function safeRate(numerator: number, denominator: number): string {
  if (!denominator) return '--'
  return `${Math.round((numerator / denominator) * 100)}%`
}

export default function StatisticsPage() {
  const { user } = useAuthContext()

  const [loading, setLoading] = useState(false)
  const [metrics, setMetrics] = useState<TaskGovernanceMetricsResponse | null>(null)
  const [queues, setQueues] = useState<TaskQueue[]>([])

  // 默认近7天
  const defaultEnd = useMemo(() => new Date(), [])
  const defaultStart = useMemo(() => {
    const d = new Date()
    d.setDate(d.getDate() - 7)
    return d
  }, [])

  const [startDate, setStartDate] = useState(toDateInputValue(defaultStart))
  const [endDate, setEndDate] = useState(toDateInputValue(defaultEnd))
  const [sceneKey, setSceneKey] = useState<string>('all')

  const sceneKeys = useMemo(() => {
    const set = new Set<string>()
    for (const q of queues) if (q.scene_key) set.add(q.scene_key)
    return Array.from(set).sort()
  }, [queues])

  const loadAll = async () => {
    const start = parseDateInputValue(startDate) || defaultStart
    const end = parseDateInputValue(endDate) || defaultEnd

    // end_at 采用“次日 00:00”以实现日期选择的闭区间体验
    const endExclusive = new Date(end.getTime())
    endExclusive.setDate(endExclusive.getDate() + 1)

    setLoading(true)
    try {
      const [qs, ms] = await Promise.all([
        taskGovernanceService.listQueues({ only_active: false }),
        taskGovernanceService.getMetrics({
          start_at: toIso(start),
          end_at: toIso(endExclusive),
          scene_key: sceneKey === 'all' ? undefined : sceneKey,
        }),
      ])
      setQueues(qs)
      setMetrics(ms)
    } catch {
      // handled by apiClient toast
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadAll()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const summary = useMemo(() => {
    if (!metrics) return null
    const totalRoute = metrics.routing_tasks_created + metrics.sensitive_tasks_created + metrics.config_required_tasks_created
    const sensitiveRate = safeRate(metrics.sensitive_tasks_created, totalRoute)
    const straightThroughRate = safeRate(metrics.routing_tasks_created, totalRoute)
    const slaRate = safeRate(metrics.sla_tasks_on_time, metrics.sla_tasks_total)
    return {
      totalRoute,
      sensitiveRate,
      straightThroughRate,
      slaRate,
    }
  }, [metrics])

  return (
    <AppLayout requiredRole={user?.currentRole}>
      <div className="h-full overflow-y-auto">
        <div className="container mx-auto px-4 py-4 md:py-6">
          <div className="mb-4 md:mb-6 flex items-center justify-between">
            <div>
              <h1 className="text-xl md:text-2xl font-bold text-gray-800">数据统计</h1>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={loadAll} disabled={loading} className="flex items-center gap-2">
                <RefreshCw className="h-4 w-4" />
                刷新
              </Button>
            </div>
          </div>

        <Card className="mb-4 md:mb-6">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">筛选</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
              <div>
                <div className="text-xs text-gray-500 mb-1">开始日期</div>
                <Input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
              </div>
              <div>
                <div className="text-xs text-gray-500 mb-1">结束日期</div>
                <Input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
              </div>
              <div>
                <div className="text-xs text-gray-500 mb-1">场景</div>
                <Select value={sceneKey} onValueChange={setSceneKey}>
                  <SelectTrigger>
                    <SelectValue placeholder="选择场景" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">全部</SelectItem>
                    {sceneKeys.map((k) => (
                      <SelectItem key={k} value={k}>{k}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="flex items-end justify-end">
                <Button
                  onClick={() => {
                    if (!startDate || !endDate) {
                      toast.error('请先选择开始/结束日期')
                      return
                    }
                    loadAll()
                  }}
                  disabled={loading}
                  className="bg-orange-500 hover:bg-orange-600"
                >
                  应用筛选
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="mb-4 md:mb-6 grid grid-cols-1 gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">期间创建任务</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metrics?.tasks_created ?? '--'}</div>
              <div className="text-xs text-muted-foreground">路由生成 + 敏感拦截 + 需要配置</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">直通率</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{summary?.straightThroughRate ?? '--'}</div>
              <div className="text-xs text-muted-foreground">路由生成任务 / 路由相关任务</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">敏感命中率</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{summary?.sensitiveRate ?? '--'}</div>
              <div className="text-xs text-muted-foreground">敏感拦截任务 / 路由相关任务</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">SLA 达标率</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{summary?.slaRate ?? '--'}</div>
              <div className="text-xs text-muted-foreground">有截止时间的已完成任务</div>
            </CardContent>
          </Card>
        </div>

        <div className="mb-4 md:mb-6 grid grid-cols-1 gap-4 md:grid-cols-3">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">完成中位耗时（分钟）</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metrics?.median_cycle_time_minutes?.toFixed?.(1) ?? '--'}</div>
              <div className="text-xs text-muted-foreground">从创建到完成（按 completed_at）</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">完成平均耗时（分钟）</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metrics?.avg_cycle_time_minutes?.toFixed?.(1) ?? '--'}</div>
              <div className="text-xs text-muted-foreground">用于趋势对比</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">当前超期未完成</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metrics?.overdue_open_tasks ?? '--'}</div>
              <div className="text-xs text-muted-foreground">pending/assigned/in_progress 且 due_date 已过</div>
            </CardContent>
          </Card>
        </div>

        <Card className="mb-4 md:mb-6">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">按场景明细</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>scene_key</TableHead>
                  <TableHead>创建</TableHead>
                  <TableHead>路由</TableHead>
                  <TableHead>敏感</TableHead>
                  <TableHead>需配置</TableHead>
                  <TableHead>完成</TableHead>
                  <TableHead>SLA达标</TableHead>
                  <TableHead>超期未完</TableHead>
                  <TableHead>中位耗时(min)</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(metrics?.scenes || []).map((s) => (
                  <TableRow key={s.scene_key}>
                    <TableCell className="font-mono">{s.scene_key}</TableCell>
                    <TableCell>{s.tasks_created}</TableCell>
                    <TableCell>{s.routing_tasks_created}</TableCell>
                    <TableCell>{s.sensitive_tasks_created}</TableCell>
                    <TableCell>{s.config_required_tasks_created}</TableCell>
                    <TableCell>{s.tasks_completed}</TableCell>
                    <TableCell>{safeRate(s.sla_tasks_on_time, s.sla_tasks_total)}</TableCell>
                    <TableCell>{s.overdue_open_tasks}</TableCell>
                    <TableCell>{typeof s.median_cycle_time_minutes === 'number' ? s.median_cycle_time_minutes.toFixed(1) : '--'}</TableCell>
                  </TableRow>
                ))}
                {!metrics?.scenes?.length && (
                  <TableRow>
                    <TableCell colSpan={9} className="text-gray-500">
                      暂无数据（先在“任务治理”配置规则并在对话中触发几条）
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
            </div>
          </CardContent>
        </Card>
        </div>
      </div>
    </AppLayout>
  )
}


