'use client'

import { useCallback, useEffect, useState } from 'react'
import Link from 'next/link'
import toast from 'react-hot-toast'
import { Plus, RefreshCw, Trash2 } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { datahubService } from '@/service/datahubService'
import type { MarketDailyBarInfo, WatchlistBoardRow } from '@/types/datahub'

function formatPrice(value?: number | null) {
  if (value == null) return '-'
  return value.toFixed(2)
}

function formatPct(value?: number | null) {
  if (value == null) return '-'
  const prefix = value > 0 ? '+' : ''
  return `${prefix}${value.toFixed(2)}%`
}

function priceColor(value?: number | null) {
  if (value == null || value === 0) return 'text-gray-700'
  return value > 0 ? 'text-red-600' : 'text-green-600'
}

export function WatchlistBoard() {
  const [rows, setRows] = useState<WatchlistBoardRow[]>([])
  const [loading, setLoading] = useState(true)
  const [adding, setAdding] = useState(false)
  const [newSymbol, setNewSymbol] = useState('')
  const [newName, setNewName] = useState('')
  const [detailSymbol, setDetailSymbol] = useState<string | null>(null)
  const [detailBars, setDetailBars] = useState<MarketDailyBarInfo[]>([])
  const [detailLoading, setDetailLoading] = useState(false)
  const [detailDays, setDetailDays] = useState(30)

  const loadBoard = useCallback(async () => {
    setLoading(true)
    try {
      const board = await datahubService.getWatchlistBoard(30)
      setRows(board.rows)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadBoard()
  }, [loadBoard])

  const handleAdd = async () => {
    const symbol = newSymbol.trim()
    if (!symbol) {
      toast.error('请输入证券代码')
      return
    }
    setAdding(true)
    try {
      await datahubService.addWatchlistItem({ symbol, name: newName.trim() || undefined })
      toast.success('已添加')
      setNewSymbol('')
      setNewName('')
      await loadBoard()
    } finally {
      setAdding(false)
    }
  }

  const handleDelete = async (row: WatchlistBoardRow) => {
    await datahubService.deleteWatchlistItem(row.id)
    toast.success(`已删除 ${row.symbol}`)
    if (detailSymbol === row.symbol) setDetailSymbol(null)
    await loadBoard()
  }

  const openDetail = async (symbol: string) => {
    setDetailSymbol(symbol)
    setDetailLoading(true)
    try {
      const end = new Date()
      const start = new Date()
      start.setDate(end.getDate() - detailDays + 1)
      const bars = await datahubService.getMarketDailyBars({
        symbol,
        start_date: start.toISOString().slice(0, 10),
        end_date: end.toISOString().slice(0, 10),
      })
      setDetailBars(bars)
    } finally {
      setDetailLoading(false)
    }
  }

  return (
    <>
      <Card className="am-card">
        <CardContent className="space-y-4 pt-6">
          <div className="flex flex-wrap items-end gap-3">
            <div className="min-w-[200px] flex-1">
              <Label>证券代码</Label>
              <Input
                className="am-field mt-1"
                placeholder="如 002472 或 002472.SZ"
                value={newSymbol}
                onChange={(e) => setNewSymbol(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleAdd()}
              />
            </div>
            <div className="min-w-[160px] flex-1">
              <Label>名称（可选）</Label>
              <Input className="am-field mt-1" placeholder="自动从主数据获取" value={newName} onChange={(e) => setNewName(e.target.value)} />
            </div>
            <div className="flex gap-2">
              <Button className="am-btn-primary" onClick={handleAdd} disabled={adding}>
                <Plus className="mr-1 h-4 w-4" />
                添加
              </Button>
              <Button className="am-btn-reset" onClick={loadBoard} disabled={loading}>
                <RefreshCw className="mr-1 h-4 w-4" />
                刷新
              </Button>
            </div>
          </div>

          <p className="text-xs text-gray-500">
            数据来自 DataHub 标准层（T+1）。名称来自证券主数据，板块来自板块成分快照；板块涨幅为成分股均值估算。若无数据，请前往
            <Link href="/admin/datahub" className="mx-1 text-brand-primaryHover hover:underline">数据获取</Link>
            执行回填或增量。
          </p>

          {loading ? (
            <div className="flex justify-center py-12">
              <div className="am-spinner h-8 w-8" />
            </div>
          ) : rows.length === 0 ? (
            <div className="rounded border border-dashed border-gray-200 bg-gray-50 p-8 text-center text-sm text-gray-500">
              暂无自选股，添加后即可查看日线行情
            </div>
          ) : (
            <div className="overflow-x-auto rounded-lg border border-gray-200">
              <table className="min-w-[1100px] w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-3 py-2 text-left font-medium text-gray-700">代码</th>
                    <th className="px-3 py-2 text-left font-medium text-gray-700">名称</th>
                    <th className="px-3 py-2 text-left font-medium text-gray-700">所属板块</th>
                    <th className="px-3 py-2 text-right font-medium text-gray-700">开</th>
                    <th className="px-3 py-2 text-right font-medium text-gray-700">高</th>
                    <th className="px-3 py-2 text-right font-medium text-gray-700">低</th>
                    <th className="px-3 py-2 text-right font-medium text-gray-700">收</th>
                    <th className="px-3 py-2 text-right font-medium text-gray-700">涨跌</th>
                    <th className="px-3 py-2 text-right font-medium text-gray-700">涨幅</th>
                    <th className="px-3 py-2 text-right font-medium text-gray-700">板块涨幅</th>
                    <th className="px-3 py-2 text-right font-medium text-gray-700">成交量</th>
                    <th className="px-3 py-2 text-left font-medium text-gray-700">日期</th>
                    <th className="px-3 py-2 text-right font-medium text-gray-700">操作</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row) => (
                    <tr key={row.id} className="border-t border-gray-100 hover:bg-gray-50">
                      <td className="px-3 py-2 font-mono text-gray-900">{row.symbol}</td>
                      <td className="px-3 py-2 text-gray-700">{row.name || '-'}</td>
                      <td className="px-3 py-2 text-gray-600">{row.sector_name || '-'}</td>
                      <td className={`px-3 py-2 text-right ${priceColor(row.change_pct)}`}>
                        {row.has_data ? formatPrice(row.open) : '-'}
                      </td>
                      <td className={`px-3 py-2 text-right ${priceColor(row.change_pct)}`}>
                        {row.has_data ? formatPrice(row.high) : '-'}
                      </td>
                      <td className={`px-3 py-2 text-right ${priceColor(row.change_pct)}`}>
                        {row.has_data ? formatPrice(row.low) : '-'}
                      </td>
                      <td className={`px-3 py-2 text-right font-medium ${priceColor(row.change_pct)}`}>
                        {row.has_data ? formatPrice(row.close) : <span className="text-gray-400">无数据</span>}
                      </td>
                      <td className={`px-3 py-2 text-right ${priceColor(row.change_amount)}`}>{formatPrice(row.change_amount)}</td>
                      <td className={`px-3 py-2 text-right ${priceColor(row.change_pct)}`}>{formatPct(row.change_pct)}</td>
                      <td className={`px-3 py-2 text-right ${priceColor(row.sector_change_pct)}`}>{formatPct(row.sector_change_pct)}</td>
                      <td className="px-3 py-2 text-right text-gray-600">{row.volume != null ? Math.round(row.volume).toLocaleString() : '-'}</td>
                      <td className="px-3 py-2 text-gray-500">{row.trade_date || '-'}</td>
                      <td className="px-3 py-2">
                        <div className="flex justify-end gap-1">
                          <Button size="sm" variant="outline" className="am-btn-outline h-8 px-2 text-xs" onClick={() => openDetail(row.symbol)}>
                            明细
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            className="h-8 border-red-300 px-2 text-red-600 hover:bg-red-50"
                            onClick={() => handleDelete(row)}
                          >
                            <Trash2 className="h-3 w-3" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      <Dialog open={detailSymbol != null} onOpenChange={(open) => !open && setDetailSymbol(null)}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>{detailSymbol} 日线明细</DialogTitle>
          </DialogHeader>
          {detailLoading ? (
            <div className="py-8 text-center text-sm text-gray-500">加载中...</div>
          ) : detailBars.length === 0 ? (
            <div className="py-8 text-center text-sm text-gray-500">暂无日线数据</div>
          ) : (
            <div className="max-h-[60vh] overflow-auto rounded border border-gray-200">
              <table className="w-full text-xs">
                <thead className="sticky top-0 bg-gray-50">
                  <tr>
                    <th className="px-2 py-1 text-left">日期</th>
                    <th className="px-2 py-1 text-right">开</th>
                    <th className="px-2 py-1 text-right">高</th>
                    <th className="px-2 py-1 text-right">低</th>
                    <th className="px-2 py-1 text-right">收</th>
                    <th className="px-2 py-1 text-right">量</th>
                    <th className="px-2 py-1 text-right">换手%</th>
                  </tr>
                </thead>
                <tbody>
                  {[...detailBars].reverse().map((bar) => (
                    <tr key={bar.trade_date} className="border-t border-gray-100">
                      <td className="px-2 py-1">{bar.trade_date}</td>
                      <td className="px-2 py-1 text-right">{bar.open.toFixed(2)}</td>
                      <td className="px-2 py-1 text-right">{bar.high.toFixed(2)}</td>
                      <td className="px-2 py-1 text-right">{bar.low.toFixed(2)}</td>
                      <td className="px-2 py-1 text-right font-medium">{bar.close.toFixed(2)}</td>
                      <td className="px-2 py-1 text-right">{Math.round(bar.volume).toLocaleString()}</td>
                      <td className="px-2 py-1 text-right">{bar.turnover_rate?.toFixed(2) ?? '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </>
  )
}
