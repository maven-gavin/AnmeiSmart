'use client';

import { useState, useEffect } from 'react';
import { useAuthContext } from '@/contexts/AuthContext';
import AppLayout from '@/components/layout/AppLayout';
import { useTasks } from '@/hooks/useTasks';
import { apiClient, handleApiError } from '@/service/apiClient';
import { useRadixDialogBodyCleanup } from '@/hooks/useRadixDialogBodyCleanup';
import toast from 'react-hot-toast';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { EnhancedPagination } from '@/components/ui/pagination';
import { 
  CheckCircle, 
  Clock, 
  AlertCircle, 
  Users,
  RefreshCw,
  Plus,
  User,
  Calendar,
  Play,
  Pause,
  Check,
  XCircle,
  ArrowRight
} from 'lucide-react';
import { formatDistanceToNow, format, isValid } from 'date-fns';
import { zhCN } from 'date-fns/locale';

import type { Task, CreateTaskRequest, TaskFilters } from '@/types/task';
import { TASK_TYPE_LABELS, TASK_STATUS_LABELS, TASK_PRIORITY_LABELS } from '@/types/task';

export default function TasksPage() {
  const { user } = useAuthContext();
  
  const {
    tasks,
    isLoading,
    stats,
    filters,
    setFilters,
    claimTask,
    updateTaskStatus,
    refreshTasks
  } = useTasks(user?.currentRole);

  // 分页状态
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(5);

  // 搜索筛选状态
  const [searchText, setSearchText] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [priorityFilter, setPriorityFilter] = useState<string>('all');
  const [typeFilter, setTypeFilter] = useState<string>('all');

  // 详情抽屉状态
  const [isDetailOpen, setIsDetailOpen] = useState(false);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [notes, setNotes] = useState('');
  const [result, setResult] = useState('');
  const [isUpdating, setIsUpdating] = useState(false);

  // 新增任务抽屉状态
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  
  // 使用清理 hook 确保 Sheet 正确清理
  useRadixDialogBodyCleanup(isDetailOpen);
  useRadixDialogBodyCleanup(isCreateOpen);
  const [createLoading, setCreateLoading] = useState(false);
  const [createForm, setCreateForm] = useState<CreateTaskRequest>({
    title: '',
    description: '',
    task_type: 'new_user_reception',
    priority: 'medium',
  });

  // 筛选任务
  const filterTasks = () => {
    setCurrentPage(1);
    const newFilters: TaskFilters = {};
    if (searchText.trim()) newFilters.search = searchText.trim();
    if (statusFilter !== 'all') newFilters.status = statusFilter;
    if (priorityFilter !== 'all') newFilters.priority = priorityFilter;
    if (typeFilter !== 'all') newFilters.task_type = typeFilter;
    setFilters(newFilters);
  };

  // 重置筛选条件
  const resetFilters = () => {
    setSearchText('');
    setStatusFilter('all');
    setPriorityFilter('all');
    setTypeFilter('all');
    setCurrentPage(1);
    setFilters({});
  };

  // 打开任务详情
  const handleOpenDetail = async (task: Task) => {
    setSelectedTask(task);
    setNotes(task.notes || '');
    setResult(task.result ? JSON.stringify(task.result, null, 2) : '');
    setIsDetailOpen(true);
  };

  // 认领任务
  const handleClaimTask = async (taskId: string) => {
    try {
      await claimTask(taskId);
      // 刷新详情
      if (selectedTask?.id === taskId) {
        const response = await apiClient.get<Task>(`/tasks/${taskId}`);
        setSelectedTask(response.data);
      }
    } catch (error) {
      console.error('认领任务失败:', error);
    }
  };

  // 更新任务状态
  const handleStatusUpdate = async (newStatus: string) => {
    if (!selectedTask) return;
    
    setIsUpdating(true);
    try {
      const updateData: any = {
        status: newStatus,
        notes: notes.trim() || undefined
      };

      if (newStatus === 'completed' && result.trim()) {
        try {
          updateData.result = JSON.parse(result);
        } catch {
          updateData.result = { message: result.trim() };
        }
      }

      await updateTaskStatus(selectedTask.id, newStatus, updateData);
      toast.success('任务状态更新成功');
      setIsDetailOpen(false);
      setSelectedTask(null);
    } catch (error) {
      console.error('更新任务状态失败:', error);
      toast.error('更新任务状态失败');
    } finally {
      setIsUpdating(false);
    }
  };

  // 创建任务
  const handleCreateTask = async () => {
    if (!createForm.title.trim()) {
      toast.error('请输入任务标题');
      return;
    }

    setCreateLoading(true);
    try {
      await apiClient.post('/tasks', createForm);
      toast.success('任务创建成功');
      setIsCreateOpen(false);
      setCreateForm({
        title: '',
        description: '',
        task_type: 'new_user_reception',
        priority: 'medium',
      });
      refreshTasks();
    } catch (error) {
      handleApiError(error, '创建任务失败');
    } finally {
      setCreateLoading(false);
    }
  };

  // 分页逻辑
  const indexOfLastItem = currentPage * itemsPerPage;
  const indexOfFirstItem = indexOfLastItem - itemsPerPage;
  const currentTasks = tasks.slice(indexOfFirstItem, indexOfLastItem);
  const totalPages = Math.ceil(tasks.length / itemsPerPage);

  useEffect(() => {
    if (currentPage > totalPages && totalPages > 0) {
      setCurrentPage(totalPages);
    }
  }, [tasks, currentPage, totalPages]);

  // 格式化日期
  const formatDateSafely = (dateString: string | undefined) => {
    if (!dateString) return '未知时间';
    const date = new Date(dateString);
    if (!isValid(date)) return '无效时间';
    try {
      return formatDistanceToNow(date, { addSuffix: true, locale: zhCN });
    } catch {
      return '时间格式错误';
    }
  };

  const isOverdue = (dueDate?: string) => {
    if (!dueDate) return false;
    const date = new Date(dueDate);
    if (!isValid(date)) return false;
    return date < new Date();
  };

  const canClaim = (task: Task) => task.status === 'pending' && !task.assigned_to;
  const canStart = (task: Task) => (task.status === 'assigned' || task.status === 'pending') && 
    (task.assigned_to?.id === user?.id || !task.assigned_to);
  const canComplete = (task: Task) => task.status === 'in_progress' && task.assigned_to?.id === user?.id;
  const canCancel = (task: Task) => task.status !== 'completed' && task.status !== 'cancelled';

  // 状态样式
  const getStatusStyle = (status: string) => {
    const styles: Record<string, string> = {
      pending: 'bg-brand-soft text-brand-primaryHover',
      assigned: 'bg-blue-100 text-blue-800',
      in_progress: 'bg-brand-mid text-brand-deep',
      completed: 'bg-green-100 text-green-800',
      cancelled: 'bg-gray-100 text-gray-800',
    };
    return styles[status] || 'bg-gray-100 text-gray-800';
  };

  // 优先级样式
  const getPriorityStyle = (priority: string) => {
    const styles: Record<string, string> = {
      urgent: 'bg-red-100 text-red-800',
      high: 'bg-brand-mid text-brand-deep',
      medium: 'bg-brand-soft text-brand-primaryHover',
      low: 'bg-green-100 text-green-800',
    };
    return styles[priority] || 'bg-gray-100 text-gray-800';
  };

  if (isLoading && tasks.length === 0) {
    return (
      <AppLayout requiredRole={user?.currentRole}>
        <div className="flex h-[calc(100vh-4rem)] items-center justify-center">
          <div className="am-spinner"></div>
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout requiredRole={user?.currentRole}>
      <div className="am-page">
        <div className="am-container">
        {/* 页面头部 */}
        <div className="mb-6 flex items-center justify-between">
          <h1 className="am-page-title">任务管理</h1>
          <div className="flex items-center gap-2">
            <Button
              className="am-btn-primary"
              size="sm"
              onClick={() => setIsCreateOpen(true)}
            >
              <Plus className="h-4 w-4 mr-1" />
              新增任务
            </Button>
          </div>
        </div>

        {/* 统计卡片 */}
        <div className="hidden md:grid md:grid-cols-4 gap-4 mb-6">
          <Card className="am-card">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-700">待处理</CardTitle>
              <Clock className="h-4 w-4 text-gray-400" />
            </CardHeader>
            <CardContent className="flex items-center gap-2">
              <div className="text-2xl font-bold text-gray-900">{stats.pending}</div>
              <p className="text-xs text-gray-500">等待认领处理</p>
            </CardContent>
          </Card>
          <Card className="am-card">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-700">进行中</CardTitle>
              <Users className="h-4 w-4 text-gray-400" />
            </CardHeader>
            <CardContent className="flex items-center gap-2">
              <div className="text-2xl font-bold text-gray-900">{stats.inProgress}</div>
              <p className="text-xs text-gray-500">正在处理中</p>
            </CardContent>
          </Card>
          <Card className="am-card">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-700">已完成</CardTitle>
              <CheckCircle className="h-4 w-4 text-gray-400" />
            </CardHeader>
            <CardContent className="flex items-center gap-2">
              <div className="text-2xl font-bold text-gray-900">{stats.completed}</div>
              <p className="text-xs text-gray-500">今日完成</p>
            </CardContent>
          </Card>
          <Card className="am-card">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-700">紧急任务</CardTitle>
              <AlertCircle className="h-4 w-4 text-gray-400" />
            </CardHeader>
            <CardContent className="flex items-center gap-2">
              <div className="text-2xl font-bold text-gray-900">{stats.urgent}</div>
              <p className="text-xs text-gray-500">需优先处理</p>
            </CardContent>
          </Card>
        </div>

        {/* 搜索筛选栏 */}
        <div className="am-filter-bar">
          <div className="flex items-center gap-4 flex-wrap">
            <div className="flex items-center gap-2 flex-1 min-w-[200px]">
              <Label htmlFor="search" className="w-16 flex-shrink-0 text-sm text-gray-700">搜索:</Label>
              <Input
                id="search"
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    filterTasks();
                  }
                }}
                placeholder="搜索任务标题、描述"
                className="flex-1 am-field"
              />
            </div>
            <div className="flex items-center gap-2">
              <Label htmlFor="status" className="flex-shrink-0 text-sm text-gray-700">状态:</Label>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger id="status" className="w-28 am-field">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部</SelectItem>
                  <SelectItem value="pending">待认领</SelectItem>
                  <SelectItem value="assigned">已分配</SelectItem>
                  <SelectItem value="in_progress">进行中</SelectItem>
                  <SelectItem value="completed">已完成</SelectItem>
                  <SelectItem value="cancelled">已取消</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center gap-2">
              <Label htmlFor="priority" className="flex-shrink-0 text-sm text-gray-700">优先级:</Label>
              <Select value={priorityFilter} onValueChange={setPriorityFilter}>
                <SelectTrigger id="priority" className="w-24 am-field">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部</SelectItem>
                  <SelectItem value="urgent">紧急</SelectItem>
                  <SelectItem value="high">高</SelectItem>
                  <SelectItem value="medium">中</SelectItem>
                  <SelectItem value="low">低</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center gap-2">
              <Label htmlFor="type" className="flex-shrink-0 text-sm text-gray-700">类型:</Label>
              <Select value={typeFilter} onValueChange={setTypeFilter}>
                <SelectTrigger id="type" className="w-32 am-field">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部</SelectItem>
                  {Object.entries(TASK_TYPE_LABELS).map(([key, label]) => (
                    <SelectItem key={key} value={key}>{label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex space-x-2 flex-shrink-0">
              <Button 
                variant="outline" 
                onClick={resetFilters}
                className="am-btn-reset"
              >
                重置
              </Button>
              <Button 
                className="am-btn-primary"
                onClick={filterTasks}
              >
                查询
              </Button>
            </div>
          </div>
        </div>

        {/* 移动端卡片式布局 */}
        <div className="md:hidden space-y-3">
          {currentTasks.map((task) => (
            <Card 
              key={task.id} 
              className={`am-card overflow-hidden transition-shadow hover:shadow-md pt-6 ${
                isOverdue(task.due_date) ? 'border-l-4 border-l-red-500' : ''
              }`}
            >
              <CardContent className="p-4">
                {/* 任务标题和状态 */}
                <div className="flex items-start justify-between gap-3 mb-3">
                  <div className="flex-1 min-w-0">
                    <h3 className="text-base font-semibold text-gray-900 mb-1 line-clamp-2">
                      {task.title}
                    </h3>
                    {task.description && (
                      <p className="text-sm text-gray-600 line-clamp-2 mb-2">
                        {task.description}
                      </p>
                    )}
                  </div>
                  <span className={`flex-shrink-0 inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${getStatusStyle(task.status)}`}>
                    {TASK_STATUS_LABELS[task.status] || task.status}
                  </span>
                </div>

                {/* 任务元信息 */}
                <div className="space-y-2 mb-4">
                  {/* 类型和优先级 */}
                  <div className="flex items-center gap-2 flex-wrap">
                    <Badge variant="outline" className="text-xs am-badge-neutral">
                      {TASK_TYPE_LABELS[task.task_type] || task.task_type}
                    </Badge>
                    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${getPriorityStyle(task.priority)}`}>
                      {TASK_PRIORITY_LABELS[task.priority] || task.priority}
                    </span>
                  </div>

                  {/* 负责人 */}
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <User className="h-4 w-4 text-gray-400" />
                    <span>{task.assigned_to ? task.assigned_to.username : '未分配'}</span>
                  </div>

                  {/* 截止时间 */}
                  {task.due_date && (
                    <div className={`flex items-center gap-2 text-xs ${isOverdue(task.due_date) ? 'text-red-600 font-medium' : 'text-gray-500'}`}>
                      <Clock className={`h-3.5 w-3.5 ${isOverdue(task.due_date) ? 'text-red-600' : 'text-gray-400'}`} />
                      <span>截止: {formatDateSafely(task.due_date)}</span>
                      {isOverdue(task.due_date) && <AlertCircle className="h-3.5 w-3.5 text-red-600" />}
                    </div>
                  )}

                  {/* 创建时间 */}
                  <div className="flex items-center gap-2 text-xs text-gray-500">
                    <Calendar className="h-3.5 w-3.5 text-gray-400" />
                    <span>{formatDateSafely(task.created_at)}</span>
                  </div>
                </div>

                {/* 操作按钮 */}
                <div className="flex gap-2 pt-3 border-t border-gray-100">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleOpenDetail(task)}
                    className="flex-1 am-btn-outline"
                  >
                    <ArrowRight className="h-4 w-4 mr-1.5" />
                    查看详情
                  </Button>
                  {canClaim(task) && (
                    <Button
                      size="sm"
                      onClick={() => handleClaimTask(task.id)}
                      className="flex-1 am-btn-primary"
                    >
                      <User className="h-4 w-4 mr-1.5" />
                      认领任务
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}

          {tasks.length === 0 && (
            <Card className="am-card">
              <CardContent className="p-12 text-center">
                <CheckCircle className="h-12 w-12 mx-auto text-gray-400 mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">暂无任务</h3>
                <p className="text-gray-500">所有任务都已处理完成</p>
              </CardContent>
            </Card>
          )}
        </div>

        {/* 桌面端表格布局 */}
        <div className="hidden md:block overflow-hidden rounded-lg border border-gray-200 shadow-sm bg-white">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  任务信息
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium uppercase tracking-wider text-gray-500">
                  类型
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium uppercase tracking-wider text-gray-500">
                  状态
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium uppercase tracking-wider text-gray-500">
                  优先级
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium uppercase tracking-wider text-gray-500">
                  负责人
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium uppercase tracking-wider text-gray-500">
                  创建时间
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">
                  操作
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {currentTasks.map((task) => (
                <tr key={task.id} className={`hover:bg-gray-50 ${isOverdue(task.due_date) ? 'border-l-4 border-red-500' : ''}`}>
                  <td className="px-6 py-4">
                    <div className="min-w-0">
                      <div className="text-sm font-medium text-gray-900 truncate max-w-xs">
                        {task.title}
                      </div>
                      {task.description && (
                        <p className="text-sm text-gray-500 truncate max-w-xs">
                          {task.description}
                        </p>
                      )}
                      {task.due_date && (
                        <div className={`flex items-center gap-1 text-xs mt-1 ${isOverdue(task.due_date) ? 'text-red-600' : 'text-gray-400'}`}>
                          <Clock className="h-3 w-3" />
                          <span>截止: {formatDateSafely(task.due_date)}</span>
                          {isOverdue(task.due_date) && <AlertCircle className="h-3 w-3" />}
                        </div>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <Badge variant="outline" className="text-xs am-badge-neutral">
                      {TASK_TYPE_LABELS[task.task_type] || task.task_type}
                    </Badge>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${getStatusStyle(task.status)}`}>
                      {TASK_STATUS_LABELS[task.status] || task.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${getPriorityStyle(task.priority)}`}>
                      {TASK_PRIORITY_LABELS[task.priority] || task.priority}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-center text-sm text-gray-600">
                    {task.assigned_to ? (
                      <div className="flex items-center justify-center gap-1">
                        <User className="h-4 w-4" />
                        <span>{task.assigned_to.username}</span>
                      </div>
                    ) : (
                      <span className="text-gray-400">未分配</span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-center text-sm text-gray-500">
                    <div className="flex items-center justify-center gap-1">
                      <Calendar className="h-4 w-4" />
                      <span>{formatDateSafely(task.created_at)}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-right text-sm">
                    <div className="flex justify-end space-x-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleOpenDetail(task)}
                        className="am-btn-ghost-brand"
                      >
                        查看详情
                        <ArrowRight className="h-3 w-3 ml-1" />
                      </Button>
                      {canClaim(task) && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleClaimTask(task.id)}
                          className="am-btn-ghost-brand"
                        >
                          <User className="h-3 w-3 mr-1" />
                          认领任务
                        </Button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}

              {tasks.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center">
                    <CheckCircle className="h-12 w-12 mx-auto text-gray-400 mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">暂无任务</h3>
                    <p className="text-gray-500">所有任务都已处理完成</p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* 分页 */}
        {tasks.length > 0 && (
          <div className="mt-6">
            <EnhancedPagination
              currentPage={currentPage}
              totalPages={totalPages}
              totalItems={tasks.length}
              itemsPerPage={itemsPerPage}
              itemsPerPageOptions={[5, 10, 20, 50]}
              onPageChange={setCurrentPage}
              onItemsPerPageChange={(newItemsPerPage) => {
                setItemsPerPage(newItemsPerPage);
                setCurrentPage(1);
              }}
              showPageInput={true}
            />
          </div>
        )}
        </div>
      </div>

      {/* 任务详情抽屉 */}
      <Sheet open={isDetailOpen} onOpenChange={setIsDetailOpen}>
        <SheetContent side="right" className="w-[94vw] sm:w-[640px] lg:w-[800px] max-h-screen overflow-y-auto">
          <SheetHeader>
            <SheetTitle className="flex items-center gap-2">
              任务详情
              {selectedTask && (
                <Badge className={getStatusStyle(selectedTask.status)}>
                  {TASK_STATUS_LABELS[selectedTask.status]}
                </Badge>
              )}
            </SheetTitle>
          </SheetHeader>

          {selectedTask && (
            <div className="mt-6 space-y-6">
              {/* 基本信息 */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">{selectedTask.title}</h3>
                <div className="flex items-center gap-2 mb-4">
                  <Badge variant="outline" className="am-badge-neutral">{TASK_TYPE_LABELS[selectedTask.task_type] || selectedTask.task_type}</Badge>
                  <Badge className={getPriorityStyle(selectedTask.priority)}>
                    {TASK_PRIORITY_LABELS[selectedTask.priority]}
                  </Badge>
                </div>
                <p className="text-gray-600">{selectedTask.description || '暂无描述'}</p>
              </div>

              {/* 任务信息 */}
              <div className="bg-gray-50 rounded-lg p-4 space-y-3 text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-gray-500">任务ID</span>
                  <span className="am-mono text-xs text-gray-700">{selectedTask.id}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-500">创建时间</span>
                  <span>{format(new Date(selectedTask.created_at), 'yyyy-MM-dd HH:mm', { locale: zhCN })}</span>
                </div>
                {selectedTask.due_date && (
                  <div className="flex items-center justify-between">
                    <span className="text-gray-500">截止时间</span>
                    <span className={isOverdue(selectedTask.due_date) ? 'text-red-600' : ''}>
                      {format(new Date(selectedTask.due_date), 'yyyy-MM-dd HH:mm', { locale: zhCN })}
                      {isOverdue(selectedTask.due_date) && <AlertCircle className="h-4 w-4 inline ml-1" />}
                    </span>
                  </div>
                )}
                {selectedTask.created_by && (
                  <div className="flex items-center justify-between">
                    <span className="text-gray-500">创建人</span>
                    <span>{selectedTask.created_by.username}</span>
                  </div>
                )}
                {selectedTask.assigned_to && (
                  <div className="flex items-center justify-between">
                    <span className="text-gray-500">负责人</span>
                    <span>{selectedTask.assigned_to.username}</span>
                  </div>
                )}
                {selectedTask.related_object_type && (
                  <div className="flex items-center justify-between">
                    <span className="text-gray-500">关联对象</span>
                    <div className="text-right">
                      <Badge variant="outline" className="text-xs mb-1 am-badge-neutral">{selectedTask.related_object_type}</Badge>
                      <div className="am-mono text-xs text-gray-600">{selectedTask.related_object_id}</div>
                    </div>
                  </div>
                )}
              </div>

              {/* 任务数据 */}
              {selectedTask.task_data ? (
                <div>
                  <Label className="text-sm font-medium">任务数据</Label>
                  <pre className="am-mono mt-2 text-sm text-gray-700 bg-gray-50 p-3 rounded border border-gray-300 overflow-auto max-h-40">
                    {JSON.stringify(selectedTask.task_data, null, 2)}
                  </pre>
                </div>
              ) : null}

              {/* 处理记录 */}
              <div className="space-y-4">
                <div>
                  <Label htmlFor="notes">处理备注</Label>
                  <Textarea
                    id="notes"
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    placeholder="记录处理过程和备注信息..."
                    rows={3}
                    disabled={selectedTask.status === 'completed' || selectedTask.status === 'cancelled'}
                    className="mt-2 am-field"
                  />
                </div>

                {canComplete(selectedTask) && (
                  <div>
                    <Label htmlFor="result">处理结果</Label>
                    <Textarea
                      id="result"
                      value={result}
                      onChange={(e) => setResult(e.target.value)}
                      placeholder="输入处理结果（支持JSON格式）..."
                      rows={3}
                      className="mt-2 am-field"
                    />
                  </div>
                )}

                {selectedTask.result && (
                  <div>
                    <Label>已有处理结果</Label>
                    <pre className="am-mono mt-2 text-sm text-gray-700 bg-white p-3 rounded border border-gray-300 overflow-auto max-h-40">
                      {typeof selectedTask.result === 'string' ? selectedTask.result : JSON.stringify(selectedTask.result, null, 2)}
                    </pre>
                  </div>
                )}
              </div>

              {/* 操作按钮 */}
              <div className="flex flex-wrap gap-2 pt-4 border-t">
                {canClaim(selectedTask) && (
                  <Button
                    onClick={() => handleClaimTask(selectedTask.id)}
                    disabled={isUpdating}
                    className="flex items-center gap-2 am-btn-primary"
                  >
                    <User className="h-4 w-4" />
                    认领任务
                  </Button>
                )}
                {canStart(selectedTask) && (
                  <Button
                    onClick={() => handleStatusUpdate('in_progress')}
                    disabled={isUpdating}
                    className="flex items-center gap-2 am-btn-primary"
                  >
                    <Play className="h-4 w-4" />
                    开始处理
                  </Button>
                )}
                {canComplete(selectedTask) && (
                  <Button
                    onClick={() => handleStatusUpdate('completed')}
                    disabled={isUpdating}
                    className="flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white border-0 shadow-sm"
                  >
                    <Check className="h-4 w-4" />
                    完成任务
                  </Button>
                )}
                {selectedTask.status === 'in_progress' && selectedTask.assigned_to?.id === user?.id && (
                  <Button
                    variant="outline"
                    onClick={() => handleStatusUpdate('assigned')}
                    disabled={isUpdating}
                    className="flex items-center gap-2 am-btn-reset"
                  >
                    <Pause className="h-4 w-4" />
                    暂停处理
                  </Button>
                )}
                {canCancel(selectedTask) && (
                  <Button
                    variant="outline"
                    onClick={() => handleStatusUpdate('cancelled')}
                    disabled={isUpdating}
                    className="flex items-center gap-2 text-red-600 hover:text-red-700 border-red-300 hover:bg-red-50"
                  >
                    <XCircle className="h-4 w-4" />
                    取消任务
                  </Button>
                )}
              </div>
            </div>
          )}
        </SheetContent>
      </Sheet>

      {/* 新增任务抽屉 */}
      <Sheet open={isCreateOpen} onOpenChange={setIsCreateOpen}>
        <SheetContent side="right" className="w-[94vw] sm:w-[540px] max-h-screen overflow-y-auto">
          <SheetHeader>
            <SheetTitle>新增任务</SheetTitle>
          </SheetHeader>

          <div className="mt-6 space-y-4">
            <div>
              <Label htmlFor="title">任务标题 *</Label>
              <Input
                id="title"
                value={createForm.title}
                onChange={(e) => setCreateForm({ ...createForm, title: e.target.value })}
                placeholder="输入任务标题"
                className="mt-2 am-field"
              />
            </div>

            <div>
              <Label htmlFor="description">任务描述</Label>
              <Textarea
                id="description"
                value={createForm.description}
                onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })}
                placeholder="输入任务描述"
                rows={3}
                className="mt-2 am-field"
              />
            </div>

            <div>
              <Label htmlFor="task_type">任务类型</Label>
              <Select
                value={createForm.task_type}
                onValueChange={(value) => setCreateForm({ ...createForm, task_type: value })}
              >
                <SelectTrigger className="mt-2 am-field">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(TASK_TYPE_LABELS).map(([key, label]) => (
                    <SelectItem key={key} value={key}>{label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="priority">优先级</Label>
              <Select
                value={createForm.priority}
                onValueChange={(value: any) => setCreateForm({ ...createForm, priority: value })}
              >
                <SelectTrigger className="mt-2 am-field">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="low">低</SelectItem>
                  <SelectItem value="medium">中</SelectItem>
                  <SelectItem value="high">高</SelectItem>
                  <SelectItem value="urgent">紧急</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="due_date">截止时间</Label>
              <Input
                id="due_date"
                type="datetime-local"
                value={createForm.due_date || ''}
                onChange={(e) => setCreateForm({ ...createForm, due_date: e.target.value })}
                className="mt-2 am-field"
              />
            </div>

            <div className="flex justify-end gap-2 pt-4 border-t">
              <Button
                variant="outline"
                onClick={() => setIsCreateOpen(false)}
                disabled={createLoading}
                className="am-btn-reset"
              >
                取消
              </Button>
              <Button
                onClick={handleCreateTask}
                disabled={createLoading}
                className="am-btn-primary"
              >
                {createLoading ? '创建中...' : '创建任务'}
              </Button>
            </div>
          </div>
        </SheetContent>
      </Sheet>
    </AppLayout>
  );
}
