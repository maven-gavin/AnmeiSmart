'use client';

import { ConsultationHistoryItem } from '@/types/chat';

interface ConsultationHistoryProps {
  consultationHistory: ConsultationHistoryItem[];
  onOpenHistoryDetail: (history: ConsultationHistoryItem) => void;
  onViewConversation: (conversationId: string) => void;
}

export function ConsultationHistory({ 
  consultationHistory, 
  onOpenHistoryDetail, 
  onViewConversation 
}: ConsultationHistoryProps) {
  if (!consultationHistory || consultationHistory.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-gray-500">
        <svg className="h-12 w-12 text-gray-300 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <p>暂无咨询历史</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-800">咨询历史</h3>
        <span className="text-sm text-gray-500">共 {consultationHistory.length} 条记录</span>
      </div>
      
      <div className="space-y-3">
        {consultationHistory.map((history, index) => (
          <div 
            key={index}
            className="rounded-lg border border-gray-200 bg-white p-4 cursor-pointer hover:border-orange-200 hover:shadow-sm transition-all"
            onClick={() => onOpenHistoryDetail(history)}
          >
            <div className="mb-2 flex justify-between items-center">
              <div className="flex items-center">
                <span className="text-sm font-medium">{history.date}</span>
                <span className="ml-3 rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600">
                  {history.type}
                </span>
              </div>
              <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </div>
            <p className="text-sm text-gray-600 line-clamp-2">{history.description}</p>
            {history.id && (
              <div className="mt-2 flex justify-end">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onViewConversation(history.id);
                  }}
                  className="text-xs text-orange-500 hover:text-orange-600 flex items-center"
                >
                  <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                  </svg>
                  选为当前会话
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
} 