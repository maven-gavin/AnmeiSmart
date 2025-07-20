'use client';

import { useState, useEffect } from 'react';
import AppLayout from '@/components/layout/AppLayout';

export default function CustomerTreatmentsPage() {
  return (
    <AppLayout requiredRole="customer">
      <div className="p-6">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-800">治疗记录</h1>
          <p className="text-gray-600">查看我的治疗记录</p>
        </div>
        
        {/* 这里放原来的客户治疗记录内容 */}
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-500">我的治疗记录正在开发中...</p>
        </div>
      </div>
    </AppLayout>
  );
} 