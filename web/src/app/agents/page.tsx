'use client';

import { useAuthContext } from '@/contexts/AuthContext';
import AppLayout from '@/components/layout/AppLayout';
import DifyConfigPanel from '@/components/settings/DifyConfigPanel';
import { useDifyConfigs } from '@/hooks/useDifyConfigs';

export default function AgentsConfigPage() {
  const { user } = useAuthContext();
  
  const {
    configs: difyConfigs,
    isLoading: isDifyLoading,
    isTestingConnection,
    createConfig: createDifyConfig,
    updateConfig: updateDifyConfig,
    deleteConfig: deleteDifyConfig,
    testConnection: testDifyConnection
  } = useDifyConfigs();

  return (
    <AppLayout requiredRole={user?.currentRole}>
      <div className="container mx-auto px-4 py-6">
        <h1 className="mb-6 text-2xl font-bold text-gray-800">智能体配置管理</h1>
        
        <div className="space-y-6">
          {isDifyLoading ? (
            <div className="flex h-64 items-center justify-center">
              <div className="text-center">
                <div className="mb-4 h-8 w-8 animate-spin rounded-full border-b-2 border-t-2 border-orange-500"></div>
                <p className="text-gray-600">加载智能体配置...</p>
              </div>
            </div>
          ) : (
            <DifyConfigPanel
              configs={difyConfigs}
              onCreateConfig={createDifyConfig}
              onUpdateConfig={updateDifyConfig}
              onDeleteConfig={deleteDifyConfig}
              onTestConnection={testDifyConnection}
              isTestingConnection={isTestingConnection}
            />
          )}
        </div>
      </div>
    </AppLayout>
  );
}
