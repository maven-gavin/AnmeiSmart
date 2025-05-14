'use client';

import { useEffect, useState } from 'react';
import { customerService } from '@/service/customerService';
import { CustomerAppointment } from '@/types/customer';

// 预约卡片组件
function AppointmentCard({ appointment }: { appointment: CustomerAppointment }) {
  const statusClasses = {
    confirmed: 'bg-green-100 text-green-800',
    pending: 'bg-yellow-100 text-yellow-800',
    canceled: 'bg-red-100 text-red-800',
    completed: 'bg-blue-100 text-blue-800',
  };
  
  const statusText = {
    confirmed: '已确认',
    pending: '待确认',
    canceled: '已取消',
    completed: '已完成',
  };
  
  const typeText = {
    consultation: '咨询',
    treatment: '治疗',
    followup: '复诊',
  };
  
  const isPast = new Date(`${appointment.date} ${appointment.time}`) < new Date();
  
  return (
    <div className={`rounded-lg border ${
      isPast ? 'border-gray-200 bg-gray-50' : 'border-orange-200 bg-white'
    } p-5 shadow-sm`}>
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-lg font-medium text-gray-800">{appointment.title}</h3>
        <span className={`rounded-full px-3 py-1 text-xs font-medium ${statusClasses[appointment.status]}`}>
          {statusText[appointment.status]}
        </span>
      </div>
      
      <div className="mb-4 grid grid-cols-1 gap-2 text-sm md:grid-cols-2">
        <div>
          <p className="font-medium text-gray-700">预约类型：
            <span className="font-normal text-gray-600">
              {typeText[appointment.type]}
            </span>
          </p>
        </div>
        <div>
          <p className="font-medium text-gray-700">预约时间：
            <span className="font-normal text-gray-600">
              {appointment.date} {appointment.time}
            </span>
          </p>
        </div>
        {appointment.doctor && (
          <div>
            <p className="font-medium text-gray-700">医生：
              <span className="font-normal text-gray-600">{appointment.doctor}</span>
            </p>
          </div>
        )}
        {appointment.advisor && (
          <div>
            <p className="font-medium text-gray-700">顾问：
              <span className="font-normal text-gray-600">{appointment.advisor}</span>
            </p>
          </div>
        )}
      </div>
      
      {appointment.notes && (
        <div className="mb-4">
          <p className="text-xs font-medium text-gray-500">备注</p>
          <p className="text-sm text-gray-600">{appointment.notes}</p>
        </div>
      )}
      
      <div className="mt-4 flex items-center justify-end space-x-3">
        {appointment.status !== 'canceled' && appointment.status !== 'completed' && !isPast && (
          <>
            <button className="rounded-md border border-red-200 bg-white px-3 py-1 text-xs font-medium text-red-600 hover:bg-red-50">
              取消预约
            </button>
            <button className="rounded-md border border-orange-200 bg-white px-3 py-1 text-xs font-medium text-orange-600 hover:bg-orange-50">
              修改时间
            </button>
          </>
        )}
        {appointment.status === 'completed' && (
          <button className="rounded-md border border-blue-200 bg-white px-3 py-1 text-xs font-medium text-blue-600 hover:bg-blue-50">
            评价服务
          </button>
        )}
      </div>
    </div>
  );
}

// 空状态组件
function EmptyState() {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-8 text-center">
      <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-gray-100">
        <svg className="h-8 w-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
      </div>
      <h3 className="mb-1 text-lg font-medium text-gray-800">暂无预约</h3>
      <p className="text-gray-500">您目前没有任何预约记录</p>
      <button className="mt-4 rounded-md bg-orange-500 px-4 py-2 text-sm font-medium text-white hover:bg-orange-600">
        预约咨询
      </button>
    </div>
  );
}

export default function AppointmentsList() {
  const [appointments, setAppointments] = useState<CustomerAppointment[]>([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    const loadAppointments = async () => {
      try {
        const data = await customerService.getAppointments();
        
        // 按日期排序，最近的排前面
        data.sort((a, b) => {
          const dateA = new Date(`${a.date} ${a.time}`).getTime();
          const dateB = new Date(`${b.date} ${b.time}`).getTime();
          return dateB - dateA;
        });
        
        setAppointments(data);
      } catch (error) {
        console.error('加载预约失败', error);
      } finally {
        setLoading(false);
      }
    };
    
    loadAppointments();
  }, []);
  
  // 将预约分为未来和历史
  const futureAppointments = appointments.filter(appointment => {
    return new Date(`${appointment.date} ${appointment.time}`) >= new Date();
  });
  
  const pastAppointments = appointments.filter(appointment => {
    return new Date(`${appointment.date} ${appointment.time}`) < new Date();
  });
  
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
        <h1 className="text-2xl font-bold text-gray-800">我的预约</h1>
        <p className="text-gray-600">管理您的咨询和治疗预约</p>
      </div>
      
      {appointments.length === 0 ? (
        <EmptyState />
      ) : (
        <div className="space-y-8">
          {futureAppointments.length > 0 && (
            <div>
              <h2 className="mb-4 text-lg font-medium text-gray-800">
                即将到来的预约 ({futureAppointments.length})
              </h2>
              <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
                {futureAppointments.map((appointment) => (
                  <AppointmentCard key={appointment.id} appointment={appointment} />
                ))}
              </div>
            </div>
          )}
          
          {pastAppointments.length > 0 && (
            <div>
              <h2 className="mb-4 text-lg font-medium text-gray-800">
                历史预约 ({pastAppointments.length})
              </h2>
              <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
                {pastAppointments.map((appointment) => (
                  <AppointmentCard key={appointment.id} appointment={appointment} />
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
} 