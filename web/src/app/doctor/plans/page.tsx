'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { doctorService } from '@/service/doctorService';
import { TreatmentPlan } from '@/types/doctor';

// 状态标签组件
function StatusBadge({ status }: { status: TreatmentPlan['status'] }) {
  const statusConfig = {
    draft: { bg: 'bg-gray-100', text: 'text-gray-800', label: '草稿' },
    pending: { bg: 'bg-yellow-100', text: 'text-yellow-800', label: '待审核' },
    approved: { bg: 'bg-green-100', text: 'text-green-800', label: '已批准' },
    completed: { bg: 'bg-blue-100', text: 'text-blue-800', label: '已完成' },
    cancelled: { bg: 'bg-red-100', text: 'text-red-800', label: '已取消' },
  };
  
  const config = statusConfig[status];
  
  return (
    <span className={`rounded-full px-2 py-1 text-xs ${config.bg} ${config.text}`}>
      {config.label}
    </span>
  );
}

export default function TreatmentPlansPage() {
  const [loading, setLoading] = useState(true);
  const [plans, setPlans] = useState<TreatmentPlan[]>([]);
  
  useEffect(() => {
    const loadPlans = async () => {
      try {
        const data = await doctorService.getTreatmentPlans();
        setPlans(data);
      } catch (error) {
        console.error('加载治疗方案失败', error);
      } finally {
        setLoading(false);
      }
    };
    
    loadPlans();
  }, []);
  
  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="h-12 w-12 animate-spin rounded-full border-4 border-orange-500 border-t-transparent"></div>
      </div>
    );
  }
  
  return (
    <div className="p-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">治疗方案</h1>
          <p className="text-gray-600">查看和管理患者治疗方案</p>
        </div>
        <Link 
          href="/doctor/plans/create" 
          className="rounded-md bg-orange-500 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-orange-600"
        >
          创建新方案
        </Link>
      </div>
      
      <div className="overflow-hidden rounded-lg border border-gray-200 bg-white">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  患者信息
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  诊断
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  创建日期
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  状态
                </th>
                <th scope="col" className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">
                  操作
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {plans.length > 0 ? (
                plans.map((plan) => (
                  <tr key={plan.id} className="hover:bg-gray-50">
                    <td className="whitespace-nowrap px-6 py-4">
                      <div className="flex items-center">
                        <div className="h-10 w-10 flex-shrink-0">
                          <img 
                            className="h-10 w-10 rounded-full"
                            src={`/avatars/user${plan.patientId === '101' ? '1' : plan.patientId === '102' ? '2' : '3'}.png`}
                            alt={plan.patientName}
                          />
                        </div>
                        <div className="ml-4">
                          <div className="text-sm font-medium text-gray-900">{plan.patientName}</div>
                          <div className="text-sm text-gray-500">患者ID: {plan.patientId}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-900 line-clamp-2">{plan.diagnosis}</div>
                    </td>
                    <td className="whitespace-nowrap px-6 py-4">
                      <div className="text-sm text-gray-900">
                        {new Date(plan.createdAt).toLocaleDateString('zh-CN')}
                      </div>
                    </td>
                    <td className="whitespace-nowrap px-6 py-4">
                      <StatusBadge status={plan.status} />
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-right text-sm font-medium">
                      <Link 
                        href={`/doctor/plans/${plan.id}`}
                        className="text-orange-600 hover:text-orange-900 mr-4"
                      >
                        查看
                      </Link>
                      <Link 
                        href={`/doctor/plans/${plan.id}/edit`}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        编辑
                      </Link>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5} className="px-6 py-4 text-center text-sm text-gray-500">
                    暂无治疗方案数据
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
} 