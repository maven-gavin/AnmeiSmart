'use client';

import { CustomerProfile, ConsultationHistoryItem } from '@/types/chat';
import { RecentConsultations } from './RecentConsultations';

interface CustomerBasicInfoProps {
  profile: CustomerProfile;
  currentConsultation?: ConsultationHistoryItem;
  onViewAllHistory: () => void;
  onOpenHistoryDetail: (history: ConsultationHistoryItem) => void;
  onCreateSummary: () => void;
}

export function CustomerBasicInfo({ profile, currentConsultation, onViewAllHistory, onOpenHistoryDetail, onCreateSummary }: CustomerBasicInfoProps) {
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-800">客户档案</h3>
      
      {/* 基本信息卡片 */}
      <div className="rounded-lg border border-gray-200 bg-white p-4">
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div className="text-gray-500">姓名</div>
          <div className="font-medium">{profile.basicInfo.name}</div>
          
          <div className="text-gray-500">年龄</div>
          <div className="font-medium">{profile.basicInfo.age}岁</div>
          
          <div className="text-gray-500">性别</div>
          <div className="font-medium">{profile.basicInfo.gender === 'female' ? '女' : '男'}</div>
          
          <div className="text-gray-500">联系方式</div>
          <div className="font-medium break-all">{profile.basicInfo.phone}</div>
        </div>
      </div>
      
      {/* 风险概览 */}
      {profile.riskNotes && profile.riskNotes.length > 0 && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4">
          <h4 className="mb-2 font-medium text-red-700 flex items-center">
            <svg className="h-4 w-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            重要风险提示
          </h4>
          <ul className="text-sm text-red-700 space-y-1 list-disc list-inside">
            {profile.riskNotes.map((risk, index) => (
              <li key={index}>{risk.type}: {risk.description}</li>
            ))}
          </ul>
        </div>
      )}
      
      {/* 最近咨询 */}
      <RecentConsultations
        currentConsultation={currentConsultation}
        onViewAllHistory={onViewAllHistory}
        onOpenHistoryDetail={onOpenHistoryDetail}
        onCreateSummary={onCreateSummary}
      />
    </div>
  );
} 