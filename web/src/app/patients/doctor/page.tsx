'use client';

import { useState, useEffect } from 'react';
import AppLayout from '@/components/layout/AppLayout';

export default function DoctorPatientsPage() {
  return (
    <AppLayout requiredRole="doctor">
      <div className="p-6">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-800">患者管理</h1>
          <p className="text-gray-600">管理和查看患者信息</p>
        </div>
        
        {/* 这里放原来的患者管理内容 */}
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-500">患者管理功能正在开发中...</p>
        </div>
      </div>
    </AppLayout>
  );
} 