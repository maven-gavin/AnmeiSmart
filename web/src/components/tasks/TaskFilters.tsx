'use client';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { X, Search, RotateCcw } from 'lucide-react';

export interface TaskFilters {
  status?: string;
  priority?: string;
  taskType?: string;
  assignedTo?: string;
  createdBy?: string;
  search?: string;
  dateRange?: {
    start?: string;
    end?: string;
  };
}

interface TaskFiltersProps {
  filters: TaskFilters;
  onFiltersChange: (filters: TaskFilters) => void;
  onClose: () => void;
}

export default function TaskFilters({
  filters,
  onFiltersChange,
  onClose
}: TaskFiltersProps) {
  const handleFilterChange = (key: keyof TaskFilters, value: any) => {
    // 如果值是 "all" 或空字符串，则设置为 undefined 以清除筛选
    const filterValue = value === 'all' || value === '' ? undefined : value;
    onFiltersChange({
      ...filters,
      [key]: filterValue
    });
  };

  const handleDateRangeChange = (key: 'start' | 'end', value: string) => {
    onFiltersChange({
      ...filters,
      dateRange: {
        ...filters.dateRange,
        [key]: value
      }
    });
  };

  const clearFilters = () => {
    onFiltersChange({});
  };

  const hasActiveFilters = () => {
    return Object.keys(filters).some(key => {
      const value = filters[key as keyof TaskFilters];
      if (key === 'dateRange') {
        return value && typeof value === 'object' && (value.start || value.end);
      }
      return value && value !== '' && value !== 'all';
    });
  };

  return (
    <div className="bg-white border rounded-lg p-6 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">筛选条件</h3>
        <Button
          variant="ghost"
          size="sm"
          onClick={onClose}
          className="h-8 w-8 p-0"
        >
          <X className="h-4 w-4" />
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
        {/* 搜索 */}
        <div>
          <Label htmlFor="search">搜索</Label>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              id="search"
              placeholder="搜索任务标题..."
              value={filters.search || ''}
              onChange={(e) => handleFilterChange('search', e.target.value)}
              className="pl-9"
            />
          </div>
        </div>

        {/* 状态 */}
        <div>
          <Label htmlFor="status">状态</Label>
          <Select
            value={filters.status || 'all'}
            onValueChange={(value) => handleFilterChange('status', value)}
          >
            <SelectTrigger>
              <SelectValue placeholder="选择状态" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部状态</SelectItem>
              <SelectItem value="pending">待认领</SelectItem>
              <SelectItem value="assigned">已分配</SelectItem>
              <SelectItem value="in_progress">进行中</SelectItem>
              <SelectItem value="completed">已完成</SelectItem>
              <SelectItem value="cancelled">已取消</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* 优先级 */}
        <div>
          <Label htmlFor="priority">优先级</Label>
          <Select
            value={filters.priority || 'all'}
            onValueChange={(value) => handleFilterChange('priority', value)}
          >
            <SelectTrigger>
              <SelectValue placeholder="选择优先级" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部优先级</SelectItem>
              <SelectItem value="urgent">紧急</SelectItem>
              <SelectItem value="high">高</SelectItem>
              <SelectItem value="medium">中</SelectItem>
              <SelectItem value="low">低</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* 任务类型 */}
        <div>
          <Label htmlFor="taskType">任务类型</Label>
          <Select
            value={filters.taskType || 'all'}
            onValueChange={(value) => handleFilterChange('taskType', value)}
          >
            <SelectTrigger>
              <SelectValue placeholder="选择任务类型" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部类型</SelectItem>
              <SelectItem value="new_user_reception">新用户接待</SelectItem>
              <SelectItem value="consultation_upgrade">咨询升级</SelectItem>
              <SelectItem value="system_exception">系统异常</SelectItem>
              <SelectItem value="periodic_followup">定期回访</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* 日期范围 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <div>
          <Label htmlFor="start-date">开始日期</Label>
          <Input
            id="start-date"
            type="date"
            value={filters.dateRange?.start || ''}
            onChange={(e) => handleDateRangeChange('start', e.target.value)}
          />
        </div>
        <div>
          <Label htmlFor="end-date">结束日期</Label>
          <Input
            id="end-date"
            type="date"
            value={filters.dateRange?.end || ''}
            onChange={(e) => handleDateRangeChange('end', e.target.value)}
          />
        </div>
      </div>

      {/* 操作按钮 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          {hasActiveFilters() && (
            <Button
              variant="outline"
              size="sm"
              onClick={clearFilters}
              className="flex items-center space-x-1"
            >
              <RotateCcw className="h-3 w-3" />
              <span>清除筛选</span>
            </Button>
          )}
        </div>

        <div className="text-sm text-gray-500">
          {hasActiveFilters() ? '已应用筛选条件' : '暂无筛选条件'}
        </div>
      </div>
    </div>
  );
}
