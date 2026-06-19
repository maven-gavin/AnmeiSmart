'use client'

import { useEffect, useMemo, useState } from 'react'
import { useRouter } from 'next/navigation'
import toast from 'react-hot-toast'
import type { CheckedState } from '@radix-ui/react-checkbox'
import { ClipboardList, RefreshCw, Play, Database, Search, RotateCcw, ChevronDown } from 'lucide-react'

import AppLayout from '@/components/layout/AppLayout'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { Checkbox } from '@/components/ui/checkbox'
import { useAuthContext } from '@/contexts/AuthContext'
import { usePermission } from '@/hooks/usePermission'
import { datahubService } from '@/service/datahubService'
import { formatDatasetLabel } from '@/lib/datahub/datasetLabels'
import type {
  FillMarketDailyMissingResult,
  MarketDailyMissingScanResult,
  DatahubDatasetInfo,
} from '@/types/datahub'

const ALL_DATASETS_VALUE = '__ALL__'
const SUPPORTED_TRIGGER_DATASETS = new Set([
  'market_daily',
  'security_master',
  'trading_calendar',
  'money_flow',
  'sector_members',
  'financial_summary',
])

export default function DatahubAcquisitionPage() {
  const { user } = useAuthContext()
  const { isAdmin } = usePermission()
  const router = useRouter()

  const [seeding, setSeeding] = useState(false)
  const [runningBackfill, setRunningBackfill] = useState(false)
  const [runningDaily, setRunningDaily] = useState(false)
  const [datasetCatalog, setDatasetCatalog] = useState<DatahubDatasetInfo[]>([])
  const [datasetOptions, setDatasetOptions] = useState<string[]>([])

  const [missingForm, setMissingForm] = useState({
    start_date: '2024-01-01',
    end_date: '2024-01-31',
    reference_date: '',
    limit: 500,
    batch_size: 200,
  })
  const [missingLoading, setMissingLoading] = useState(false)
  const [fillingMissing, setFillingMissing] = useState(false)
  const [missingReport, setMissingReport] = useState<MarketDailyMissingScanResult | null>(null)
  const [fillResult, setFillResult] = useState<FillMarketDailyMissingResult | null>(null)

  const [backfillForm, setBackfillForm] = useState({
    datasets: [ALL_DATASETS_VALUE],
    symbol: '',
    start_date: '2024-01-01',
    end_date: '2024-01-31',
  })
  const [dailyForm, setDailyForm] = useState({
    datasets: [ALL_DATASETS_VALUE],
    symbol: '',
    window_days: 7,
  })

  useEffect(() => {
    if (user && !isAdmin) router.push('/unauthorized')
  }, [user, isAdmin, router])

  const loadDatasets = async () => {
    const datasets = await datahubService.listDatasets()
    setDatasetCatalog(datasets)
    setDatasetOptions(datasets.map((item) => item.dataset_key))
  }

  useEffect(() => {
    loadDatasets()
  }, [])

  const datasetLabelMap = useMemo(() => {
    const map: Record<string, string | null | undefined> = {}
    datasetCatalog.forEach((item) => {
      map[item.dataset_key] = item.label_zh
    })
    return map
  }, [datasetCatalog])

  const supportedDatasetOptions = useMemo(
    () => datasetOptions.filter((item) => SUPPORTED_TRIGGER_DATASETS.has(item)),
    [datasetOptions],
  )

  const resolveSelectedDatasets = (selectedValues: string[]) => {
    if (selectedValues.includes(ALL_DATASETS_VALUE)) return supportedDatasetOptions
    return selectedValues.filter((item) => SUPPORTED_TRIGGER_DATASETS.has(item))
  }

  const toggleDatasets = (selectedValues: string[], changedValue: string, checked: boolean) => {
    if (changedValue === ALL_DATASETS_VALUE) return checked ? [ALL_DATASETS_VALUE] : []
    const next = checked
      ? [...selectedValues.filter((item) => item !== ALL_DATASETS_VALUE), changedValue]
      : selectedValues.filter((item) => item !== changedValue && item !== ALL_DATASETS_VALUE)
    return Array.from(new Set(next))
  }

  const onDatasetCheckedChange = (
    currentValues: string[],
    setter: (nextValues: string[]) => void,
    changedValue: string,
    checkedState: CheckedState,
  ) => {
    setter(toggleDatasets(currentValues, changedValue, checkedState === true))
  }

  const getDatasetTriggerText = (selectedValues: string[]) => {
    if (datasetOptions.length === 0) return '暂无数据集，请先初始化'
    if (selectedValues.includes(ALL_DATASETS_VALUE)) {
      return supportedDatasetOptions.length > 0 ? `全部可执行数据集 (${supportedDatasetOptions.length})` : '暂无可执行数据集'
    }
    if (selectedValues.length === 0) return '请选择数据集'
    return selectedValues.map((key) => formatDatasetLabel(key, datasetLabelMap[key])).join(', ')
  }

  const seedDatasets = async () => {
    setSeeding(true)
    try {
      const created = await datahubService.seedDatasets()
      toast.success(`初始化完成，新增 ${created} 个数据集`)
      await loadDatasets()
    } finally {
      setSeeding(false)
    }
  }

  const runBackfill = async () => {
    const selectedDatasets = resolveSelectedDatasets(backfillForm.datasets)
    if (selectedDatasets.length === 0) {
      toast.error('请选择已支持的数据集')
      return
    }
    setRunningBackfill(true)
    try {
      for (const dataset of selectedDatasets) {
        await datahubService.runBackfill({
          dataset,
          symbol: backfillForm.symbol.trim() || undefined,
          start_date: backfillForm.start_date,
          end_date: backfillForm.end_date,
        })
      }
      toast.success(`回填已提交：${selectedDatasets.length} 个任务`)
    } finally {
      setRunningBackfill(false)
    }
  }

  const runDailyIncremental = async () => {
    const selectedDatasets = resolveSelectedDatasets(dailyForm.datasets)
    if (selectedDatasets.length === 0) {
      toast.error('请选择已支持的数据集')
      return
    }
    setRunningDaily(true)
    try {
      for (const dataset of selectedDatasets) {
        await datahubService.runDailyIncremental({
          dataset,
          symbol: dailyForm.symbol.trim() || undefined,
          window_days: Number(dailyForm.window_days || 7),
        })
      }
      toast.success(`增量已提交：${selectedDatasets.length} 个任务`)
    } finally {
      setRunningDaily(false)
    }
  }

  const scanMissing = async () => {
    setMissingLoading(true)
    setFillResult(null)
    try {
      const report = await datahubService.scanMarketDailyMissing({
        start_date: missingForm.start_date,
        end_date: missingForm.end_date,
        reference_date: missingForm.reference_date || undefined,
        limit: missingForm.limit,
      })
      setMissingReport(report)
    } finally {
      setMissingLoading(false)
    }
  }

  const fillMissing = async () => {
    setFillingMissing(true)
    try {
      const result = await datahubService.fillMarketDailyMissing({
        start_date: missingForm.start_date,
        end_date: missingForm.end_date,
        reference_date: missingForm.reference_date || undefined,
        max_symbols: missingForm.limit,
        batch_size: missingForm.batch_size,
      })
      setFillResult(result)
      toast.success(`已提交补齐：${result.filled_symbols} 个 symbol`)
    } finally {
      setFillingMissing(false)
    }
  }

  const renderDatasetPicker = (
    selectedValues: string[],
    setter: (next: string[]) => void,
  ) => (
    <Popover>
      <PopoverTrigger asChild>
        <button type="button" className="am-field mt-1 flex w-full items-center justify-between">
          <span className="truncate text-left">{getDatasetTriggerText(selectedValues)}</span>
          <ChevronDown className="h-4 w-4 text-gray-500" />
        </button>
      </PopoverTrigger>
      <PopoverContent align="start" className="z-[80] w-[320px] border-gray-200 bg-white p-3 shadow-lg">
        <div className="space-y-2">
          <label className="flex cursor-pointer items-center gap-2 rounded-sm px-1.5 py-1 text-sm hover:bg-gray-50">
            <Checkbox
              disabled={datasetOptions.length === 0}
              checked={selectedValues.includes(ALL_DATASETS_VALUE)}
              onCheckedChange={(checked) => onDatasetCheckedChange(selectedValues, setter, ALL_DATASETS_VALUE, checked)}
            />
            全部可执行数据集
          </label>
          <div className="max-h-48 space-y-1 overflow-auto pr-1">
            {datasetOptions.map((dataset) => {
              const isSupported = SUPPORTED_TRIGGER_DATASETS.has(dataset)
              return (
                <label
                  key={dataset}
                  className={`flex items-center gap-2 rounded-sm px-1.5 py-1 text-sm ${isSupported ? 'cursor-pointer hover:bg-gray-50' : 'cursor-not-allowed text-gray-400'}`}
                >
                  <Checkbox
                    disabled={!isSupported}
                    checked={selectedValues.includes(ALL_DATASETS_VALUE) || selectedValues.includes(dataset)}
                    onCheckedChange={(checked) => onDatasetCheckedChange(selectedValues, setter, dataset, checked)}
                  />
                  {formatDatasetLabel(dataset, datasetLabelMap[dataset])}
                </label>
              )
            })}
          </div>
        </div>
      </PopoverContent>
    </Popover>
  )

  return (
    <AppLayout requiredRole={user?.currentRole}>
      <div className="am-page">
        <div className="am-container space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="am-page-title">数据获取</h1>
              <p className="text-sm text-gray-500">触发回填、增量与缺失补齐任务。任务进度请到「运行监控」查看。</p>
            </div>
            <div className="flex gap-2">
              <Button className="am-btn-outline" onClick={seedDatasets} disabled={seeding}>
                <Database className="mr-1 h-4 w-4" />
                {seeding ? '初始化中...' : '初始化数据集'}
              </Button>
              <Button className="am-btn-reset" onClick={loadDatasets}>
                <RefreshCw className="mr-1 h-4 w-4" />
                刷新
              </Button>
            </div>
          </div>

          <Card className="am-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-sm">
                <Search className="h-4 w-4" />
                缺失巡检与补齐（日线行情）
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid grid-cols-1 gap-3 md:grid-cols-5">
                <div>
                  <Label>开始日期</Label>
                  <Input type="date" className="am-field mt-1" value={missingForm.start_date} onChange={(e) => setMissingForm((p) => ({ ...p, start_date: e.target.value }))} />
                </div>
                <div>
                  <Label>结束日期</Label>
                  <Input type="date" className="am-field mt-1" value={missingForm.end_date} onChange={(e) => setMissingForm((p) => ({ ...p, end_date: e.target.value }))} />
                </div>
                <div>
                  <Label>参考日期</Label>
                  <Input type="date" className="am-field mt-1" value={missingForm.reference_date} onChange={(e) => setMissingForm((p) => ({ ...p, reference_date: e.target.value }))} />
                </div>
                <div>
                  <Label>最多补齐</Label>
                  <Input type="number" min={1} max={5000} className="am-field mt-1" value={missingForm.limit} onChange={(e) => setMissingForm((p) => ({ ...p, limit: Number(e.target.value || 500) }))} />
                </div>
                <div>
                  <Label>每批数量</Label>
                  <Input type="number" min={1} max={1000} className="am-field mt-1" value={missingForm.batch_size} onChange={(e) => setMissingForm((p) => ({ ...p, batch_size: Number(e.target.value || 200) }))} />
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                <Button className="am-btn-outline" onClick={scanMissing} disabled={missingLoading}>
                  <ClipboardList className="mr-1 h-4 w-4" />
                  {missingLoading ? '扫描中...' : '扫描缺失'}
                </Button>
                <Button className="am-btn-primary" onClick={fillMissing} disabled={fillingMissing || !missingReport || missingReport.missing_count === 0}>
                  <RotateCcw className="mr-1 h-4 w-4" />
                  {fillingMissing ? '提交中...' : '补齐缺失'}
                </Button>
              </div>
              {missingReport && (
                <div className="rounded border border-gray-200 bg-gray-50 p-3 text-sm text-gray-700">
                  预期 {missingReport.expected_count}，已存在 {missingReport.existing_count}，缺失 {missingReport.missing_count}
                </div>
              )}
              {fillResult && (
                <div className="rounded border border-green-200 bg-green-50 p-3 text-sm text-green-700">
                  已创建 {fillResult.created_runs} 个补齐 run，共 {fillResult.filled_symbols} 个 symbol
                </div>
              )}
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <Card className="am-card">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-sm"><Play className="h-4 w-4" />历史回填</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                  <div>
                    <Label>数据集</Label>
                    {renderDatasetPicker(backfillForm.datasets, (next) => setBackfillForm((p) => ({ ...p, datasets: next })))}
                  </div>
                  <div>
                    <Label>证券代码（可选）</Label>
                    <Input className="am-field mt-1" value={backfillForm.symbol} onChange={(e) => setBackfillForm((p) => ({ ...p, symbol: e.target.value }))} placeholder="不填则处理全部标的" />
                  </div>
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
                  {runningBackfill ? '执行中...' : '立即执行回填'}
                </Button>
              </CardContent>
            </Card>

            <Card className="am-card">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-sm"><RefreshCw className="h-4 w-4" />每日增量</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                  <div>
                    <Label>数据集</Label>
                    {renderDatasetPicker(dailyForm.datasets, (next) => setDailyForm((p) => ({ ...p, datasets: next })))}
                  </div>
                  <div>
                    <Label>证券代码（可选）</Label>
                    <Input className="am-field mt-1" value={dailyForm.symbol} onChange={(e) => setDailyForm((p) => ({ ...p, symbol: e.target.value }))} placeholder="不填则处理全部标的" />
                  </div>
                </div>
                <div>
                  <Label>回溯窗口（天）</Label>
                  <Input type="number" min={1} max={30} className="am-field mt-1" value={dailyForm.window_days} onChange={(e) => setDailyForm((p) => ({ ...p, window_days: Number(e.target.value || 7) }))} />
                </div>
                <Button className="am-btn-primary w-full" onClick={runDailyIncremental} disabled={runningDaily}>
                  {runningDaily ? '执行中...' : '立即执行增量'}
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </AppLayout>
  )
}
