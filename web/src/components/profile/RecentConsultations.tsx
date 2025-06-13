'use client';

import { ConsultationHistoryItem } from '@/types/chat';

interface RecentConsultationsProps {
  conversationId?: string;
  currentConsultation?: ConsultationHistoryItem;
  onViewAllHistory: () => void;
  onOpenHistoryDetail: (history: ConsultationHistoryItem) => void;
  onCreateSummary: () => void;
}

export function RecentConsultations({ 
  conversationId,
  currentConsultation, 
  onViewAllHistory, 
  onOpenHistoryDetail,
  onCreateSummary 
}: RecentConsultationsProps) {
  
  // 如果有当前会话但没有总结，显示创建提示
  if (conversationId && !currentConsultation) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-4">
        <div className="flex justify-between items-center mb-3">
          <h4 className="font-medium text-gray-700">咨询总结</h4>
          <button 
            className="px-3 py-1 text-sm bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition-colors"
            onClick={onCreateSummary}
          >
            创建总结
          </button>
        </div>
        
        <div className="text-center py-6 text-gray-500">
          <svg className="h-8 w-8 text-gray-300 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
          </svg>
          <p className="text-sm mb-3">本次咨询尚未创建总结</p>
          <p className="text-xs text-gray-400">点击上方按钮创建详细的咨询总结</p>
        </div>
      </div>
    );
  }

  // 如果有总结，显示总结内容
  if (currentConsultation) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-4">
        <div className="flex justify-between items-center mb-3">
          <h4 className="font-medium text-gray-700">咨询总结</h4>
          <div className="flex items-center space-x-2">
            <button 
              className="text-xs text-orange-500 hover:text-orange-600"
              onClick={onViewAllHistory}
            >
              查看全部
            </button>
          </div>
        </div>
        
        <div 
          className="rounded-lg bg-gray-50 p-3 text-sm cursor-pointer hover:bg-gray-100 transition-colors"
          onClick={() => onOpenHistoryDetail(currentConsultation)}
        >
          <div className="mb-2 flex justify-between items-start">
            <div className="flex items-center">
              <span className="font-medium text-gray-800">{currentConsultation.type}</span>
              {currentConsultation.satisfaction_rating && (
                <div className="ml-2 flex items-center">
                  <span className="text-xs text-gray-500">满意度:</span>
                  <div className="ml-1 flex">
                    {[1,2,3,4,5].map(star => (
                      <svg 
                        key={star}
                        className={`w-3 h-3 ${star <= currentConsultation.satisfaction_rating! ? 'text-yellow-400' : 'text-gray-300'}`}
                        fill="currentColor" 
                        viewBox="0 0 20 20"
                      >
                        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                      </svg>
                    ))}
                  </div>
                </div>
              )}
            </div>
            <span className="text-gray-500 text-xs">{currentConsultation.date}</span>
          </div>
          
          <div className="mb-2">
            <p className="text-gray-600 break-words line-clamp-2">{currentConsultation.description}</p>
          </div>
          
          <div className="flex justify-between items-center text-xs text-gray-500">
            {currentConsultation.duration_minutes && (
              <span>时长: {currentConsultation.duration_minutes}分钟</span>
            )}
            <span className="text-orange-500">点击查看详情 →</span>
          </div>
        </div>
      </div>
    );
  }

  // 如果没有会话ID，显示空状态
  return null;
} 