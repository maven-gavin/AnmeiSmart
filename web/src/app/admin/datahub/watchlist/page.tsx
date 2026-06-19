'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import AppLayout from '@/components/layout/AppLayout'
import { WatchlistBoard } from '@/components/admin/datahub/WatchlistBoard'
import { useAuthContext } from '@/contexts/AuthContext'
import { usePermission } from '@/hooks/usePermission'

export default function DatahubWatchlistPage() {
  const { user } = useAuthContext()
  const { isAdmin } = usePermission()
  const router = useRouter()

  useEffect(() => {
    if (user && !isAdmin) router.push('/unauthorized')
  }, [user, isAdmin, router])

  return (
    <AppLayout requiredRole={user?.currentRole}>
      <div className="am-page">
        <div className="am-container space-y-6">
          <div>
            <h1 className="am-page-title">自选股</h1>
            <p className="text-sm text-gray-500">查看自选列表的最新日线行情（DataHub 标准数据）</p>
          </div>
          <WatchlistBoard />
        </div>
      </div>
    </AppLayout>
  )
}
