'use client';

import Link from 'next/link';
import ConsultantNavigation from '@/components/ui/ConsultantNavigation';
import AppLayout from '../layout/AppLayout';
import { useAuthContext } from '@/contexts/AuthContext';

export default function ConsultantDashboard() {
  const { user } = useAuthContext();
  return (
    <AppLayout requiredRole={user?.currentRole}>
    <div className="container mx-auto p-6">
      <h1 className="mb-6 text-2xl font-bold text-gray-800">欢迎使用顾问端</h1>
      
      <ConsultantNavigation />
      
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
        <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <h2 className="mb-4 text-lg font-semibold">智能客服</h2>
          <p className="mb-4 text-gray-600">多模态智能沟通，AI自动回复与顾问介入支持</p>
          <p className="text-sm text-gray-500">
            通过AI赋能的客服系统，提高沟通效率，更好地了解客户需求。系统会自动回复常见问题，
            需要时您可以随时介入对话。所有客户沟通记录将被保存，便于后续分析和跟进。
          </p>
        </div>
        
        <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <h2 className="mb-4 text-lg font-semibold">术前模拟</h2>
          <p className="mb-4 text-gray-600">上传照片，生成多角度术效果模拟图像</p>
          <p className="text-sm text-gray-500">
            通过先进的AI图像处理技术，为客户提供个性化的术前效果模拟。只需上传照片，
            调整参数，系统将生成逼真的术后效果预览，帮助客户做出更明智的决策。
          </p>
        </div>
        
        <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <h2 className="mb-4 text-lg font-semibold">方案推荐</h2>
          <p className="mb-4 text-gray-600">根据客户需求生成个性化方案推荐</p>
          <p className="text-sm text-gray-500">
            基于客户的具体需求、预算和期望，系统协助您创建个性化的方案建议。
            包括项目组合、费用估算、治疗周期和恢复时间，为客户提供全面的信息，
            帮助他们做出最适合自己的选择。
          </p>
        </div>
      </div>
    </div>
    </AppLayout>
  );
} 