'use client';

import { useState, useEffect } from 'react';
import AppLayout from '@/components/layout/AppLayout';

export default function DoctorPlansPage() {
  return (
    <AppLayout requiredRole="doctor">
      <div className="p-6">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-800">治疗方案</h1>
          <p className="text-gray-600">管理和创建治疗方案</p>
        </div>
        
        {/* 这里放原来的治疗方案内容 */}
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-500">治疗方案管理功能正在开发中...</p>
        </div>
      </div>
    </AppLayout>
  );
} 