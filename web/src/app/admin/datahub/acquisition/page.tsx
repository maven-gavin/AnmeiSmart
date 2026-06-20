'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import toast from 'react-hot-toast'
import { Database, Play, RefreshCw } from 'lucide-react'

import AppLayout from '@/components/layout/AppLayout'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useAuthContext } from '@/contexts/AuthContext'
import { usePermission } from '@/hooks/usePermission'
import { datahubService } from '@/service/datahubService'

export default function DatahubAcquisitionPage() {
  const { user } = useAuthContext()
  const { isAdmin } = usePermission()
  const router = useRouter()

  const [seeding, setSeeding] = useState(false)
  const [runningDaily, setRunningDaily] = useState(false)
  const [runningBackfill, setRunningBackfill] = useState(false)
  const [dailyForm, setDailyForm] = useState({ dataset: 'market_daily', symbol: '', window_days: 7 })
  const [backfillForm, setBackfillForm] = useState({
    dataset: 'market_daily',
    symbol: '',
    start_date: '2024-01-01',
    end_date: '2024-01-31',
  })

  useEffect(() => {
    if (user && !isAdmin) router.push('/unauthorized')
  }, [user, isAdmin, router])

  const seedDatasets = async () => {
    setSeeding(true)
    try {
      const created = await datahubService.seedDatasets()
      toast.success(`初始化完成，新增 ${created} 个数据集`)
    } finally {
      setSeeding(false)
    }
  }

  const runDaily = async () => {
    setRunningDaily(true)
    try {
      await datahubService.runDailyIncremental({
        dataset: dailyForm.dataset,
        symbol: dailyForm.symbol.trim() || undefined,
        window_days: Number(dailyForm.window_days || 7),
      })
      toast.success('每日增量任务已提交')
    } finally {
      setRunningDaily(false)
    }
  }

  const runBackfill = async () => {
    setRunningBackfill(true)
    try {
      await datahubService.runBackfill({
        dataset: backfillForm.dataset,
        symbol: backfillForm.symbol.trim() || undefined,
        start_date: backfillForm.start_date,
        end_date: backfillForm.end_date,
      })
      toast.success('历史回填任务已提交')
    } finally {
      setRunningBackfill(false)
    }
  }

  return (
    <AppLayout requiredRole={user?.currentRole}>
      <div className="am-page">
        <div className="am-container space-y-6">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div>
              <h1 className="am-page-title">数据获取（高级）</h1>
              <p className="text-sm text-gray-500">用于初始化、手动回填和排障。日常请优先使用「每日看盘」。</p>
            </div>
            <Button className="am-btn-outline" onClick={seedDatasets} disabled={seeding}>
              <Database className="mr-1 h-4 w-4" />
              {seeding ? '初始化中...' : '初始化数据集'}
            </Button>
          </div>

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <Card className="am-card">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <RefreshCw className="h-4 w-4" />
                  每日增量
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <Label>数据集</Label>
                  <Input className="am-field mt-1" value={dailyForm.dataset} onChange={(e) => setDailyForm((p) => ({ ...p, dataset: e.target.value }))} />
                </div>
                <div>
                  <Label>证券代码（可选）</Label>
                  <Input className="am-field mt-1" value={dailyForm.symbol} onChange={(e) => setDailyForm((p) => ({ ...p, symbol: e.target.value }))} placeholder="不填则按数据集默认范围" />
                </div>
                <div>
                  <Label>回溯窗口（天）</Label>
                  <Input type="number" min={1} max={30} className="am-field mt-1" value={dailyForm.window_days} onChange={(e) => setDailyForm((p) => ({ ...p, window_days: Number(e.target.value || 7) }))} />
                </div>
                <Button className="am-btn-primary w-full" onClick={runDaily} disabled={runningDaily}>
                  {runningDaily ? '提交中...' : '提交增量任务'}
                </Button>
              </CardContent>
            </Card>

            <Card className="am-card">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Play className="h-4 w-4" />
                  历史回填
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <Label>数据集</Label>
                  <Input className="am-field mt-1" value={backfillForm.dataset} onChange={(e) => setBackfillForm((p) => ({ ...p, dataset: e.target.value }))} />
                </div>
                <div>
                  <Label>证券代码（可选）</Label>
                  <Input className="am-field mt-1" value={backfillForm.symbol} onChange={(e) => setBackfillForm((p) => ({ ...p, symbol: e.target.value }))} placeholder="不填则按数据集默认范围" />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label>开始日期</Label>
                    <Input type="date" className="am-field mt-1" value={backfillForm.start_date} onChange={(e) => setBackfillForm((p) => ({ ...p, start_date: e.target.value }))} />
                  </div>
                  <div>
                    <Label>结束日期</Label>
                    <Input type="date" className="am-field mt-1" value={backfillForm.end_date} onChange={(e) => setBackfillForm((p) => ({ ...p, end_date: e.target.value }))} />
                  </div>
                </div>
                <Button className="am-btn-primary w-full" onClick={runBackfill} disabled={runningBackfill}>
                  {runningBackfill ? '提交中...' : '提交回填任务'}
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </AppLayout>
  )
}
