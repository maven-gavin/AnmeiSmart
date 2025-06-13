'use client';

import { useState } from 'react';
import { useCustomerProfile } from '@/hooks/useCustomerProfile';
import { useConsultationModal } from '@/hooks/useConsultationModal';
import { ProfileTabs } from './ProfileTabs';
import { CustomerBasicInfo } from './CustomerBasicInfo';
import { ConsultationHistory } from './ConsultationHistory';
import { RiskWarnings } from './RiskWarnings';
import { ConsultationModal } from './ConsultationModal';

interface CustomerProfileProps {
  customerId: string;
  conversationId?: string;
}

export default function CustomerProfile({ customerId, conversationId }: CustomerProfileProps) {
  const [activeTab, setActiveTab] = useState<'basic' | 'history' | 'risk'>('basic');
  const [showCreateSummaryModal, setShowCreateSummaryModal] = useState(false);
  
  // 使用自定义hooks管理状态和逻辑
  const { profile, consultationHistory, currentConsultation, loading, error } = useCustomerProfile(customerId, conversationId);
  const {
    showHistoryModal,
    selectedHistory,
    openHistoryDetail,
    closeHistoryDetail,
    viewHistoryConversation,
  } = useConsultationModal(customerId);

  // 切换到历史标签页
  const handleViewAllHistory = () => {
    setActiveTab('history');
  };

  // 创建咨询总结
  const handleCreateSummary = () => {
    console.log('🎯 创建咨询总结被调用, conversationId:', conversationId);
    if (conversationId) {
      setShowCreateSummaryModal(true);
    } else {
      console.error('❌ 没有conversationId，无法创建总结');
    }
  };

  // 保存咨询总结
  const handleSaveSummary = async (summaryData: any) => {
    console.log('💾 CustomerProfile handleSaveSummary 被调用');
    console.log('📋 summaryData:', summaryData);
    console.log('💬 conversationId:', conversationId);
    
    try {
      // TODO: 调用API保存咨询总结
      // 这里应该调用真实的API接口
      console.log('📤 模拟保存咨询总结到API...');
      
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      console.log('✅ 咨询总结保存成功');
    } catch (error) {
      console.error('❌ 保存咨询总结失败:', error);
      throw error;
    }
  };

  // AI生成咨询总结
  const handleAIGenerate = async (conversationId: string) => {
    console.log('🤖 AI生成咨询总结 conversationId:', conversationId);
    
    try {
      // TODO: 调用AI生成接口
      console.log('📤 模拟AI生成咨询总结...');
      
      // 模拟AI生成的数据
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      const mockAIData = {
        main_issues: ['客户咨询AI生成的主要问题'],
        solutions: ['AI建议的解决方案'],
        follow_up_plan: ['AI制定的跟进计划'],
        satisfaction_rating: 4,
        additional_notes: 'AI生成的补充备注',
        tags: ['AI', '自动生成']
      };
      
      console.log('✅ AI生成完成:', mockAIData);
      return mockAIData;
    } catch (error) {
      console.error('❌ AI生成失败:', error);
      throw error;
    }
  };

  // 加载状态
  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-orange-500 border-t-transparent"></div>
      </div>
    );
  }

  // 错误状态
  if (error) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-gray-500">{error}</p>
      </div>
    );
  }

  // 没有找到客户信息
  if (!profile) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-gray-500">没有找到客户信息</p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* 标签页导航 */}
      <ProfileTabs
        activeTab={activeTab}
        onTabChange={setActiveTab}
        consultationCount={consultationHistory.length}
        riskCount={profile.riskNotes?.length || 0}
      />
      
      {/* 内容区域 */}
      <div className="flex-1 overflow-y-auto p-4">
        {activeTab === 'basic' && (
          <CustomerBasicInfo
            profile={profile}
            currentConsultation={currentConsultation}
            onViewAllHistory={handleViewAllHistory}
            onOpenHistoryDetail={openHistoryDetail}
            onCreateSummary={handleCreateSummary}
          />
        )}
        
        {activeTab === 'history' && (
          <ConsultationHistory
            consultationHistory={consultationHistory}
            onOpenHistoryDetail={openHistoryDetail}
            onViewConversation={viewHistoryConversation}
          />
        )}
        
        {activeTab === 'risk' && (
          <RiskWarnings riskNotes={profile.riskNotes} />
        )}
      </div>
      
      {/* 历史咨询详情弹窗 */}
      <ConsultationModal
        isOpen={showHistoryModal}
        consultation={selectedHistory}
        onClose={closeHistoryDetail}
        onSaveSummary={handleSaveSummary}
        onAIGenerate={handleAIGenerate}
      />
    </div>
  );
} 