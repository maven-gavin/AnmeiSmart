'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthContext } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Checkbox } from '@/components/ui/checkbox';
import AppLayout from '@/components/layout/AppLayout';
import { useAgentConfigs } from '@/hooks/useAgentConfigs';
import { AgentConfig, AgentConfigCreate } from '@/service/agentConfigService';

export default function AgentsPage() {
  const { user } = useAuthContext();
  const router = useRouter();
  const {
    configs: agentConfigs,
    isLoading,
    createConfig,
    deleteConfig,
    testConnection
  } = useAgentConfigs();

  const [configs, setConfigs] = useState<AgentConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [formLoading, setFormLoading] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  
  // 表单字段
  const [environment, setEnvironment] = useState('dev');
  const [appId, setAppId] = useState('');
  const [appName, setAppName] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [baseUrl, setBaseUrl] = useState('http://localhost/v1');
  const [description, setDescription] = useState('');
  const [timeoutSeconds, setTimeoutSeconds] = useState(30);
  const [maxRetries, setMaxRetries] = useState(3);
  const [enabled, setEnabled] = useState(true);

  // 分页状态
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(5);
  
  // 搜索筛选状态
  const [searchEnvironment, setSearchEnvironment] = useState('all');
  const [searchAppName, setSearchAppName] = useState('');
  const [searchStatus, setSearchStatus] = useState('all');
  const [allConfigs, setAllConfigs] = useState<AgentConfig[]>([]);

  // 检查用户是否有管理员权限
  useEffect(() => {
    if (user && !user.roles.includes('admin')) {
      router.push('/unauthorized');
    }
  }, [user, router]);

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

  // 创建配置
  const handleCreateConfig = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!appId.trim() || !appName.trim() || !apiKey.trim()) {
      setFormError('应用ID、应用名称和API密钥不能为空');
      return;
    }
    
    setFormLoading(true);
    setFormError(null);
    
    try {
      const configData: AgentConfigCreate = {
        environment,
        appId: appId.trim(),
        appName: appName.trim(),
        apiKey: apiKey.trim(),
        baseUrl,
        description: description.trim() || undefined,
        timeoutSeconds,
        maxRetries,
        enabled
      };

      await createConfig(configData);
      
      // 重置表单
      setEnvironment('dev');
      setAppId('');
      setAppName('');
      setApiKey('');
      setBaseUrl('http://localhost/v1');
      setDescription('');
      setTimeoutSeconds(30);
      setMaxRetries(3);
      setEnabled(true);
      setShowCreateForm(false);
    } catch (err) {
      setFormError(err instanceof Error ? err.message : '创建配置失败');
      console.error('创建配置错误', err);
    } finally {
      setFormLoading(false);
    }
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

  return (
    <AppLayout requiredRole={user?.currentRole}>
      <div className="container mx-auto px-4 py-6">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">Agent配置管理</h1>
            <p className="text-gray-600 mt-1">管理Agent应用的配置信息</p>
          </div>
          <Button 
            onClick={() => setShowCreateForm(!showCreateForm)}
            className="bg-orange-500 hover:bg-orange-600"
          >
            {showCreateForm ? '取消' : '添加配置'}
          </Button>
        </div>

        {/* 组合查询区域 */}
        <div className="mb-6 rounded-lg border border-gray-200 bg-white p-4 shadow">
          <h2 className="mb-4 text-lg font-medium text-gray-800">组合查询</h2>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <div>
              <Label htmlFor="searchEnvironment" className="mb-2 block text-sm font-medium">环境</Label>
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
              <Label htmlFor="searchAppName" className="mb-2 block text-sm font-medium">应用名称</Label>
              <Input
                id="searchAppName"
                value={searchAppName}
                onChange={(e) => setSearchAppName(e.target.value)}
                placeholder="搜索应用名称"
                className="w-full"
              />
            </div>
            <div>
              <Label htmlFor="searchStatus" className="mb-2 block text-sm font-medium">状态</Label>
              <Select value={searchStatus} onValueChange={setSearchStatus}>
                <SelectTrigger>
                  <SelectValue placeholder="所有状态" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">所有状态</SelectItem>
                  <SelectItem value="enabled">启用</SelectItem>
                  <SelectItem value="disabled">禁用</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="mt-4 flex justify-end space-x-2">
            <Button variant="outline" onClick={resetFilters}>
              重置
            </Button>
            <Button className="bg-orange-500 hover:bg-orange-600" onClick={filterConfigs}>
              查询
            </Button>
          </div>
        </div>



        {showCreateForm && (
          <div className="mb-6 rounded-lg border border-gray-200 bg-white p-4 shadow">
            <h2 className="mb-4 text-lg font-medium text-gray-800">创建新配置</h2>
            
            {formError && (
              <div className="mb-4 rounded-md bg-red-50 p-3 text-sm text-red-500">
                {formError}
              </div>
            )}
            
            <form onSubmit={handleCreateConfig} className="space-y-4">
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div>
                  <Label htmlFor="environment" className="mb-2 block text-sm font-medium text-gray-700">
                    环境 *
                  </Label>
                  <Select value={environment} onValueChange={setEnvironment}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="dev">开发环境</SelectItem>
                      <SelectItem value="test">测试环境</SelectItem>
                      <SelectItem value="prod">生产环境</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                <div>
                  <Label htmlFor="appId" className="mb-2 block text-sm font-medium text-gray-700">
                    应用ID *
                  </Label>
                  <Input
                    id="appId"
                    type="text"
                    value={appId}
                    onChange={(e) => setAppId(e.target.value)}
                    disabled={formLoading}
                    placeholder="例如: AGENT_CHAT_API_KEY"
                  />
                </div>

                <div>
                  <Label htmlFor="appName" className="mb-2 block text-sm font-medium text-gray-700">
                    应用名称 *
                  </Label>
                  <Input
                    id="appName"
                    type="text"
                    value={appName}
                    onChange={(e) => setAppName(e.target.value)}
                    disabled={formLoading}
                    placeholder="例如: 通用聊天"
                  />
                </div>

                <div>
                  <Label htmlFor="baseUrl" className="mb-2 block text-sm font-medium text-gray-700">
                    基础URL
                  </Label>
                  <Input
                    id="baseUrl"
                    type="text"
                    value={baseUrl}
                    onChange={(e) => setBaseUrl(e.target.value)}
                    disabled={formLoading}
                    placeholder="http://localhost/v1"
                  />
                </div>

                <div>
                  <Label htmlFor="timeoutSeconds" className="mb-2 block text-sm font-medium text-gray-700">
                    超时时间(秒)
                  </Label>
                  <Input
                    id="timeoutSeconds"
                    type="number"
                    value={timeoutSeconds}
                    onChange={(e) => setTimeoutSeconds(parseInt(e.target.value) || 30)}
                    disabled={formLoading}
                    min="1"
                    max="300"
                  />
                </div>

                <div>
                  <Label htmlFor="maxRetries" className="mb-2 block text-sm font-medium text-gray-700">
                    最大重试次数
                  </Label>
                  <Input
                    id="maxRetries"
                    type="number"
                    value={maxRetries}
                    onChange={(e) => setMaxRetries(parseInt(e.target.value) || 3)}
                    disabled={formLoading}
                    min="0"
                    max="10"
                  />
                </div>
              </div>

              <div>
                <Label htmlFor="apiKey" className="mb-2 block text-sm font-medium text-gray-700">
                  API密钥 *
                </Label>
                <Input
                  id="apiKey"
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  disabled={formLoading}
                  placeholder="输入API密钥"
                />
              </div>
              
              <div>
                <Label htmlFor="description" className="mb-2 block text-sm font-medium text-gray-700">
                  描述
                </Label>
                <Textarea
                  id="description"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  disabled={formLoading}
                  rows={3}
                  placeholder="可选: 配置的详细描述"
                />
              </div>

              <div className="flex items-center space-x-2">
                <Checkbox
                  id="enabled"
                  checked={enabled}
                  onCheckedChange={setEnabled}
                  disabled={formLoading}
                />
                <Label htmlFor="enabled" className="text-sm font-medium text-gray-700">
                  启用配置
                </Label>
              </div>
              
              <div className="flex justify-end space-x-3">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setShowCreateForm(false);
                    setFormError(null);
                  }}
                  disabled={formLoading}
                >
                  取消
                </Button>
                <Button
                  type="submit"
                  disabled={formLoading}
                  className="bg-orange-500 hover:bg-orange-600"
                >
                  {formLoading ? '创建中...' : '创建配置'}
                </Button>
              </div>
            </form>
          </div>
        )}

        <div className="overflow-hidden rounded-lg border border-gray-200 shadow">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  环境
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  应用名称
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  应用ID
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  基础URL
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  状态
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  操作
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {currentConfigs.map((config) => (
                <tr key={config.id} className="hover:bg-gray-50">
                  <td className="whitespace-nowrap px-6 py-4 text-sm font-medium text-gray-900">
                    <span className={`rounded-full ${getEnvironmentStyle(config.environment)} px-3 py-1 text-sm font-medium`}>
                      {config.environment}
                    </span>
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-900">
                    {config.appName}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                    {config.appId}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                    {config.baseUrl}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm font-medium text-gray-900">
                    <span className={`rounded-full ${getStatusStyle(config.enabled)} px-3 py-1 text-sm font-medium`}>
                      {config.enabled ? '启用' : '禁用'}
                    </span>
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm font-medium space-x-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => testConnection(config)}
                      className="text-blue-600 hover:text-blue-800"
                    >
                      测试连接
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      className="text-gray-600 hover:text-gray-800"
                    >
                      编辑
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => deleteConfig(config.id)}
                      className="text-red-600 hover:text-red-800"
                      disabled={config.enabled}
                    >
                      删除
                    </Button>
                  </td>
                </tr>
              ))}
              
              {configs.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-6 py-4 text-center text-sm text-gray-500">
                    暂无配置数据
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        
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
