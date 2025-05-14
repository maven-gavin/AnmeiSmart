'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
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

export default function TreatmentPlanDetailPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [plan, setPlan] = useState<TreatmentPlan | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    const loadPlan = async () => {
      try {
        setLoading(true);
        const data = await doctorService.getTreatmentPlanById(params.id);
        
        if (!data) {
          setError('未找到治疗方案');
          return;
        }
        
        setPlan(data);
      } catch (err) {
        console.error('加载治疗方案失败', err);
        setError('加载治疗方案失败');
      } finally {
        setLoading(false);
      }
    };
    
    loadPlan();
  }, [params.id]);
  
  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="h-12 w-12 animate-spin rounded-full border-4 border-orange-500 border-t-transparent"></div>
      </div>
    );
  }
  
  if (error || !plan) {
    return (
      <div className="flex h-full flex-col items-center justify-center p-6">
        <div className="rounded-lg bg-red-50 p-4 text-red-800">
          <h3 className="text-lg font-medium">{error || '未找到治疗方案'}</h3>
          <p className="mt-2">请返回方案列表重试</p>
        </div>
        <button
          onClick={() => router.push('/doctor/plans')}
          className="mt-4 rounded-md bg-orange-500 px-4 py-2 text-white hover:bg-orange-600"
        >
          返回方案列表
        </button>
      </div>
    );
  }
  
  return (
    <div className="p-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">治疗方案详情</h1>
          <p className="text-gray-600">查看患者治疗方案的详细信息</p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={() => router.push(`/doctor/plans/${plan.id}/edit`)}
            className="rounded-md bg-white px-4 py-2 text-sm font-medium text-orange-600 shadow-sm ring-1 ring-orange-600 hover:bg-orange-50"
          >
            编辑方案
          </button>
          <button
            onClick={() => router.push('/doctor/plans')}
            className="rounded-md bg-white px-4 py-2 text-sm font-medium text-gray-600 shadow-sm ring-1 ring-gray-300 hover:bg-gray-50"
          >
            返回列表
          </button>
        </div>
      </div>
      
      <div className="space-y-6">
        {/* 基本信息卡片 */}
        <div className="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
          <div className="border-b border-gray-200 bg-gray-50 px-6 py-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-medium text-gray-800">基本信息</h2>
              <StatusBadge status={plan.status} />
            </div>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
              <div>
                <h3 className="mb-2 text-sm font-medium text-gray-500">患者信息</h3>
                <div className="flex items-center">
                  <img 
                    src={`/avatars/user${plan.patientId === '101' ? '1' : plan.patientId === '102' ? '2' : '3'}.png`}
                    alt={plan.patientName}
                    className="h-12 w-12 rounded-full"
                  />
                  <div className="ml-3">
                    <p className="font-medium">{plan.patientName}</p>
                    <p className="text-sm text-gray-500">患者ID: {plan.patientId}</p>
                  </div>
                </div>
              </div>
              
              <div>
                <h3 className="mb-2 text-sm font-medium text-gray-500">创建信息</h3>
                <p className="font-medium">{plan.doctorName}</p>
                <p className="text-sm text-gray-500">
                  创建于 {new Date(plan.createdAt).toLocaleDateString('zh-CN')}
                </p>
                {plan.followUpDate && (
                  <p className="mt-2 text-sm text-gray-800">
                    随访日期: {new Date(plan.followUpDate).toLocaleDateString('zh-CN')}
                  </p>
                )}
              </div>
            </div>
            
            <div className="mt-6">
              <h3 className="mb-2 text-sm font-medium text-gray-500">诊断</h3>
              <p className="rounded-md bg-gray-50 p-3 text-gray-800">{plan.diagnosis}</p>
            </div>
            
            {plan.notes && (
              <div className="mt-6">
                <h3 className="mb-2 text-sm font-medium text-gray-500">备注</h3>
                <p className="rounded-md bg-gray-50 p-3 text-gray-800">{plan.notes}</p>
              </div>
            )}
          </div>
        </div>
        
        {/* 药物卡片 */}
        <div className="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
          <div className="border-b border-gray-200 bg-gray-50 px-6 py-4">
            <h2 className="text-lg font-medium text-gray-800">处方药物</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                    药物名称
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                    剂量
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                    频率
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                    持续时间
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                    备注
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 bg-white">
                {plan.medications.length > 0 ? (
                  plan.medications.map((medication) => (
                    <tr key={medication.id} className="hover:bg-gray-50">
                      <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-900">{medication.name}</td>
                      <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-900">{medication.dosage}</td>
                      <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-900">{medication.frequency}</td>
                      <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-900">{medication.duration}</td>
                      <td className="px-6 py-4 text-sm text-gray-900">{medication.notes || '-'}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5} className="px-6 py-4 text-center text-sm text-gray-500">
                      无药物信息
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
        
        {/* 治疗项目卡片 */}
        <div className="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
          <div className="border-b border-gray-200 bg-gray-50 px-6 py-4">
            <h2 className="text-lg font-medium text-gray-800">治疗项目</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                    项目名称
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                    描述
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                    持续时间
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                    备注
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 bg-white">
                {plan.procedures.length > 0 ? (
                  plan.procedures.map((procedure) => (
                    <tr key={procedure.id} className="hover:bg-gray-50">
                      <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-900">{procedure.name}</td>
                      <td className="px-6 py-4 text-sm text-gray-900">{procedure.description}</td>
                      <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-900">{procedure.duration}</td>
                      <td className="px-6 py-4 text-sm text-gray-900">{procedure.notes || '-'}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={4} className="px-6 py-4 text-center text-sm text-gray-500">
                      无治疗项目信息
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
} 