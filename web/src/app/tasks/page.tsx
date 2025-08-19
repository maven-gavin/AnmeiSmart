'use client';

import { useState } from 'react';
import { useAuthContext } from '@/contexts/AuthContext';
import AppLayout from '@/components/layout/AppLayout';
import TaskList from '@/components/tasks/TaskList';
import TaskDetail from '@/components/tasks/TaskDetail';
import TaskFilters from '@/components/tasks/TaskFilters';
import { usePendingTasks } from '@/hooks/usePendingTasks';

import { Button } from '@/components/ui/button';
import { 
  CheckCircle, 
  Clock, 
  AlertCircle, 
  Users,
  Filter,
  RefreshCw
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export default function TasksPage() {
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [showFilters, setShowFilters] = useState(false);
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
  } = usePendingTasks(user?.currentRole);

  const handleTaskSelect = (taskId: string) => {
    setSelectedTaskId(taskId);
  };

  const handleTaskClaim = async (taskId: string) => {
    try {
      await claimTask(taskId);
    } catch (error) {
      console.error('认领任务失败:', error);
    }
  };

  const handleTaskStatusUpdate = async (taskId: string, status: string, result?: unknown) => {
    try {
      await updateTaskStatus(taskId, status, result);
      if (selectedTaskId === taskId) {
        setSelectedTaskId(null);
      }
    } catch (error) {
      console.error('更新任务状态失败:', error);
    }
  };

  const handleBackToList = () => {
    setSelectedTaskId(null);
  };



  if (isLoading) {
    return (
      <AppLayout requiredRole={user?.currentRole}>
        <div className="flex h-screen items-center justify-center">
          <div className="text-center">
            <div className="mb-4 h-12 w-12 animate-spin rounded-full border-b-2 border-t-2 border-orange-500"></div>
            <p className="text-gray-600">加载任务列表...</p>
          </div>
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout requiredRole={user?.currentRole}>
      <div className="container mx-auto px-4 py-6">
        {/* 页面头部 */}
        <div className="mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-800">
                {selectedTaskId ? '任务详情' : '待办任务'}
              </h1>
              <p className="text-gray-600 mt-1">
                {selectedTaskId ? '查看和处理任务详情' : '管理系统分配的待办任务'}
              </p>
            </div>

            <div className="flex items-center space-x-3">
              {!selectedTaskId && (
                <>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowFilters(!showFilters)}
                    className="flex items-center space-x-2"
                  >
                    <Filter className="h-4 w-4" />
                    <span>筛选</span>
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={refreshTasks}
                    className="flex items-center space-x-2"
                  >
                    <RefreshCw className="h-4 w-4" />
                    <span>刷新</span>
                  </Button>
                </>
              )}
            </div>
          </div>
        </div>

        {!selectedTaskId ? (
          <div className="space-y-6">
            {/* 统计卡片 */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">待处理</CardTitle>
                  <Clock className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stats.pending}</div>
                  <p className="text-xs text-muted-foreground">
                    等待认领处理
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">进行中</CardTitle>
                  <Users className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stats.inProgress}</div>
                  <p className="text-xs text-muted-foreground">
                    正在处理中
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">已完成</CardTitle>
                  <CheckCircle className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stats.completed}</div>
                  <p className="text-xs text-muted-foreground">
                    今日完成
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">紧急任务</CardTitle>
                  <AlertCircle className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stats.urgent}</div>
                  <p className="text-xs text-muted-foreground">
                    需优先处理
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* 筛选器 */}
            {showFilters && (
              <TaskFilters
                filters={filters}
                onFiltersChange={setFilters}
                onClose={() => setShowFilters(false)}
              />
            )}

            {/* 任务列表 */}
            <div className="bg-white rounded-lg shadow-sm">
              <TaskList
                tasks={tasks}
                onTaskSelect={handleTaskSelect}
                onTaskClaim={handleTaskClaim}
                currentUserId={user?.id}
              />
            </div>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow-sm">
            <TaskDetail
              taskId={selectedTaskId}
              onBack={handleBackToList}
              onStatusUpdate={handleTaskStatusUpdate}
              currentUserId={user?.id}
            />
          </div>
        )}
      </div>
    </AppLayout>
  );
}
