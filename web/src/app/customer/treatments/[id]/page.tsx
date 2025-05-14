'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { customerService } from '@/service/customerService';
import { Treatment } from '@/types/customer';

// 图片对比组件
function BeforeAfterComparison({ 
  beforeImage, 
  afterImage 
}: { 
  beforeImage?: string; 
  afterImage?: string; 
}) {
  if (!beforeImage && !afterImage) return null;
  
  return (
    <div className="my-6 overflow-hidden rounded-lg">
      <div className="flex flex-col md:flex-row">
        {beforeImage && (
          <div className="flex-1">
            <div className="relative">
              <img 
                src={beforeImage} 
                alt="治疗前" 
                className="w-full rounded-t-lg object-cover md:rounded-l-lg md:rounded-t-none" 
              />
              <div className="absolute left-4 top-4 rounded-lg bg-black bg-opacity-50 px-3 py-1 text-sm text-white">
                治疗前
              </div>
            </div>
          </div>
        )}
        
        {afterImage && (
          <div className="flex-1">
            <div className="relative">
              <img 
                src={afterImage} 
                alt="治疗后" 
                className="w-full rounded-b-lg object-cover md:rounded-b-none md:rounded-r-lg" 
              />
              <div className="absolute left-4 top-4 rounded-lg bg-black bg-opacity-50 px-3 py-1 text-sm text-white">
                治疗后
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function TreatmentDetail() {
  const params = useParams();
  const router = useRouter();
  const [treatment, setTreatment] = useState<Treatment | null>(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    const loadTreatment = async () => {
      try {
        if (typeof params.id !== 'string') {
          throw new Error('Invalid treatment ID');
        }
        
        const data = await customerService.getTreatmentById(params.id);
        
        if (!data) {
          // 如果找不到记录，返回列表页
          router.push('/customer/treatments');
          return;
        }
        
        setTreatment(data);
      } catch (error) {
        console.error('加载治疗记录详情失败', error);
      } finally {
        setLoading(false);
      }
    };
    
    loadTreatment();
  }, [params.id, router]);
  
  const statusText = {
    completed: '已完成',
    scheduled: '已预约',
    canceled: '已取消',
  };
  
  const statusClasses = {
    completed: 'bg-green-100 text-green-800',
    scheduled: 'bg-blue-100 text-blue-800',
    canceled: 'bg-red-100 text-red-800',
  };
  
  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="h-12 w-12 animate-spin rounded-full border-4 border-orange-500 border-t-transparent"></div>
      </div>
    );
  }
  
  if (!treatment) {
    return null; // 加载失败会重定向，这里不会渲染
  }
  
  return (
    <div className="min-h-full bg-gray-50 p-6">
      <div className="mb-6">
        <Link href="/customer/treatments" className="inline-flex items-center text-sm text-orange-600 hover:text-orange-500">
          <svg className="mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          返回治疗记录
        </Link>
      </div>
      
      <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
        <div className="border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-800">{treatment.name}</h1>
            <span className={`rounded-full px-3 py-1 text-xs font-medium ${
              statusClasses[treatment.status as keyof typeof statusClasses]
            }`}>
              {statusText[treatment.status as keyof typeof statusText]}
            </span>
          </div>
        </div>
        
        <div className="p-6">
          <div className="mb-6 grid grid-cols-1 gap-6 md:grid-cols-2">
            <div>
              <h2 className="mb-3 text-lg font-medium text-gray-800">治疗信息</h2>
              <dl className="grid grid-cols-1 gap-2 text-sm">
                <div className="grid grid-cols-3 gap-2 py-2">
                  <dt className="font-medium text-gray-500">治疗项目</dt>
                  <dd className="col-span-2 text-gray-800">{treatment.name}</dd>
                </div>
                <div className="grid grid-cols-3 gap-2 py-2">
                  <dt className="font-medium text-gray-500">治疗时间</dt>
                  <dd className="col-span-2 text-gray-800">{treatment.date}</dd>
                </div>
                <div className="grid grid-cols-3 gap-2 py-2">
                  <dt className="font-medium text-gray-500">主治医生</dt>
                  <dd className="col-span-2 text-gray-800">{treatment.doctor}</dd>
                </div>
                <div className="grid grid-cols-3 gap-2 py-2">
                  <dt className="font-medium text-gray-500">状态</dt>
                  <dd className="col-span-2 text-gray-800">
                    {statusText[treatment.status as keyof typeof statusText]}
                  </dd>
                </div>
              </dl>
            </div>
            
            <div>
              <h2 className="mb-3 text-lg font-medium text-gray-800">治疗详情</h2>
              <p className="whitespace-pre-wrap text-sm text-gray-700">{treatment.description}</p>
            </div>
          </div>
          
          {/* 治疗前后对比 */}
          {(treatment.beforeImages?.length || treatment.afterImages?.length) && (
            <div className="mt-6">
              <h2 className="mb-3 text-lg font-medium text-gray-800">治疗效果对比</h2>
              
              {treatment.beforeImages && treatment.afterImages && 
               treatment.beforeImages.length > 0 && treatment.afterImages.length > 0 && (
                <BeforeAfterComparison
                  beforeImage={treatment.beforeImages[0]}
                  afterImage={treatment.afterImages[0]}
                />
              )}
              
              {/* 如果有多张图片，展示缩略图 */}
              {((treatment.beforeImages && treatment.beforeImages.length > 1) || 
                (treatment.afterImages && treatment.afterImages.length > 1)) && (
                <div className="mt-4">
                  <p className="mb-2 text-sm font-medium text-gray-600">更多图片</p>
                  <div className="flex flex-wrap gap-4">
                    {treatment.beforeImages && treatment.beforeImages.slice(1).map((img, index) => (
                      <div key={`before-${index}`} className="relative h-20 w-20">
                        <img src={img} alt={`治疗前 ${index + 2}`} className="h-full w-full rounded-md object-cover" />
                        <span className="absolute bottom-0 left-0 rounded-bl-md rounded-tr-md bg-black bg-opacity-60 px-2 py-1 text-xs text-white">
                          前
                        </span>
                      </div>
                    ))}
                    
                    {treatment.afterImages && treatment.afterImages.slice(1).map((img, index) => (
                      <div key={`after-${index}`} className="relative h-20 w-20">
                        <img src={img} alt={`治疗后 ${index + 2}`} className="h-full w-full rounded-md object-cover" />
                        <span className="absolute bottom-0 left-0 rounded-bl-md rounded-tr-md bg-black bg-opacity-60 px-2 py-1 text-xs text-white">
                          后
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
          
          {/* 操作按钮 */}
          <div className="mt-8 flex items-center justify-end space-x-4">
            <Link
              href="/customer/chat"
              className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50"
            >
              咨询问题
            </Link>
            <Link
              href="/customer/appointments"
              className="rounded-md border border-orange-500 bg-orange-500 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-orange-600"
            >
              预约复查
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
} 