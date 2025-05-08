'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { doctorService } from '@/lib/doctorService';
import { Patient, Treatment, TreatmentPlan, DoctorAppointment } from '@/types/doctor';

export default function PatientDetailPage() {
  const params = useParams();
  const router = useRouter();
  const patientId = params.id as string;
  
  const [loading, setLoading] = useState(true);
  const [patient, setPatient] = useState<Patient | null>(null);
  const [treatments, setTreatments] = useState<Treatment[]>([]);
  const [plans, setPlans] = useState<TreatmentPlan[]>([]);
  const [appointments, setAppointments] = useState<DoctorAppointment[]>([]);
  const [activeTab, setActiveTab] = useState('basic');
  
  useEffect(() => {
    const fetchPatientData = async () => {
      setLoading(true);
      try {
        // 获取患者基本信息
        const patientData = await doctorService.getPatientById(patientId);
        if (!patientData) {
          console.error('未找到患者数据');
          router.push('/doctor/patients');
          return;
        }
        setPatient(patientData);
        
        // 获取患者治疗记录
        const treatmentData = await doctorService.getTreatmentsByPatientId(patientId);
        setTreatments(treatmentData);
        
        // 获取患者治疗方案
        const allPlans = await doctorService.getTreatmentPlans();
        const patientPlans = allPlans.filter(plan => plan.patientId === patientId);
        setPlans(patientPlans);
        
        // 获取患者预约
        const allAppointments = await doctorService.getAppointments();
        const patientAppointments = allAppointments.filter(
          appointment => appointment.patientId === patientId
        );
        setAppointments(patientAppointments);
      } catch (error) {
        console.error('获取患者数据失败:', error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchPatientData();
  }, [patientId, router]);
  
  // 获取最新预约
  const upcomingAppointments = appointments
    .filter(a => 
      a.status !== 'completed' && 
      a.status !== 'cancelled' && 
      new Date(a.date + 'T' + a.time) >= new Date()
    )
    .sort((a, b) => 
      new Date(a.date + 'T' + a.time).getTime() - 
      new Date(b.date + 'T' + b.time).getTime()
    );
  
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
          <div className="flex gap-2">
            <Link
              href={`/doctor/treatments/create?patientId=${patient.id}`}
              className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
            >
              新增治疗记录
            </Link>
            <Link
              href={`/doctor/plans/create?patientId=${patient.id}`}
              className="rounded-md bg-orange-500 px-4 py-2 text-sm font-medium text-white hover:bg-orange-600"
            >
              创建治疗方案
            </Link>
            <Link
              href={`/doctor/appointments/create?patientId=${patient.id}`}
              className="rounded-md bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700"
            >
              预约就诊
            </Link>
          </div>
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
            <div className="mb-4 grid grid-cols-2 gap-4">
              <div className="rounded-md bg-blue-50 p-3 text-center">
                <span className="block text-2xl font-bold text-blue-600">{treatments.length}</span>
                <span className="text-sm text-gray-500">治疗记录</span>
              </div>
              <div className="rounded-md bg-orange-50 p-3 text-center">
                <span className="block text-2xl font-bold text-orange-600">{plans.length}</span>
                <span className="text-sm text-gray-500">治疗方案</span>
              </div>
            </div>
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
            {upcomingAppointments.length > 0 && (
              <div className="mt-4">
                <h4 className="mb-1 text-sm font-medium text-gray-700">即将到来的预约</h4>
                {upcomingAppointments.slice(0, 1).map(appointment => (
                  <div 
                    key={appointment.id} 
                    className="rounded-md border border-gray-200 bg-gray-50 p-2"
                  >
                    <div className="flex justify-between">
                      <span className="text-sm font-medium">{appointment.treatmentType}</span>
                      <span className="rounded-full bg-blue-100 px-2 py-0.5 text-xs text-blue-800">
                        {appointment.status === 'confirmed' ? '已确认' : '待确认'}
                      </span>
                    </div>
                    <div className="mt-1 text-xs text-gray-500">
                      {appointment.date} {appointment.time} · {appointment.duration}分钟
                    </div>
                  </div>
                ))}
              </div>
            )}
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
      
      {/* 选项卡导航 */}
      <div className="mb-4 border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('basic')}
            className={`pb-3 pt-2 text-sm font-medium ${
              activeTab === 'basic'
                ? 'border-b-2 border-orange-500 text-orange-600'
                : 'border-b-2 border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
            }`}
          >
            治疗记录
          </button>
          <button
            onClick={() => setActiveTab('plans')}
            className={`pb-3 pt-2 text-sm font-medium ${
              activeTab === 'plans'
                ? 'border-b-2 border-orange-500 text-orange-600'
                : 'border-b-2 border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
            }`}
          >
            治疗方案
          </button>
          <button
            onClick={() => setActiveTab('appointments')}
            className={`pb-3 pt-2 text-sm font-medium ${
              activeTab === 'appointments'
                ? 'border-b-2 border-orange-500 text-orange-600'
                : 'border-b-2 border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
            }`}
          >
            预约记录
          </button>
        </nav>
      </div>
      
      {/* 根据选项卡显示不同内容 */}
      <div className="mt-6">
        {/* 治疗记录 */}
        {activeTab === 'basic' && (
          <div>
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-lg font-medium text-gray-800">治疗记录列表</h3>
              <Link
                href={`/doctor/treatments/create?patientId=${patient.id}`}
                className="rounded-md bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700"
              >
                新增记录
              </Link>
            </div>
            
            <div className="overflow-hidden rounded-lg border border-gray-200 bg-white shadow">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                      治疗类型
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                      日期
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                      状态
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                      操作
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {treatments.length > 0 ? (
                    treatments.map((treatment) => (
                      <tr key={treatment.id} className="hover:bg-gray-50">
                        <td className="whitespace-nowrap px-6 py-4">
                          <div className="font-medium text-gray-900">{treatment.treatmentType}</div>
                        </td>
                        <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                          {new Date(treatment.date).toLocaleDateString('zh-CN')}
                        </td>
                        <td className="whitespace-nowrap px-6 py-4">
                          <span className={`rounded-full px-2 py-1 text-xs font-medium ${
                            treatment.status === 'completed' 
                              ? 'bg-green-100 text-green-800' 
                              : treatment.status === 'cancelled'
                              ? 'bg-red-100 text-red-800'
                              : 'bg-yellow-100 text-yellow-800'
                          }`}>
                            {treatment.status === 'completed' && '已完成'}
                            {treatment.status === 'cancelled' && '已取消'}
                            {treatment.status === 'in-progress' && '进行中'}
                          </span>
                        </td>
                        <td className="whitespace-nowrap px-6 py-4 text-sm">
                          <Link 
                            href={`/doctor/treatments/${treatment.id}`}
                            className="mr-2 text-indigo-600 hover:text-indigo-900"
                          >
                            查看详情
                          </Link>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={4} className="px-6 py-4 text-center text-sm text-gray-500">
                        暂无治疗记录
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}
        
        {/* 治疗方案 */}
        {activeTab === 'plans' && (
          <div>
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-lg font-medium text-gray-800">治疗方案列表</h3>
              <Link
                href={`/doctor/plans/create?patientId=${patient.id}`}
                className="rounded-md bg-orange-500 px-3 py-1.5 text-sm font-medium text-white hover:bg-orange-600"
              >
                创建方案
              </Link>
            </div>
            
            <div className="overflow-hidden rounded-lg border border-gray-200 bg-white shadow">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                      方案名称
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                      创建日期
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                      状态
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                      操作
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {plans.length > 0 ? (
                    plans.map((plan) => (
                      <tr key={plan.id} className="hover:bg-gray-50">
                        <td className="whitespace-nowrap px-6 py-4">
                          <div className="font-medium text-gray-900">{plan.diagnosis}</div>
                        </td>
                        <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                          {new Date(plan.createdAt).toLocaleDateString('zh-CN')}
                        </td>
                        <td className="whitespace-nowrap px-6 py-4">
                          <span className={`rounded-full px-2 py-1 text-xs font-medium ${
                            plan.status === 'approved' 
                              ? 'bg-green-100 text-green-800' 
                              : plan.status === 'cancelled' || plan.status === 'draft'
                              ? 'bg-gray-100 text-gray-800'
                              : plan.status === 'pending'
                              ? 'bg-yellow-100 text-yellow-800'
                              : 'bg-blue-100 text-blue-800'
                          }`}>
                            {plan.status === 'approved' && '已批准'}
                            {plan.status === 'cancelled' && '已取消'}
                            {plan.status === 'draft' && '草稿'}
                            {plan.status === 'pending' && '待审核'}
                            {plan.status === 'completed' && '已完成'}
                          </span>
                        </td>
                        <td className="whitespace-nowrap px-6 py-4 text-sm">
                          <Link 
                            href={`/doctor/plans/${plan.id}`}
                            className="mr-2 text-indigo-600 hover:text-indigo-900"
                          >
                            查看详情
                          </Link>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={4} className="px-6 py-4 text-center text-sm text-gray-500">
                        暂无治疗方案
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}
        
        {/* 预约记录 */}
        {activeTab === 'appointments' && (
          <div>
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-lg font-medium text-gray-800">预约记录列表</h3>
              <Link
                href={`/doctor/appointments/create?patientId=${patient.id}`}
                className="rounded-md bg-green-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-green-700"
              >
                创建预约
              </Link>
            </div>
            
            <div className="overflow-hidden rounded-lg border border-gray-200 bg-white shadow">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                      预约项目
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                      预约时间
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                      状态
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                      备注
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {appointments.length > 0 ? (
                    appointments.map((appointment) => (
                      <tr key={appointment.id} className="hover:bg-gray-50">
                        <td className="whitespace-nowrap px-6 py-4">
                          <div className="font-medium text-gray-900">{appointment.treatmentType}</div>
                        </td>
                        <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                          {appointment.date} {appointment.time} ({appointment.duration}分钟)
                        </td>
                        <td className="whitespace-nowrap px-6 py-4">
                          <span className={`rounded-full px-2 py-1 text-xs font-medium ${
                            appointment.status === 'confirmed' 
                              ? 'bg-blue-100 text-blue-800' 
                              : appointment.status === 'completed'
                              ? 'bg-green-100 text-green-800'
                              : appointment.status === 'cancelled'
                              ? 'bg-red-100 text-red-800'
                              : 'bg-yellow-100 text-yellow-800'
                          }`}>
                            {appointment.status === 'confirmed' && '已确认'}
                            {appointment.status === 'completed' && '已完成'}
                            {appointment.status === 'cancelled' && '已取消'}
                            {appointment.status === 'pending' && '待确认'}
                          </span>
                        </td>
                        <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                          {appointment.notes || '-'}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={4} className="px-6 py-4 text-center text-sm text-gray-500">
                        暂无预约记录
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
} 