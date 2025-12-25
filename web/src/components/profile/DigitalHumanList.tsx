'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { EnhancedPagination } from '@/components/ui/pagination';
import { Shield, Bot, User, Building, Zap } from 'lucide-react';

import type { DigitalHuman } from '@/types/digital-human';
import { AvatarCircle } from '@/components/ui/AvatarCircle';

interface DigitalHumanListProps {
  digitalHumans: DigitalHuman[];
  onEdit: (id: string) => void;
  onDelete: (id: string) => void;
  onConfigureAgents: (id: string) => void;
}

export default function DigitalHumanList({
  digitalHumans,
  onEdit,
  onDelete,
  onConfigureAgents
}: DigitalHumanListProps) {
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(5);

  useEffect(() => {
    const totalPages = Math.max(1, Math.ceil(digitalHumans.length / itemsPerPage));
    if (currentPage > totalPages) {
      setCurrentPage(totalPages);
    }
  }, [digitalHumans, currentPage, itemsPerPage]);

  const getTypeStyle = (type: string) => {
    const styles: Record<string, string> = {
      personal: 'bg-blue-100 text-blue-800',
      business: 'bg-purple-100 text-purple-800',
      specialized: 'bg-green-100 text-green-800',
      system: 'bg-orange-100 text-orange-800'
    };
    return styles[type] || 'bg-gray-100 text-gray-800';
  };

  const getTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      personal: '个人助手',
      business: '商务助手',
      specialized: '专业助手',
      system: '系统助手'
    };
    return labels[type] || type;
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'personal':
        return <User className="h-4 w-4" />;
      case 'business':
        return <Building className="h-4 w-4" />;
      case 'specialized':
        return <Zap className="h-4 w-4" />;
      case 'system':
        return <Shield className="h-4 w-4" />;
      default:
        return <Bot className="h-4 w-4" />;
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return '从未';
    try {
      return new Date(dateString).toLocaleString('zh-CN');
    } catch {
      return '无效日期';
    }
  };

  const indexOfLastItem = currentPage * itemsPerPage;
  const indexOfFirstItem = indexOfLastItem - itemsPerPage;
  const currentDigitalHumans = digitalHumans.slice(indexOfFirstItem, indexOfLastItem);
  const totalPages = Math.max(1, Math.ceil(digitalHumans.length / itemsPerPage));

  return (
    <div className="space-y-4">
      <div className="overflow-hidden rounded-lg border border-gray-200 shadow-sm">
        <table className="min-w-full divide-y divide-gray-100">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                数字人信息
              </th>
              <th className="px-6 py-3 text-center text-xs font-medium uppercase tracking-wider text-gray-500">
                类型
              </th>
              <th className="px-6 py-3 text-center text-xs font-medium uppercase tracking-wider text-gray-500">
                状态
              </th>
              <th className="px-6 py-3 text-center text-xs font-medium uppercase tracking-wider text-gray-500">
                智能体
              </th>
              <th className="px-6 py-3 text-center text-xs font-medium uppercase tracking-wider text-gray-500">
                最后活跃
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">
                操作
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 bg-white">
            {currentDigitalHumans.map((dh) => (
              <tr key={dh.id} className="hover:bg-gray-50">
                <td className="px-6 py-4">
                  <div className="flex items-center space-x-3">
                    <AvatarCircle
                      name={dh.name}
                      avatar={dh.avatar}
                      sizeClassName="w-10 h-10"
                      className="flex-shrink-0 text-sm"
                    />
                    <div className="min-w-0">
                      <div className="flex items-center space-x-2">
                        <span className="text-sm font-medium text-gray-900">
                          {dh.name}
                        </span>
                        {dh.is_system_created && (
                          <span title="系统创建">
                            <Shield className="h-4 w-4 text-blue-500" />
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 text-center">
                  <span
                    className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ${getTypeStyle(
                      dh.type
                    )}`}
                  >
                    {getTypeIcon(dh.type)}
                    {getTypeLabel(dh.type)}
                  </span>
                </td>
                <td className="px-6 py-4 text-center">
                  <span
                    className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                      dh.status === 'active'
                        ? 'bg-green-100 text-green-800'
                        : dh.status === 'maintenance'
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    {dh.status === 'active'
                      ? '活跃'
                      : dh.status === 'maintenance'
                      ? '维护中'
                      : '停用'}
                  </span>
                </td>
                <td className="px-6 py-4 text-center text-sm text-gray-600">
                  {dh.agent_count || 0}
                </td>
                <td className="px-6 py-4 text-center text-sm text-gray-500">
                  {formatDate(dh.last_active_at)}
                </td>
                <td className="px-6 py-4 text-right text-sm">
                  <div className="flex justify-end space-x-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onEdit(dh.id)}
                      className="text-blue-600 hover:text-blue-800"
                    >
                      编辑
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onConfigureAgents(dh.id)}
                      className="text-gray-600 hover:text-gray-800"
                    >
                      配置
                    </Button>
                    {!dh.is_system_created && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onDelete(dh.id)}
                        className="text-red-600 hover:text-red-800"
                      >
                        删除
                      </Button>
                    )}
                  </div>
                </td>
              </tr>
            ))}

            {digitalHumans.length === 0 && (
              <tr>
                <td
                  colSpan={6}
                  className="px-6 py-6 text-center text-sm text-gray-500"
                >
                  暂无数字人数据
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {digitalHumans.length > 0 && (
        <div className="mt-4">
          <EnhancedPagination
            currentPage={currentPage}
            totalPages={totalPages}
            totalItems={digitalHumans.length}
            itemsPerPage={itemsPerPage}
            itemsPerPageOptions={[5, 10, 20, 50]}
            onPageChange={(page) => setCurrentPage(page)}
            onItemsPerPageChange={(newItemsPerPage) => {
              setItemsPerPage(newItemsPerPage);
              setCurrentPage(1);
            }}
            showPageInput
          />
        </div>
      )}
    </div>
  );
}
