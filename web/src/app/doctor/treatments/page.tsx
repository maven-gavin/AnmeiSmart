'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { doctorService } from '@/service/doctorService';
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

export default function TreatmentsPage() {
  const [loading, setLoading] = useState(true);
  const [treatments, setTreatments] = useState<Treatment[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState<Treatment['status'] | 'all'>('all');
  
  useEffect(() => {
    const loadTreatments = async () => {
      try {
        setLoading(true);
        const data = await doctorService.getTreatments();
        setTreatments(data);
      } catch (error) {
        console.error('加载治疗记录失败', error);
      } finally {
        setLoading(false);
      }
    };
    
    loadTreatments();
  }, []);
  
  // 过滤和搜索
  const filteredTreatments = treatments.filter(treatment => {
    // 状态过滤
    if (filterStatus !== 'all' && treatment.status !== filterStatus) {
      return false;
    }
    
    // 搜索过滤
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      return (
        treatment.patientName.toLowerCase().includes(query) ||
        treatment.treatmentType.toLowerCase().includes(query) ||
        treatment.details.toLowerCase().includes(query)
      );
    }
    
    return true;
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
          <h1 className="text-2xl font-bold text-gray-800">治疗记录</h1>
          <p className="text-gray-600">查看和管理患者治疗记录</p>
        </div>
        <Link 
          href="/doctor/treatments/create" 
          className="rounded-md bg-orange-500 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-orange-600"
        >
          新增治疗记录
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
            onChange={(e) => setFilterStatus(e.target.value as Treatment['status'] | 'all')}
            className="rounded-md border border-gray-300 px-4 py-2 focus:border-orange-500 focus:outline-none"
          >
            <option value="all">全部状态</option>
            <option value="completed">已完成</option>
            <option value="in-progress">进行中</option>
            <option value="cancelled">已取消</option>
          </select>
        </div>
      </div>
      
      {/* 治疗记录列表 */}
      <div className="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  患者信息
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  治疗项目
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  治疗日期
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  状态
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  治疗效果
                </th>
                <th scope="col" className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">
                  操作
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {filteredTreatments.length > 0 ? (
                filteredTreatments.map((treatment) => (
                  <tr key={treatment.id} className="hover:bg-gray-50">
                    <td className="whitespace-nowrap px-6 py-4">
                      <div className="flex items-center">
                        <div className="h-10 w-10 flex-shrink-0">
                          <img 
                            className="h-10 w-10 rounded-full"
                            src={`/avatars/user${treatment.patientId === '101' ? '1' : treatment.patientId === '102' ? '2' : '3'}.png`}
                            alt={treatment.patientName}
                          />
                        </div>
                        <div className="ml-4">
                          <div className="text-sm font-medium text-gray-900">{treatment.patientName}</div>
                          <div className="text-sm text-gray-500">患者ID: {treatment.patientId}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm font-medium text-gray-900">{treatment.treatmentType}</div>
                      <div className="text-sm text-gray-500 line-clamp-1">{treatment.details}</div>
                    </td>
                    <td className="whitespace-nowrap px-6 py-4">
                      <div className="text-sm text-gray-900">
                        {new Date(treatment.date).toLocaleDateString('zh-CN')}
                      </div>
                      <div className="text-sm text-gray-500">
                        {treatment.duration}分钟
                      </div>
                    </td>
                    <td className="whitespace-nowrap px-6 py-4">
                      <StatusBadge status={treatment.status} />
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-900 line-clamp-2">{treatment.outcome}</div>
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-right text-sm font-medium">
                      <Link 
                        href={`/doctor/treatments/${treatment.id}`}
                        className="text-orange-600 hover:text-orange-900 mr-4"
                      >
                        查看
                      </Link>
                      <Link 
                        href={`/doctor/treatments/${treatment.id}/edit`}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        编辑
                      </Link>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} className="px-6 py-4 text-center text-sm text-gray-500">
                    {searchQuery || filterStatus !== 'all'
                      ? '没有找到符合条件的治疗记录'
                      : '暂无治疗记录数据'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
} 