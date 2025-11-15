'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { doctorService } from '@/service/doctorService';
import { Patient } from '@/types/doctor';

export default function PatientDetailPage() {
  const params = useParams();
  const router = useRouter();
  const patientId = params.id as string;
  
  const [loading, setLoading] = useState(true);
  const [patient, setPatient] = useState<Patient | null>(null);
  
  useEffect(() => {
    // TODO: 实现真实API调用
    setLoading(false);
    router.push('/doctor/patients');
  }, [patientId, router]);
  
  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-orange-500 border-t-transparent"></div>
        <span className="ml-2 text-gray-600">加载患者信息中...</span>
      </div>
    );
  }
  
  if (!patient) {
    return (
      <div className="flex h-64 flex-col items-center justify-center">
        <div className="text-lg font-medium text-red-600">未找到患者信息</div>
        <Link href="/doctor/patients" className="mt-4 text-blue-600 hover:underline">
          返回患者列表
        </Link>
      </div>
    );
  }
  
  return (
    <div className="container mx-auto p-6">
      {/* 顶部导航和标题 */}
      <div className="mb-6">
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <Link href="/doctor" className="hover:text-gray-700">首页</Link>
          <span>/</span>
          <Link href="/doctor/patients" className="hover:text-gray-700">患者管理</Link>
          <span>/</span>
          <span className="text-gray-900">{patient.name} - 详情</span>
        </div>
        
        <div className="mt-4 flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-800">患者详情</h1>
        </div>
      </div>
      
      {/* 患者信息卡片 */}
      <div className="mb-6 grid grid-cols-1 gap-6 md:grid-cols-3">
        {/* 基本信息 */}
        <div className="overflow-hidden rounded-lg border border-gray-200 bg-white shadow">
          <div className="flex items-center space-x-4 border-b border-gray-200 px-6 py-4">
            <div className="h-16 w-16 flex-shrink-0">
              <img
                className="h-16 w-16 rounded-full object-cover"
                src={patient.avatar || "/avatars/default.png"}
                alt={patient.name}
              />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-800">{patient.name}</h2>
              <p className="text-sm text-gray-500">
                {patient.gender === 'male' ? '男' : '女'}, {patient.age}岁
              </p>
              {patient.needsFollowUp && (
                <span className="mt-1 inline-flex rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-800">
                  需要跟进
                </span>
              )}
            </div>
          </div>
          <div className="px-6 py-4">
            <div className="mb-2 flex items-center border-b border-gray-100 pb-2">
              <span className="w-24 text-sm font-medium text-gray-500">联系电话</span>
              <span className="text-sm text-gray-900">{patient.phone}</span>
            </div>
            <div className="mb-2 flex items-center border-b border-gray-100 pb-2">
              <span className="w-24 text-sm font-medium text-gray-500">电子邮箱</span>
              <span className="text-sm text-gray-900">{patient.email || '未填写'}</span>
            </div>
            <div className="mb-2 flex items-center border-b border-gray-100 pb-2">
              <span className="w-24 text-sm font-medium text-gray-500">最近就诊</span>
              <span className="text-sm text-gray-900">
                {new Date(patient.lastVisit).toLocaleDateString('zh-CN')}
              </span>
            </div>
            {patient.allergies.length > 0 && (
              <div className="mt-4">
                <span className="mb-2 block text-sm font-medium text-red-600">过敏史</span>
                <div className="flex flex-wrap gap-1">
                  {patient.allergies.map((allergy, index) => (
                    <span 
                      key={index} 
                      className="rounded-full bg-red-50 px-2 py-0.5 text-xs text-red-700"
                    >
                      {allergy}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
        
        {/* 治疗概览 */}
        <div className="overflow-hidden rounded-lg border border-gray-200 bg-white shadow">
          <div className="border-b border-gray-200 px-6 py-4">
            <h3 className="text-lg font-medium text-gray-800">治疗概览</h3>
          </div>
          <div className="px-6 py-4">
            <div className="mb-2">
              <h4 className="mb-1 text-sm font-medium text-gray-700">治疗项目</h4>
              <div className="flex flex-wrap gap-1">
                {patient.treatments.map((treatment, index) => (
                  <span 
                    key={index} 
                    className="rounded-full bg-blue-100 px-2 py-0.5 text-xs text-blue-800"
                  >
                    {treatment}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
        
        {/* 病历记录 */}
        <div className="overflow-hidden rounded-lg border border-gray-200 bg-white shadow">
          <div className="border-b border-gray-200 px-6 py-4">
            <h3 className="text-lg font-medium text-gray-800">病历记录</h3>
          </div>
          <div className="px-6 py-4">
            {patient.medicalHistory.length > 0 ? (
              <div className="divide-y divide-gray-100">
                {patient.medicalHistory.map(record => (
                  <div key={record.id} className="py-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">{record.description}</span>
                      <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-800">
                        {record.type === 'surgery' && '手术'}
                        {record.type === 'allergy' && '过敏'}
                        {record.type === 'treatment' && '治疗'}
                        {record.type === 'heart' && '心脏病史'}
                        {record.type === 'skin' && '皮肤问题'}
                      </span>
                    </div>
                    <div className="text-xs text-gray-500">
                      {new Date(record.date).toLocaleDateString('zh-CN')}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="py-4 text-center text-sm text-gray-500">
                无病历记录
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
} 