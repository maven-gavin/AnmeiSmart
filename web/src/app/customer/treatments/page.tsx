'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { customerService } from '@/lib/customerService';
import { Treatment } from '@/types/customer';

// 治疗记录卡片组件
function TreatmentCard({ treatment }: { treatment: Treatment }) {
  const statusClasses = {
    completed: 'bg-green-100 text-green-800',
    scheduled: 'bg-blue-100 text-blue-800',
    canceled: 'bg-red-100 text-red-800',
  };
  
  const statusText = {
    completed: '已完成',
    scheduled: '已预约',
    canceled: '已取消',
  };
  
  return (
    <Link href={`/customer/treatments/${treatment.id}`}>
      <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm transition-all hover:shadow-md">
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-800">{treatment.name}</h3>
          <span className={`rounded-full px-3 py-1 text-xs font-medium ${statusClasses[treatment.status]}`}>
            {statusText[treatment.status]}
          </span>
        </div>
        
        <div className="mb-4 text-sm text-gray-600">
          <p>治疗日期：{treatment.date}</p>
          <p>主治医生：{treatment.doctor}</p>
        </div>
        
        <p className="text-sm text-gray-700">{treatment.description}</p>
        
        {(treatment.beforeImages?.length || treatment.afterImages?.length) ? (
          <div className="mt-4">
            <p className="mb-2 text-xs font-medium text-gray-500">治疗前后对比</p>
            <div className="flex space-x-2">
              {treatment.beforeImages && treatment.beforeImages.length > 0 && (
                <div className="relative">
                  <img 
                    src={treatment.beforeImages[0]} 
                    alt="治疗前" 
                    className="h-20 w-20 rounded-md object-cover"
                  />
                  <span className="absolute bottom-0 left-0 rounded-bl-md rounded-tr-md bg-black bg-opacity-60 px-2 py-1 text-xs text-white">
                    前
                  </span>
                </div>
              )}
              
              {treatment.afterImages && treatment.afterImages.length > 0 && (
                <div className="relative">
                  <img 
                    src={treatment.afterImages[0]} 
                    alt="治疗后" 
                    className="h-20 w-20 rounded-md object-cover"
                  />
                  <span className="absolute bottom-0 left-0 rounded-bl-md rounded-tr-md bg-black bg-opacity-60 px-2 py-1 text-xs text-white">
                    后
                  </span>
                </div>
              )}
            </div>
          </div>
        ) : null}
      </div>
    </Link>
  );
}

export default function TreatmentsList() {
  const [treatments, setTreatments] = useState<Treatment[]>([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    const loadTreatments = async () => {
      try {
        const data = await customerService.getTreatments();
        setTreatments(data);
      } catch (error) {
        console.error('加载治疗记录失败', error);
      } finally {
        setLoading(false);
      }
    };
    
    loadTreatments();
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
        <h1 className="text-2xl font-bold text-gray-800">我的治疗记录</h1>
        <p className="text-gray-600">查看您的所有医美治疗历史</p>
      </div>
      
      {treatments.length === 0 ? (
        <div className="rounded-lg border border-gray-200 bg-white p-8 text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-gray-100">
            <svg className="h-8 w-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
          </div>
          <h3 className="mb-1 text-lg font-medium text-gray-800">暂无治疗记录</h3>
          <p className="text-gray-500">您尚未进行任何医美治疗</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
          {treatments.map((treatment) => (
            <TreatmentCard key={treatment.id} treatment={treatment} />
          ))}
        </div>
      )}
    </div>
  );
} 