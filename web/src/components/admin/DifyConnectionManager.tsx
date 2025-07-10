'use client';

import React, { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import { apiClient } from '@/service/apiClient';

interface DifyConnection {
  id: string;
  name: string;
  api_base_url: string;
  description?: string;
  is_default: boolean;
  is_active: boolean;
  last_sync_at?: string;
  sync_status: string;
}

interface DifyApp {
  id: string;
  name: string;
  description: string;
  mode: string;
  status: string;
  created_at?: string;
  icon?: string;
  tags: string[];
}

interface AgentType {
  value: string;
  label: string;
  description: string;
}

export const DifyConnectionManager: React.FC = () => {
  const [connections, setConnections] = useState<DifyConnection[]>([]);
  const [apps, setApps] = useState<DifyApp[]>([]);
  const [agentTypes, setAgentTypes] = useState<AgentType[]>([]);
  const [selectedConnection, setSelectedConnection] = useState<string>('');
  const [showNewConnection, setShowNewConnection] = useState(false);
  const [showAppConfig, setShowAppConfig] = useState(false);
  const [selectedApp, setSelectedApp] = useState<DifyApp | null>(null);
  const [loading, setLoading] = useState(false);

  const [newConnection, setNewConnection] = useState({
    name: '',
    api_base_url: 'http://localhost/v1',
    api_key: '',
    description: '',
    is_default: false
  });

  const [appConfig, setAppConfig] = useState({
    agent_type: 'general_chat',
    description: '',
    is_default_for_type: false
  });

  useEffect(() => {
    loadConnections();
    loadAgentTypes();
  }, []);

  const loadConnections = async () => {
    try {
      const response = await apiClient.get('/dify-management/connections');
      const data = response.data as { connections: DifyConnection[] };
      setConnections(data.connections);
      
      // 选择默认连接
      const defaultConnection = data.connections.find((conn: DifyConnection) => conn.is_default);
      if (defaultConnection) {
        setSelectedConnection(defaultConnection.id);
        loadApps(defaultConnection.id);
      }
    } catch (error) {
      console.error('加载Dify连接失败:', error);
      toast.error('加载Dify连接失败');
    }
  };

  const loadAgentTypes = async () => {
    try {
      const response = await apiClient.get('/dify-management/agent-types');
      setAgentTypes(response.data as AgentType[]);
    } catch (error) {
      console.error('加载Agent类型失败:', error);
    }
  };

  const createConnection = async () => {
    try {
      setLoading(true);
      await apiClient.post('/dify-management/connections', newConnection);
      
      toast.success('Dify连接创建成功');
      setShowNewConnection(false);
      setNewConnection({
        name: '',
        api_base_url: 'http://localhost/v1',
        api_key: '',
        description: '',
        is_default: false
      });
      loadConnections();
    } catch (error: any) {
      const errorMessage = error?.response?.data?.detail || error?.message || '创建连接失败';
      toast.error(`创建连接失败: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  };

  const testConnection = async (connectionId: string) => {
    try {
      const response = await apiClient.post(`/dify-management/connections/${connectionId}/test`);
      const data = response.data as any;
      
      if (data.success) {
        toast.success('连接测试成功');
      } else {
        toast.error(`连接测试失败: ${data.message}`);
      }
    } catch (error) {
      toast.error('连接测试失败');
    }
  };

  const syncApps = async (connectionId: string) => {
    try {
      setLoading(true);
      const response = await apiClient.post(`/dify-management/connections/${connectionId}/sync`);
      const data = response.data as any;
      
      if (data.success) {
        toast.success(data.message);
        loadApps(connectionId);
        loadConnections(); // 更新同步状态
      } else {
        toast.error(`同步失败: ${data.message}`);
      }
    } catch (error) {
      toast.error('同步应用失败');
    } finally {
      setLoading(false);
    }
  };

  const loadApps = async (connectionId: string) => {
    try {
      const response = await apiClient.get(`/dify-management/connections/${connectionId}/apps`);
      const data = response.data as any;
      setApps(data.apps);
    } catch (error) {
      console.error('加载应用列表失败:', error);
      toast.error('加载应用列表失败');
    }
  };

  const configureApp = async () => {
    if (!selectedApp) return;

    try {
      setLoading(true);
      await apiClient.post('/dify-management/apps/configure', {
        connection_id: selectedConnection,
        app_id: selectedApp.id,
        app_name: selectedApp.name,
        app_mode: selectedApp.mode,
        ...appConfig
      });

      toast.success('应用配置成功');
      setShowAppConfig(false);
      setSelectedApp(null);
      setAppConfig({
        agent_type: 'general_chat',
        description: '',
        is_default_for_type: false
      });
    } catch (error: any) {
      const errorMessage = error?.response?.data?.detail || error?.message || '配置应用失败';
      toast.error(`配置应用失败: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Dify连接管理 */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">Dify连接管理</h3>
          <button
            onClick={() => setShowNewConnection(true)}
            className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
          >
            添加连接
          </button>
        </div>

        <div className="space-y-3">
          {connections.map((conn) => (
            <div key={conn.id} className="flex items-center justify-between p-3 border border-gray-200 rounded">
              <div className="flex-1">
                <div className="flex items-center space-x-2">
                  <h4 className="font-medium">{conn.name}</h4>
                  {conn.is_default && (
                    <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded">默认</span>
                  )}
                  {!conn.is_active && (
                    <span className="bg-red-100 text-red-800 text-xs px-2 py-1 rounded">已停用</span>
                  )}
                </div>
                <p className="text-sm text-gray-600">{conn.api_base_url}</p>
                {conn.description && (
                  <p className="text-xs text-gray-500">{conn.description}</p>
                )}
                <p className="text-xs text-gray-500">{conn.sync_status}</p>
                {conn.last_sync_at && (
                  <p className="text-xs text-gray-400">
                    最后同步: {new Date(conn.last_sync_at).toLocaleString()}
                  </p>
                )}
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={() => testConnection(conn.id)}
                  className="bg-gray-500 text-white px-3 py-1 text-sm rounded hover:bg-gray-600"
                >
                  测试
                </button>
                <button
                  onClick={() => syncApps(conn.id)}
                  disabled={loading}
                  className="bg-blue-500 text-white px-3 py-1 text-sm rounded hover:bg-blue-600 disabled:opacity-50"
                >
                  同步
                </button>
                <button
                  onClick={() => {
                    setSelectedConnection(conn.id);
                    loadApps(conn.id);
                  }}
                  className="bg-orange-500 text-white px-3 py-1 text-sm rounded hover:bg-orange-600"
                >
                  选择
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 应用列表和配置 */}
      {selectedConnection && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold mb-4">可用应用配置</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {apps.map((app) => (
              <div key={app.id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    {app.icon && (
                      <img src={app.icon} alt="" className="w-8 h-8 rounded" />
                    )}
                    <div>
                      <h4 className="font-medium">{app.name}</h4>
                      <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                        {app.mode}
                      </span>
                    </div>
                  </div>
                </div>
                
                <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                  {app.description || '暂无描述'}
                </p>
                
                <div className="flex flex-wrap gap-1 mb-3">
                  {app.tags.map((tag, index) => (
                    <span key={index} className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">
                      {tag}
                    </span>
                  ))}
                </div>
                
                <button
                  onClick={() => {
                    setSelectedApp(app);
                    setShowAppConfig(true);
                  }}
                  className="w-full bg-green-500 text-white py-2 rounded hover:bg-green-600"
                >
                  配置为Agent
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 新建连接模态框 */}
      {showNewConnection && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96 max-w-full">
            <h3 className="text-lg font-semibold mb-4">添加Dify连接</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">连接名称 *</label>
                <input
                  type="text"
                  value={newConnection.name}
                  onChange={(e) => setNewConnection({...newConnection, name: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded"
                  placeholder="本地Dify实例"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">API基础URL *</label>
                <input
                  type="text"
                  value={newConnection.api_base_url}
                  onChange={(e) => setNewConnection({...newConnection, api_base_url: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded"
                  placeholder="http://localhost/v1"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">API密钥 *</label>
                <input
                  type="password"
                  value={newConnection.api_key}
                  onChange={(e) => setNewConnection({...newConnection, api_key: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded"
                  placeholder="app-xxxxxxxxxxxx"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">描述</label>
                <textarea
                  value={newConnection.description}
                  onChange={(e) => setNewConnection({...newConnection, description: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded"
                  rows={2}
                />
              </div>
              
              <div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={newConnection.is_default}
                    onChange={(e) => setNewConnection({...newConnection, is_default: e.target.checked})}
                    className="mr-2"
                  />
                  设为默认连接
                </label>
              </div>
            </div>
            
            <div className="flex justify-end mt-4 space-x-2">
              <button
                onClick={() => setShowNewConnection(false)}
                className="px-4 py-2 bg-gray-300 text-gray-700 rounded hover:bg-gray-400"
              >
                取消
              </button>
              <button
                onClick={createConnection}
                disabled={loading || !newConnection.name || !newConnection.api_key}
                className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
              >
                {loading ? '创建中...' : '创建'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 配置应用模态框 */}
      {showAppConfig && selectedApp && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96 max-w-full">
            <h3 className="text-lg font-semibold mb-4">配置应用: {selectedApp.name}</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Agent类型 *</label>
                <select
                  value={appConfig.agent_type}
                  onChange={(e) => setAppConfig({...appConfig, agent_type: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded"
                >
                  {agentTypes.map((type) => (
                    <option key={type.value} value={type.value}>
                      {type.label} - {type.description}
                    </option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">描述</label>
                <textarea
                  value={appConfig.description}
                  onChange={(e) => setAppConfig({...appConfig, description: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded"
                  rows={3}
                  placeholder="描述这个Agent的具体用途..."
                />
              </div>
              
              <div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={appConfig.is_default_for_type}
                    onChange={(e) => setAppConfig({...appConfig, is_default_for_type: e.target.checked})}
                    className="mr-2"
                  />
                  设为该类型的默认Agent
                </label>
              </div>
            </div>
            
            <div className="flex justify-end mt-4 space-x-2">
              <button
                onClick={() => setShowAppConfig(false)}
                className="px-4 py-2 bg-gray-300 text-gray-700 rounded hover:bg-gray-400"
              >
                取消
              </button>
              <button
                onClick={configureApp}
                disabled={loading}
                className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50"
              >
                {loading ? '配置中...' : '配置'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}; 