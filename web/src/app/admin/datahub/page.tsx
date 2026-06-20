'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import toast from 'react-hot-toast'
import { AlertTriangle, Bot, CheckCircle2, Copy, DatabaseZap, RefreshCw } from 'lucide-react'

import AppLayout from '@/components/layout/AppLayout'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useAuthContext } from '@/contexts/AuthContext'
import { usePermission } from '@/hooks/usePermission'
import { datahubService } from '@/service/datahubService'
import type { DailyBriefContextInfo, DailyBriefReadinessInfo } from '@/types/datahub'

function statusText(status?: string): string {
  const map: Record<string, string> = {
    ready: '就绪',
    partial: '部分可用',
    worker_offline: 'Worker 离线',
    empty_watchlist: '自选股为空',
    missing: '缺数据',
  }
  return status ? map[status] ?? status : '未知'
}

function formatPct(value?: number | null): string {
  if (value === null || value === undefined) return '-'
  return `${value > 0 ? '+' : ''}${value.toFixed(2)}%`
}

export default function DatahubDailyBriefPage() {
  const { user } = useAuthContext()
  const { isAdmin } = usePermission()
  const router = useRouter()

  const [loading, setLoading] = useState(true)
  const [preparing, setPreparing] = useState(false)
  const [exporting, setExporting] = useState(false)
  const [readiness, setReadiness] = useState<DailyBriefReadinessInfo | null>(null)
  const [context, setContext] = useState<DailyBriefContextInfo | null>(null)

  useEffect(() => {
    if (user && !isAdmin) router.push('/unauthorized')
  }, [user, isAdmin, router])

  const loadDailyBrief = async () => {
    setLoading(true)
    try {
      const [nextReadiness, nextContext] = await Promise.all([
        datahubService.getDailyBriefReadiness(),
        datahubService.getDailyBriefToday(),
      ])
      setReadiness(nextReadiness)
      setContext(nextContext)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadDailyBrief()
  }, [])

  const prepareTodayData = async () => {
    setPreparing(true)
    try {
      const result = await datahubService.prepareDailyBrief(7)
      toast.success(result.message)
      await loadDailyBrief()
    } finally {
      setPreparing(false)
    }
  }

  const exportForOpencode = async () => {
    setExporting(true)
    try {
      const payload = await datahubService.getOpencodeContext()
      await navigator.clipboard.writeText(JSON.stringify(payload, null, 2))
      toast.success('已复制 opencode 上下文 JSON')
    } finally {
      setExporting(false)
    }
  }

  const isReady = readiness?.status === 'ready'

  return (
    <AppLayout requiredRole={user?.currentRole}>
      <div className="am-page">
        <div className="am-container space-y-6">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div>
              <h1 className="am-page-title">每日看盘</h1>
              <p className="text-sm text-gray-500">
                聚合自选股、板块、数据质量与 AI/opencode 分析上下文。
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button className="am-btn-reset" onClick={loadDailyBrief} disabled={loading}>
                <RefreshCw className="mr-1 h-4 w-4" />
                刷新
              </Button>
              <Button className="am-btn-outline" onClick={prepareTodayData} disabled={preparing}>
                <DatabaseZap className="mr-1 h-4 w-4" />
                {preparing ? '提交中...' : '更新今日数据'}
              </Button>
              <Button className="am-btn-primary" onClick={exportForOpencode} disabled={exporting}>
                <Copy className="mr-1 h-4 w-4" />
                {exporting ? '导出中...' : '导出给 opencode'}
              </Button>
            </div>
          </div>

          <Card className="am-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                {isReady ? <CheckCircle2 className="h-5 w-5 text-green-600" /> : <AlertTriangle className="h-5 w-5 text-yellow-600" />}
                今日数据状态：{statusText(readiness?.status)}
              </CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-1 gap-3 md:grid-cols-4">
              <div className="rounded-lg bg-gray-50 p-3">
                <div className="text-xs text-gray-500">最新交易日</div>
                <div className="mt-1 font-medium text-gray-900">{readiness?.latest_trade_date ?? '-'}</div>
              </div>
              <div className="rounded-lg bg-gray-50 p-3">
                <div className="text-xs text-gray-500">自选股数量</div>
                <div className="mt-1 font-medium text-gray-900">{readiness?.watchlist_count ?? 0}</div>
              </div>
              <div className="rounded-lg bg-gray-50 p-3">
                <div className="text-xs text-gray-500">缺失标的</div>
                <div className="mt-1 font-medium text-gray-900">{readiness?.missing_count ?? 0}</div>
              </div>
              <div className="rounded-lg bg-gray-50 p-3">
                <div className="text-xs text-gray-500">Worker</div>
                <div className="mt-1 font-medium text-gray-900">{readiness?.worker_online ? '在线' : '离线/未知'}</div>
              </div>
              {readiness?.warnings?.length ? (
                <div className="md:col-span-4 rounded-lg border border-yellow-200 bg-yellow-50 p-3 text-sm text-yellow-800">
                  {readiness.warnings.join('；')}
                </div>
              ) : null}
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
            <Card className="am-card lg:col-span-2">
              <CardHeader>
                <CardTitle className="text-base">自选股观察</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[760px] text-sm">
                    <thead className="bg-gray-50 text-left text-gray-600">
                      <tr>
                        <th className="px-3 py-2">标的</th>
                        <th className="px-3 py-2">板块</th>
                        <th className="px-3 py-2">交易日</th>
                        <th className="px-3 py-2">收盘</th>
                        <th className="px-3 py-2">涨跌</th>
                        <th className="px-3 py-2">板块涨跌</th>
                        <th className="px-3 py-2">状态</th>
                      </tr>
                    </thead>
                    <tbody>
                      {context?.watchlist.map((item) => (
                        <tr key={item.symbol} className="border-t border-gray-100">
                          <td className="px-3 py-2 font-medium text-gray-900">
                            {item.name || item.symbol}
                            <div className="text-xs text-gray-500">{item.symbol}</div>
                          </td>
                          <td className="px-3 py-2">{item.sector_name || '-'}</td>
                          <td className="px-3 py-2">{item.trade_date || '-'}</td>
                          <td className="px-3 py-2">{item.close ?? '-'}</td>
                          <td className={`px-3 py-2 ${item.change_pct && item.change_pct > 0 ? 'text-red-600' : 'text-green-600'}`}>
                            {formatPct(item.change_pct)}
                          </td>
                          <td className="px-3 py-2">{formatPct(item.sector_change_pct)}</td>
                          <td className="px-3 py-2">{item.data_status}</td>
                        </tr>
                      ))}
                      {!loading && (!context?.watchlist || context.watchlist.length === 0) && (
                        <tr>
                          <td className="px-3 py-8 text-center text-gray-500" colSpan={7}>
                            暂无自选股数据，请先维护自选股或更新数据。
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>

            <div className="space-y-4">
              <Card className="am-card">
                <CardHeader>
                  <CardTitle className="text-base">相关板块</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {context?.related_sectors.map((sector) => (
                    <div key={sector.sector_name} className="rounded-lg bg-gray-50 p-3">
                      <div className="font-medium text-gray-900">{sector.sector_name}</div>
                      <div className="mt-1 text-xs text-gray-500">
                        自选 {sector.stock_count} 只，板块 {formatPct(sector.sector_change_pct)}，自选均值 {formatPct(sector.avg_stock_change_pct)}
                      </div>
                    </div>
                  ))}
                  {!context?.related_sectors.length && <div className="text-sm text-gray-500">暂无板块聚合数据。</div>}
                </CardContent>
              </Card>

              <Card className="am-card">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Bot className="h-4 w-4" />
                    AI 风险提示
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {context?.risk_flags.map((flag, idx) => (
                    <div key={`${flag.source}-${flag.symbol || idx}`} className="rounded-lg border border-yellow-200 bg-yellow-50 p-3 text-sm text-yellow-800">
                      {flag.message}
                    </div>
                  ))}
                  {!context?.risk_flags.length && <div className="text-sm text-gray-500">暂无风险提示。</div>}
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </div>
    </AppLayout>
  )
}
