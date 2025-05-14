'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { customerService } from '@/service/customerService';
import { TreatmentPlan } from '@/types/customer';

// 治疗方案卡片组件
function PlanCard({ plan }: { plan: TreatmentPlan }) {
  const statusClasses = {
    draft: 'bg-gray-100 text-gray-800',
    pending: 'bg-yellow-100 text-yellow-800',
    approved: 'bg-green-100 text-green-800',
    rejected: 'bg-red-100 text-red-800',
  };
  
  const statusText = {
    draft: '草稿',
    pending: '待审核',
    approved: '已通过',
    rejected: '已拒绝',
  };
  
  // 格式化日期
  const formattedDate = new Date(plan.createdAt).toLocaleDateString('zh-CN');
  
  return (
    <Link href={`/customer/plans/${plan.id}`}>
      <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm transition-all hover:shadow-md">
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-800">{plan.title}</h3>
          <span className={`rounded-full px-3 py-1 text-xs font-medium ${statusClasses[plan.status]}`}>
            {statusText[plan.status]}
          </span>
        </div>
        
        <div className="mb-4 text-sm text-gray-600">
          <p>医生：{plan.doctorName}</p>
          <p>创建时间：{formattedDate}</p>
        </div>
        
        <div className="mb-3">
          <p className="mb-1 text-xs font-medium text-gray-500">治疗项目</p>
          <ul className="space-y-1 text-sm text-gray-700">
            {plan.items.slice(0, 2).map((item, index) => (
              <li key={index}>{item.name}</li>
            ))}
            {plan.items.length > 2 && (
              <li className="text-orange-500">+{plan.items.length - 2}个更多项目</li>
            )}
          </ul>
        </div>
        
        <div className="mt-4 flex items-center justify-between border-t border-gray-100 pt-4">
          <span className="text-xs text-gray-500">方案总价</span>
          <span className="text-xl font-bold text-orange-500">¥{plan.totalPrice.toLocaleString()}</span>
        </div>
      </div>
    </Link>
  );
}

export default function TreatmentPlansList() {
  const [plans, setPlans] = useState<TreatmentPlan[]>([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    const loadPlans = async () => {
      try {
        const data = await customerService.getTreatmentPlans();
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
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-800">我的治疗方案</h1>
        <p className="text-gray-600">查看医生为您定制的医美方案</p>
      </div>
      
      {plans.length === 0 ? (
        <div className="rounded-lg border border-gray-200 bg-white p-8 text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-gray-100">
            <svg className="h-8 w-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 className="mb-1 text-lg font-medium text-gray-800">暂无治疗方案</h3>
          <p className="text-gray-500">医生尚未为您制定医美方案</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
          {plans.map((plan) => (
            <PlanCard key={plan.id} plan={plan} />
          ))}
        </div>
      )}
    </div>
  );
} 