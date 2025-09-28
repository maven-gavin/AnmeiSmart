'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthContext } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import AppLayout from '@/components/layout/AppLayout';
import { useAgentConfigs } from '@/hooks/useAgentConfigs';
import { AgentConfig } from '@/service/agentConfigService';
import { Bot, Globe, Plus, Settings } from 'lucide-react';
import { toast } from 'react-hot-toast';

export default function AgentsPage() {
  const { user } = useAuthContext();
  const router = useRouter();
  const {
    configs: agentConfigs,
    isLoading,
  } = useAgentConfigs();

  const [configs, setConfigs] = useState<AgentConfig[]>([]);
  const [loading, setLoading] = useState(true);

  // 分页状态
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(5);
  
  // 搜索筛选状态
  const [searchEnvironment, setSearchEnvironment] = useState('all');
  const [searchAppName, setSearchAppName] = useState('');
  const [searchStatus, setSearchStatus] = useState('all');
  const [allConfigs, setAllConfigs] = useState<AgentConfig[]>([]);


  // 同步数据
  useEffect(() => {
    setConfigs(agentConfigs);
    setAllConfigs(agentConfigs);
    setLoading(isLoading);
  }, [agentConfigs, isLoading]);

  // 筛选配置
  const filterConfigs = () => {
    setCurrentPage(1);
    let filteredConfigs = [...allConfigs];
    
    if (searchEnvironment && searchEnvironment !== 'all') {
      filteredConfigs = filteredConfigs.filter(config => 
        config.environment.toLowerCase().includes(searchEnvironment.toLowerCase())
      );
    }
    
    if (searchAppName) {
      filteredConfigs = filteredConfigs.filter(config => 
        config.appName.toLowerCase().includes(searchAppName.toLowerCase())
      );
    }
    
    if (searchStatus && searchStatus !== 'all') {
      const isEnabled = searchStatus === 'enabled';
      filteredConfigs = filteredConfigs.filter(config => 
        config.enabled === isEnabled
      );
    }
    
    setConfigs(filteredConfigs);
  };

  // 重置筛选条件
  const resetFilters = () => {
    setSearchEnvironment('all');
    setSearchAppName('');
    setSearchStatus('all');
    setConfigs(allConfigs);
    setCurrentPage(1);
  };


  if (loading && configs.length === 0) {
    return (
      <div className="flex h-[calc(100vh-4rem)] items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-gray-300 border-t-orange-500"></div>
      </div>
    );
  }

  // 状态样式映射
  const getStatusStyle = (enabled: boolean) => {
    return enabled 
      ? 'bg-green-100 text-green-800' 
      : 'bg-gray-100 text-gray-800';
  };

  // 环境样式映射
  const getEnvironmentStyle = (env: string) => {
    const styles: Record<string, string> = {
      dev: 'bg-blue-100 text-blue-800',
      test: 'bg-yellow-100 text-yellow-800',
      prod: 'bg-red-100 text-red-800'
    };
    return styles[env] || 'bg-gray-100 text-gray-800';
  };
  
  // 分页逻辑
  const indexOfLastItem = currentPage * itemsPerPage;
  const indexOfFirstItem = indexOfLastItem - itemsPerPage;
  const currentConfigs = configs.slice(indexOfFirstItem, indexOfLastItem);
  const totalPages = Math.ceil(configs.length / itemsPerPage);

  // 页码变更
  const paginate = (pageNumber: number) => setCurrentPage(pageNumber);

  // 添加到工作空间
  const addToWorkspace = (config: AgentConfig) => {
    toast.success(`已将 ${config.appName} 添加到工作空间`);
  };

  // 获取智能体类型
  const getAgentType = (environment: string) => {
    const types: Record<string, string> = {
      dev: '开发环境',
      test: '测试环境', 
      prod: '生产环境'
    };
    return types[environment] || '未知类型';
  };

  return (
    <AppLayout requiredRole={user?.currentRole}>
      <div className="container mx-auto px-4 py-6">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">Agent探索</h1>
          </div>
        </div>

        {/* 组合查询区域 */}
        <div className="mb-6 rounded-lg border border-gray-200 bg-white p-4 shadow">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
            <span className="text-lg font-medium text-gray-800">组合查询:</span>
            <div>
              <Select value={searchEnvironment} onValueChange={setSearchEnvironment}>
                <SelectTrigger>
                  <SelectValue placeholder="所有环境" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">所有环境</SelectItem>
                  <SelectItem value="dev">开发环境</SelectItem>
                  <SelectItem value="test">测试环境</SelectItem>
                  <SelectItem value="prod">生产环境</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Input
                id="searchAppName"
                value={searchAppName}
                onChange={(e) => setSearchAppName(e.target.value)}
                placeholder="搜索应用名称"
                className="w-full"
              />
            </div>
            <div className="flex justify-end space-x-2">
              <Button variant="outline" onClick={resetFilters}>
                重置
              </Button>
              <Button className="bg-orange-500 hover:bg-orange-600" onClick={filterConfigs}>
                查询
              </Button>
            </div>
          </div>
          
        </div>

        {/* 卡片网格布局 */}
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {currentConfigs.map((config) => (
            <div
              key={config.id}
              className="group relative overflow-hidden rounded-lg border border-gray-200 bg-white p-6 shadow-sm transition-all duration-200 hover:shadow-md hover:border-orange-300"
            >
              {/* 智能体图标和基本信息 */}
              <div className="flex items-start space-x-4">
                <div className="flex-shrink-0">
                  <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-orange-100">
                    <Bot className="h-6 w-6 text-orange-600" />
                  </div>
                </div>
                <div className="min-w-0 flex-1">
                  <h3 className="text-lg font-semibold text-gray-900 truncate">
                    {config.appName}
                  </h3>
                  <p className="text-sm text-gray-600">
                    {getAgentType(config.environment)}
                  </p>
                </div>
              </div>

              {/* 描述信息 */}
              <div className="mt-4">
                <p className="text-sm text-gray-500 overflow-hidden" style={{
                  display: '-webkit-box',
                  WebkitLineClamp: 2,
                  WebkitBoxOrient: 'vertical'
                }}>
                  {config.description || '暂无描述信息'}
                </p>
              </div>

              {/* 状态和环境标签 */}
              <div className="mt-4 flex items-center justify-between">
                <span className={`rounded-full ${getEnvironmentStyle(config.environment)} px-3 py-1 text-xs font-medium`}>
                  {config.environment}
                </span>
                <span className={`rounded-full ${getStatusStyle(config.enabled)} px-3 py-1 text-xs font-medium`}>
                  {config.enabled ? '启用' : '禁用'}
                </span>
              </div>

              {/* 基础信息 */}
              <div className="mt-4 space-y-2">
                <div className="flex items-center text-xs text-gray-500">
                  <Settings className="mr-2 h-3 w-3" />
                  <span className="truncate">ID: {config.appId}</span>
                </div>
                <div className="flex items-center text-xs text-gray-500">
                  <Globe className="mr-2 h-3 w-3" />
                  <span className="truncate">{config.baseUrl}</span>
                </div>
              </div>

              {/* 悬浮按钮 */}
              <div className="absolute inset-x-0 bottom-0 transform translate-y-full transition-transform duration-200 group-hover:translate-y-0">
                <div className="bg-gradient-to-t from-white via-white to-transparent p-4 pt-8">
                  <Button
                    onClick={() => addToWorkspace(config)}
                    className="w-full bg-orange-500 hover:bg-orange-600 text-white"
                    size="sm"
                  >
                    <Plus className="mr-2 h-4 w-4" />
                    Add to workspace
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* 空状态 */}
        {configs.length === 0 && (
          <div className="text-center py-12">
            <Bot className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">暂无智能体</h3>
            <p className="mt-1 text-sm text-gray-500">暂无配置数据</p>
          </div>
        )}
        
        {/* 分页组件 */}
        {configs.length > 0 && (
          <div className="mt-6 flex justify-between items-center">
            <div className="flex space-x-2">
              <Button
                onClick={() => paginate(currentPage - 1)}
                disabled={currentPage === 1}
                variant="outline"
                size="sm"
                className="px-3"
              >
                上一页
              </Button>
              
              {Array.from({ length: totalPages }, (_, i) => (
                <Button
                  key={i}
                  onClick={() => paginate(i + 1)}
                  variant={currentPage === i + 1 ? "default" : "outline"}
                  size="sm"
                  className={`px-3 ${currentPage === i + 1 ? 'bg-orange-500 hover:bg-orange-600' : ''}`}
                >
                  {i + 1}
                </Button>
              ))}
              
              <Button
                onClick={() => paginate(currentPage + 1)}
                disabled={currentPage === totalPages}
                variant="outline"
                size="sm"
                className="px-3"
              >
                下一页
              </Button>
            </div>
          </div>
        )}
      </div>
    </AppLayout>
  );
}
