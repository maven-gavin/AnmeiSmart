'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { customerService } from '@/service/customerService';
import { TreatmentPlan } from '@/types/customer';

export default function TreatmentPlanDetail() {
  const params = useParams();
  const router = useRouter();
  const [plan, setPlan] = useState<TreatmentPlan | null>(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    const loadPlan = async () => {
      try {
        if (typeof params.id !== 'string') {
          throw new Error('Invalid plan ID');
        }
        
        const data = await customerService.getTreatmentPlanById(params.id);
        
        if (!data) {
          // 如果找不到记录，返回列表页
          router.push('/customer/plans');
          return;
        }
        
        setPlan(data);
      } catch (error) {
        console.error('加载治疗方案详情失败', error);
      } finally {
        setLoading(false);
      }
    };
    
    loadPlan();
  }, [params.id, router]);
  
  const statusText = {
    draft: '草稿',
    pending: '待审核',
    approved: '已通过',
    rejected: '已拒绝',
  };
  
  const statusClasses = {
    draft: 'bg-gray-100 text-gray-800',
    pending: 'bg-yellow-100 text-yellow-800',
    approved: 'bg-green-100 text-green-800',
    rejected: 'bg-red-100 text-red-800',
  };
  
  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="h-12 w-12 animate-spin rounded-full border-4 border-orange-500 border-t-transparent"></div>
      </div>
    );
  }
  
  if (!plan) {
    return null; // 加载失败会重定向，这里不会渲染
  }
  
  // 格式化创建日期
  const formattedDate = new Date(plan.createdAt).toLocaleDateString('zh-CN');
  
  return (
    <div className="min-h-full bg-gray-50 p-6">
      <div className="mb-6">
        <Link href="/customer/plans" className="inline-flex items-center text-sm text-orange-600 hover:text-orange-500">
          <svg className="mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          返回治疗方案列表
        </Link>
      </div>
      
      <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
        <div className="border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-800">{plan.title}</h1>
            <span className={`rounded-full px-3 py-1 text-xs font-medium ${
              statusClasses[plan.status as keyof typeof statusClasses]
            }`}>
              {statusText[plan.status as keyof typeof statusText]}
            </span>
          </div>
        </div>
        
        <div className="p-6">
          <div className="mb-6 grid grid-cols-1 gap-6 md:grid-cols-3">
            <div className="col-span-1">
              <h2 className="mb-3 text-lg font-medium text-gray-800">方案信息</h2>
              <dl className="grid grid-cols-1 gap-2 text-sm">
                <div className="grid grid-cols-3 gap-2 py-2">
                  <dt className="font-medium text-gray-500">方案名称</dt>
                  <dd className="col-span-2 text-gray-800">{plan.title}</dd>
                </div>
                <div className="grid grid-cols-3 gap-2 py-2">
                  <dt className="font-medium text-gray-500">创建医生</dt>
                  <dd className="col-span-2 text-gray-800">{plan.doctorName}</dd>
                </div>
                <div className="grid grid-cols-3 gap-2 py-2">
                  <dt className="font-medium text-gray-500">创建时间</dt>
                  <dd className="col-span-2 text-gray-800">{formattedDate}</dd>
                </div>
                <div className="grid grid-cols-3 gap-2 py-2">
                  <dt className="font-medium text-gray-500">方案状态</dt>
                  <dd className="col-span-2 text-gray-800">
                    {statusText[plan.status as keyof typeof statusText]}
                  </dd>
                </div>
              </dl>
            </div>
            
            <div className="col-span-2">
              {plan.notes && (
                <div className="mb-6">
                  <h2 className="mb-3 text-lg font-medium text-gray-800">方案说明</h2>
                  <div className="rounded-lg bg-orange-50 p-4 text-sm text-orange-800">
                    {plan.notes}
                  </div>
                </div>
              )}
            </div>
          </div>
          
          {/* 治疗项目列表 */}
          <div className="mb-8">
            <h2 className="mb-4 text-lg font-medium text-gray-800">治疗项目</h2>
            
            <div className="overflow-hidden rounded-lg border border-gray-200">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                      项目名称
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                      项目说明
                    </th>
                    <th scope="col" className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">
                      价格
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 bg-white">
                  {plan.items.map((item, index) => (
                    <tr key={index}>
                      <td className="whitespace-nowrap px-6 py-4 text-sm font-medium text-gray-800">
                        {item.name}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600">
                        {item.description}
                      </td>
                      <td className="whitespace-nowrap px-6 py-4 text-right text-sm font-medium text-gray-800">
                        ¥{item.price.toLocaleString()}
                      </td>
                    </tr>
                  ))}
                  
                  {/* 总计行 */}
                  <tr className="bg-gray-50">
                    <td colSpan={2} className="px-6 py-4 text-right text-sm font-medium text-gray-500">
                      总计
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-right text-base font-bold text-orange-600">
                      ¥{plan.totalPrice.toLocaleString()}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
          
          {/* 操作按钮 */}
          <div className="flex items-center justify-end space-x-4">
            <Link
              href="/customer/chat"
              className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50"
            >
              咨询方案
            </Link>
            {plan.status === 'approved' && (
              <Link
                href="/customer/appointments"
                className="rounded-md border border-orange-500 bg-orange-500 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-orange-600"
              >
                预约治疗
              </Link>
            )}
          </div>
        </div>
      </div>
    </div>
  );
} 