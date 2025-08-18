'use client';

import { useAuthContext } from '@/contexts/AuthContext';
import AppLayout from '@/components/layout/AppLayout';
import { MCPConfigPanel } from '@/components/settings/MCPConfigPanel';

export default function MCPConfigPage() {
  const { user } = useAuthContext();

  return (
    <AppLayout requiredRole={user?.currentRole}>
      <div className="container mx-auto px-4 py-6">
        <h1 className="mb-6 text-2xl font-bold text-gray-800">MCP配置管理</h1>
        
        <div className="space-y-6">
          <MCPConfigPanel />
        </div>
      </div>
    </AppLayout>
  );
}
