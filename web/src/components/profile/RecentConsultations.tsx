'use client';

import { ConsultationHistoryItem } from '@/types/chat';

interface RecentConsultationsProps {
  currentConsultation?: ConsultationHistoryItem;
  onViewAllHistory: () => void;
  onOpenHistoryDetail: (history: ConsultationHistoryItem) => void;
}

export function RecentConsultations({ currentConsultation, onViewAllHistory, onOpenHistoryDetail }: RecentConsultationsProps) {
  if (!currentConsultation) {
    return null;
  }

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4">
      <div className="flex justify-between items-center mb-3">
        <h4 className="font-medium text-gray-700">咨询总结</h4>
        <button 
          className="text-xs text-orange-500 hover:text-orange-600"
          onClick={onViewAllHistory}
        >
          查看全部
        </button>
      </div>
      <div className="space-y-3">
          <div 
            key={currentConsultation.id}
            className="rounded-lg bg-gray-50 p-3 text-sm cursor-pointer hover:bg-gray-100"
            onClick={() => onOpenHistoryDetail(currentConsultation)}
          >
            <div className="mb-1 flex justify-between">
              <span className="font-medium">{currentConsultation.type}</span>
              <span className="text-gray-500">{currentConsultation.date}</span>
            </div>
            <p className="text-gray-600 break-words line-clamp-2">{currentConsultation.description}</p>
          </div>
      </div>
    </div>
  );
} 