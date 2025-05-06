'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { doctorService } from '@/lib/doctorService';
import { Treatment } from '@/types/doctor';

// 状态标签组件
function StatusBadge({ status }: { status: Treatment['status'] }) {
  const statusConfig = {
    'completed': { bg: 'bg-green-100', text: 'text-green-800', label: '已完成' },
    'cancelled': { bg: 'bg-red-100', text: 'text-red-800', label: '已取消' },
    'in-progress': { bg: 'bg-blue-100', text: 'text-blue-800', label: '进行中' },
  };
  
  const config = statusConfig[status];
  
  return (
    <span className={`rounded-full px-2 py-1 text-xs ${config.bg} ${config.text}`}>
      {config.label}
    </span>
  );
}

export default function TreatmentDetailPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [treatment, setTreatment] = useState<Treatment | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    const loadTreatment = async () => {
      try {
        setLoading(true);
        const data = await doctorService.getTreatmentById(params.id);
        
        if (!data) {
          setError('未找到治疗记录');
          return;
        }
        
        setTreatment(data);
      } catch (err) {
        console.error('加载治疗记录失败', err);
        setError('加载治疗记录失败');
      } finally {
        setLoading(false);
      }
    };
    
    loadTreatment();
  }, [params.id]);
  
  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="h-12 w-12 animate-spin rounded-full border-4 border-orange-500 border-t-transparent"></div>
      </div>
    );
  }
  
  if (error || !treatment) {
    return (
      <div className="flex h-full flex-col items-center justify-center p-6">
        <div className="rounded-lg bg-red-50 p-4 text-red-800">
          <h3 className="text-lg font-medium">{error || '未找到治疗记录'}</h3>
          <p className="mt-2">请返回治疗记录列表重试</p>
        </div>
        <button
          onClick={() => router.push('/doctor/treatments')}
          className="mt-4 rounded-md bg-orange-500 px-4 py-2 text-white hover:bg-orange-600"
        >
          返回治疗记录列表
        </button>
      </div>
    );
  }
  
  return (
    <div className="p-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">治疗记录详情</h1>
          <p className="text-gray-600">查看患者的详细治疗信息</p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={() => router.push(`/doctor/treatments/${treatment.id}/edit`)}
            className="rounded-md bg-white px-4 py-2 text-sm font-medium text-orange-600 shadow-sm ring-1 ring-orange-600 hover:bg-orange-50"
          >
            编辑记录
          </button>
          <button
            onClick={() => router.push('/doctor/treatments')}
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
              <StatusBadge status={treatment.status} />
            </div>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
              <div>
                <h3 className="mb-2 text-sm font-medium text-gray-500">患者信息</h3>
                <div className="flex items-center">
                  <img 
                    src={`/avatars/user${treatment.patientId === '101' ? '1' : treatment.patientId === '102' ? '2' : '3'}.png`}
                    alt={treatment.patientName}
                    className="h-12 w-12 rounded-full"
                  />
                  <div className="ml-3">
                    <p className="font-medium">{treatment.patientName}</p>
                    <p className="text-sm text-gray-500">患者ID: {treatment.patientId}</p>
                  </div>
                </div>
              </div>
              
              <div>
                <h3 className="mb-2 text-sm font-medium text-gray-500">治疗信息</h3>
                <p className="font-medium">{treatment.treatmentType}</p>
                <p className="text-sm text-gray-500">
                  主治医生: {treatment.doctorName}
                </p>
                <p className="text-sm text-gray-500">
                  治疗日期: {new Date(treatment.date).toLocaleDateString('zh-CN')}
                  <span className="ml-2">({treatment.duration}分钟)</span>
                </p>
                {treatment.planId && (
                  <p className="mt-1 text-sm">
                    <span className="text-gray-500">关联方案: </span>
                    <button
                      onClick={() => router.push(`/doctor/plans/${treatment.planId}`)}
                      className="text-orange-600 hover:text-orange-800 underline"
                    >
                      查看方案
                    </button>
                  </p>
                )}
              </div>
            </div>
            
            <div className="mt-6">
              <h3 className="mb-2 text-sm font-medium text-gray-500">治疗详情</h3>
              <p className="rounded-md bg-gray-50 p-3 text-gray-800">{treatment.details}</p>
            </div>
            
            <div className="mt-6">
              <h3 className="mb-2 text-sm font-medium text-gray-500">治疗效果</h3>
              <p className="rounded-md bg-gray-50 p-3 text-gray-800">{treatment.outcome}</p>
            </div>
            
            {treatment.complications && (
              <div className="mt-6">
                <h3 className="mb-2 text-sm font-medium text-gray-500">并发症/副作用</h3>
                <p className="rounded-md bg-red-50 p-3 text-gray-800">{treatment.complications}</p>
              </div>
            )}
            
            {treatment.notes && (
              <div className="mt-6">
                <h3 className="mb-2 text-sm font-medium text-gray-500">备注</h3>
                <p className="rounded-md bg-gray-50 p-3 text-gray-800">{treatment.notes}</p>
              </div>
            )}
            
            <div className="mt-6">
              <h3 className="mb-2 text-sm font-medium text-gray-500">随访需求</h3>
              <div className="rounded-md bg-gray-50 p-3">
                <p className="text-gray-800">
                  {treatment.followUpRequired 
                    ? `需要随访，计划日期: ${new Date(treatment.followUpDate || '').toLocaleDateString('zh-CN')}` 
                    : '无需随访'}
                </p>
              </div>
            </div>
          </div>
        </div>
        
        {/* 药物卡片 */}
        <div className="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
          <div className="border-b border-gray-200 bg-gray-50 px-6 py-4">
            <h2 className="text-lg font-medium text-gray-800">用药情况</h2>
          </div>
          <div className="overflow-x-auto">
            {treatment.medications.length > 0 ? (
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
                  {treatment.medications.map((medication) => (
                    <tr key={medication.id} className="hover:bg-gray-50">
                      <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-900">{medication.name}</td>
                      <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-900">{medication.dosage}</td>
                      <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-900">{medication.frequency}</td>
                      <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-900">{medication.duration}</td>
                      <td className="px-6 py-4 text-sm text-gray-900">{medication.notes || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="p-6 text-center text-sm text-gray-500">
                无用药记录
              </div>
            )}
          </div>
        </div>
        
        {/* 治疗项目卡片 */}
        <div className="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
          <div className="border-b border-gray-200 bg-gray-50 px-6 py-4">
            <h2 className="text-lg font-medium text-gray-800">治疗项目</h2>
          </div>
          <div className="overflow-x-auto">
            {treatment.procedures.length > 0 ? (
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
                  {treatment.procedures.map((procedure) => (
                    <tr key={procedure.id} className="hover:bg-gray-50">
                      <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-900">{procedure.name}</td>
                      <td className="px-6 py-4 text-sm text-gray-900">{procedure.description}</td>
                      <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-900">{procedure.duration}</td>
                      <td className="px-6 py-4 text-sm text-gray-900">{procedure.notes || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="p-6 text-center text-sm text-gray-500">
                无治疗项目记录
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
} 