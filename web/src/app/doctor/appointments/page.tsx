'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { doctorService } from '@/lib/doctorService';
import { DoctorAppointment } from '@/types/doctor';

// 状态标签组件
function StatusBadge({ status }: { status: DoctorAppointment['status'] }) {
  const statusConfig = {
    'pending': { bg: 'bg-yellow-100', text: 'text-yellow-800', label: '待确认' },
    'confirmed': { bg: 'bg-blue-100', text: 'text-blue-800', label: '已确认' },
    'completed': { bg: 'bg-green-100', text: 'text-green-800', label: '已完成' },
    'cancelled': { bg: 'bg-red-100', text: 'text-red-800', label: '已取消' },
  };
  
  const config = statusConfig[status];
  
  return (
    <span className={`rounded-full px-2 py-1 text-xs ${config.bg} ${config.text}`}>
      {config.label}
    </span>
  );
}

export default function AppointmentsPage() {
  const [loading, setLoading] = useState(true);
  const [appointments, setAppointments] = useState<DoctorAppointment[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState<DoctorAppointment['status'] | 'all'>('all');
  const [filterDate, setFilterDate] = useState<'today' | 'all' | 'future'>('all');
  const [statusUpdating, setStatusUpdating] = useState<string | null>(null);
  
  useEffect(() => {
    const loadAppointments = async () => {
      try {
        setLoading(true);
        const data = await doctorService.getAppointments();
        setAppointments(data);
      } catch (error) {
        console.error('加载预约失败', error);
      } finally {
        setLoading(false);
      }
    };
    
    loadAppointments();
  }, []);
  
  // 更新预约状态
  const updateAppointmentStatus = async (id: string, status: DoctorAppointment['status']) => {
    if (statusUpdating) return; // 防止重复点击
    
    try {
      setStatusUpdating(id);
      await doctorService.updateAppointmentStatus(id, status);
      
      // 更新本地数据
      setAppointments(prevAppointments => 
        prevAppointments.map(appointment => 
          appointment.id === id ? { ...appointment, status } : appointment
        )
      );
    } catch (error) {
      console.error('更新预约状态失败', error);
      alert('更新预约状态失败，请重试');
    } finally {
      setStatusUpdating(null);
    }
  };
  
  // 过滤和搜索
  const filteredAppointments = appointments.filter(appointment => {
    // 状态过滤
    if (filterStatus !== 'all' && appointment.status !== filterStatus) {
      return false;
    }
    
    // 日期过滤
    const today = new Date().toISOString().split('T')[0];
    if (filterDate === 'today' && appointment.date !== today) {
      return false;
    } else if (filterDate === 'future' && appointment.date < today) {
      return false;
    }
    
    // 搜索过滤
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      return (
        appointment.patientName.toLowerCase().includes(query) ||
        appointment.treatmentType.toLowerCase().includes(query)
      );
    }
    
    return true;
  });
  
  // 按日期排序，近期的排在前面
  const sortedAppointments = [...filteredAppointments].sort((a, b) => {
    const dateA = a.date + 'T' + a.time;
    const dateB = b.date + 'T' + b.time;
    return dateA.localeCompare(dateB);
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
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">预约管理</h1>
          <p className="text-gray-600">查看和管理患者预约</p>
        </div>
        <Link 
          href="/doctor/appointments/create" 
          className="rounded-md bg-orange-500 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-orange-600"
        >
          添加新预约
        </Link>
      </div>
      
      {/* 搜索和过滤 */}
      <div className="mb-6 flex flex-wrap items-center gap-4">
        <div className="flex-1">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="搜索患者姓名或治疗类型"
            className="w-full rounded-md border border-gray-300 px-4 py-2 focus:border-orange-500 focus:outline-none"
          />
        </div>
        <div>
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value as DoctorAppointment['status'] | 'all')}
            className="rounded-md border border-gray-300 px-4 py-2 focus:border-orange-500 focus:outline-none"
          >
            <option value="all">全部状态</option>
            <option value="pending">待确认</option>
            <option value="confirmed">已确认</option>
            <option value="completed">已完成</option>
            <option value="cancelled">已取消</option>
          </select>
        </div>
        <div>
          <select
            value={filterDate}
            onChange={(e) => setFilterDate(e.target.value as 'today' | 'all' | 'future')}
            className="rounded-md border border-gray-300 px-4 py-2 focus:border-orange-500 focus:outline-none"
          >
            <option value="all">全部日期</option>
            <option value="today">今天</option>
            <option value="future">未来日期</option>
          </select>
        </div>
      </div>
      
      {/* 预约列表 */}
      <div className="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  患者信息
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  预约时间
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  治疗项目
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
              {sortedAppointments.length > 0 ? (
                sortedAppointments.map((appointment) => (
                  <tr key={appointment.id} className="hover:bg-gray-50">
                    <td className="whitespace-nowrap px-6 py-4">
                      <div className="flex items-center">
                        <div className="h-10 w-10 flex-shrink-0">
                          <img 
                            className="h-10 w-10 rounded-full"
                            src={`/avatars/user${appointment.patientId === '101' ? '1' : appointment.patientId === '102' ? '2' : '3'}.png`}
                            alt={appointment.patientName}
                          />
                        </div>
                        <div className="ml-4">
                          <div className="text-sm font-medium text-gray-900">{appointment.patientName}</div>
                          <div className="text-sm text-gray-500">患者ID: {appointment.patientId}</div>
                        </div>
                      </div>
                    </td>
                    <td className="whitespace-nowrap px-6 py-4">
                      <div className="text-sm text-gray-900">
                        {new Date(appointment.date).toLocaleDateString('zh-CN')}
                      </div>
                      <div className="text-sm text-gray-500">
                        {appointment.time} ({appointment.duration}分钟)
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm font-medium text-gray-900">{appointment.treatmentType}</div>
                      {appointment.description && (
                        <div className="text-sm text-gray-500 line-clamp-1">{appointment.description}</div>
                      )}
                    </td>
                    <td className="whitespace-nowrap px-6 py-4">
                      <StatusBadge status={appointment.status} />
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-right text-sm font-medium">
                      {/* 状态操作按钮 */}
                      {appointment.status === 'pending' && (
                        <>
                          <button
                            onClick={() => updateAppointmentStatus(appointment.id, 'confirmed')}
                            disabled={!!statusUpdating}
                            className="mr-2 text-green-600 hover:text-green-900"
                          >
                            确认
                          </button>
                          <button
                            onClick={() => updateAppointmentStatus(appointment.id, 'cancelled')}
                            disabled={!!statusUpdating}
                            className="text-red-600 hover:text-red-900"
                          >
                            取消
                          </button>
                        </>
                      )}
                      
                      {appointment.status === 'confirmed' && (
                        <>
                          <button
                            onClick={() => updateAppointmentStatus(appointment.id, 'completed')}
                            disabled={!!statusUpdating}
                            className="mr-2 text-green-600 hover:text-green-900"
                          >
                            完成
                          </button>
                          <button
                            onClick={() => updateAppointmentStatus(appointment.id, 'cancelled')}
                            disabled={!!statusUpdating}
                            className="text-red-600 hover:text-red-900"
                          >
                            取消
                          </button>
                        </>
                      )}
                      
                      {/* 详情按钮 */}
                      <button 
                        onClick={() => {
                          alert(`预约备注: ${appointment.notes || '无'}`);
                        }}
                        className={`ml-3 text-blue-600 hover:text-blue-900 ${
                          ['completed', 'cancelled'].includes(appointment.status) ? 'ml-0' : ''
                        }`}
                      >
                        详情
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5} className="px-6 py-4 text-center text-sm text-gray-500">
                    {searchQuery || filterStatus !== 'all' || filterDate !== 'all'
                      ? '没有找到符合条件的预约'
                      : '暂无预约数据'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
      
      {/* 图例 */}
      <div className="mt-6 flex flex-wrap items-center gap-4 text-sm text-gray-500">
        <span>图例:</span>
        <div className="flex items-center">
          <StatusBadge status="pending" />
          <span className="ml-2">待确认</span>
        </div>
        <div className="flex items-center">
          <StatusBadge status="confirmed" />
          <span className="ml-2">已确认</span>
        </div>
        <div className="flex items-center">
          <StatusBadge status="completed" />
          <span className="ml-2">已完成</span>
        </div>
        <div className="flex items-center">
          <StatusBadge status="cancelled" />
          <span className="ml-2">已取消</span>
        </div>
      </div>
    </div>
  );
} 