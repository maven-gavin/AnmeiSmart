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
  
  // 使用自定义hooks管理状态和逻辑
  const { profile, consultationHistory, currentConsultation, loading, error } = useCustomerProfile(customerId, conversationId);
  const {
    showHistoryModal,
    selectedHistory,
    showMessagesPreview,
    historyMessages,
    loadingMessages,
    openHistoryDetail,
    closeHistoryDetail,
    viewHistoryConversation,
    previewHistoryMessages,
    toggleMessagesPreview
  } = useConsultationModal(customerId);

  // 切换到历史标签页
  const handleViewAllHistory = () => {
    setActiveTab('history');
  };

  // 创建咨询总结
  const handleCreateSummary = () => {
    // TODO: 实现创建咨询总结的逻辑
    console.log('创建咨询总结');
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
            onPreviewMessages={previewHistoryMessages}
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
        onPreviewMessages={previewHistoryMessages}
        onViewConversation={viewHistoryConversation}
        messages={historyMessages}
        showMessagesPreview={showMessagesPreview}
        loadingMessages={loadingMessages}
        onTogglePreview={toggleMessagesPreview}
      />
    </div>
  );
} 