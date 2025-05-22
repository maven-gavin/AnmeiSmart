'use client';

import { useState, useEffect } from 'react';
import { type CustomerProfile } from '@/types/chat';
import { getCustomerConsultationHistory } from '@/service/chatService';
import { Button } from '@/components/ui/button';

interface HistoryConsultationProps {
  customerId: string;
  onClose: () => void;
}

export default function HistoryConsultation({ customerId, onClose }: HistoryConsultationProps) {
  const [consultationHistory, setConsultationHistory] = useState<CustomerProfile['consultationHistory']>([]);
  const [loading, setLoading] = useState(true);
  const [selectedPeriod, setSelectedPeriod] = useState<'all' | '1month' | '3months' | '6months'>('all');
  const [selectedHistory, setSelectedHistory] = useState<CustomerProfile['consultationHistory'][0] | null>(null);
  
  // 获取历史咨询记录
  useEffect(() => {
    const loadConsultationHistory = async () => {
      const history = await getCustomerConsultationHistory(customerId);
      setConsultationHistory(await history);
    };
    
    if (customerId) {
      loadConsultationHistory();
    }
  }, [customerId]);
  
  // 根据时间筛选历史记录
  const filteredHistory = () => {
    if (selectedPeriod === 'all') {
      return consultationHistory;
    }
    
    const now = new Date();
    let monthsAgo = 1;
    
    if (selectedPeriod === '3months') {
      monthsAgo = 3;
    } else if (selectedPeriod === '6months') {
      monthsAgo = 6;
    }
    
    const cutoffDate = new Date(now.setMonth(now.getMonth() - monthsAgo));
    
    return consultationHistory.filter(history => {
      const historyDate = new Date(history.date);
      return historyDate >= cutoffDate;
    });
  };
  
  // 按咨询类型分组
  const groupedHistory = () => {
    const grouped: Record<string, CustomerProfile['consultationHistory']> = {};
    
    filteredHistory().forEach(history => {
      if (!grouped[history.type]) {
        grouped[history.type] = [];
      }
      grouped[history.type].push(history);
    });
    
    return grouped;
  };
  
  // 查看详情
  const viewDetails = (history: CustomerProfile['consultationHistory'][0]) => {
    setSelectedHistory(history);
  };
  
  // 关闭详情
  const closeDetails = () => {
    setSelectedHistory(null);
  };
  
  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
        <div className="bg-white rounded-lg shadow-xl p-8 flex flex-col items-center">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-orange-500 border-t-transparent"></div>
          <p className="mt-4 text-gray-600">加载历史咨询记录...</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] flex flex-col">
        <div className="p-4 border-b border-gray-200 flex justify-between items-center">
          <h3 className="text-xl font-medium">历史咨询记录</h3>
          <button 
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        {/* 内容区域 */}
        <div className="flex flex-col md:flex-row flex-1 overflow-hidden">
          {/* 左侧列表 */}
          <div className={`w-full ${selectedHistory ? 'hidden md:block md:w-1/2 md:border-r' : ''} border-gray-200 overflow-y-auto`}>
            {/* 筛选器 */}
            <div className="p-4 border-b border-gray-200 bg-gray-50">
              <div className="text-sm font-medium text-gray-700 mb-2">时间筛选</div>
              <div className="flex flex-wrap gap-2">
                <button 
                  className={`px-3 py-1 rounded-full text-xs font-medium ${
                    selectedPeriod === 'all' 
                      ? 'bg-orange-500 text-white' 
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                  onClick={() => setSelectedPeriod('all')}
                >
                  全部
                </button>
                <button 
                  className={`px-3 py-1 rounded-full text-xs font-medium ${
                    selectedPeriod === '1month' 
                      ? 'bg-orange-500 text-white' 
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                  onClick={() => setSelectedPeriod('1month')}
                >
                  近1个月
                </button>
                <button 
                  className={`px-3 py-1 rounded-full text-xs font-medium ${
                    selectedPeriod === '3months' 
                      ? 'bg-orange-500 text-white' 
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                  onClick={() => setSelectedPeriod('3months')}
                >
                  近3个月
                </button>
                <button 
                  className={`px-3 py-1 rounded-full text-xs font-medium ${
                    selectedPeriod === '6months' 
                      ? 'bg-orange-500 text-white' 
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                  onClick={() => setSelectedPeriod('6months')}
                >
                  近6个月
                </button>
              </div>
            </div>
            
            {/* 记录列表 */}
            <div className="p-4">
              {filteredHistory().length > 0 ? (
                <div className="space-y-6">
                  {Object.entries(groupedHistory()).map(([type, histories]) => (
                    <div key={type} className="space-y-2">
                      <h4 className="text-sm font-medium text-gray-500 flex items-center">
                        <span className="inline-block w-2 h-2 bg-orange-500 rounded-full mr-2"></span>
                        {type} ({histories.length})
                      </h4>
                      
                      <div className="space-y-2 pl-4">
                        {histories.map((history, index) => (
                          <div 
                            key={index}
                            className={`p-3 border rounded-lg cursor-pointer transition-all ${
                              selectedHistory === history 
                                ? 'border-orange-500 bg-orange-50' 
                                : 'border-gray-200 bg-white hover:border-orange-200'
                            }`}
                            onClick={() => viewDetails(history)}
                          >
                            <div className="flex justify-between items-center mb-1">
                              <span className="text-sm font-medium">{history.date}</span>
                            </div>
                            <p className="text-xs text-gray-600 line-clamp-2">{history.description}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-8 text-gray-500">
                  <svg className="h-12 w-12 text-gray-300 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <p className="text-sm">所选时间段内暂无咨询记录</p>
                </div>
              )}
            </div>
          </div>
          
          {/* 右侧详情 */}
          {selectedHistory ? (
            <div className="w-full md:w-1/2 flex flex-col overflow-hidden">
              <div className="p-4 border-b border-gray-200 bg-gray-50 flex justify-between items-center md:hidden">
                <button 
                  className="flex items-center text-sm text-gray-600"
                  onClick={closeDetails}
                >
                  <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                  </svg>
                  返回列表
                </button>
              </div>
              
              <div className="p-4 flex-1 overflow-y-auto">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <div className="flex items-center">
                      <span className="text-lg font-medium">{selectedHistory.type}</span>
                      <span className="ml-2 px-2 py-0.5 bg-orange-100 text-orange-700 rounded-full text-xs">
                        {selectedHistory.date}
                      </span>
                    </div>
                  </div>
                </div>
                
                <div className="bg-gray-50 rounded-lg p-4 whitespace-pre-wrap text-gray-700">
                  {selectedHistory.description}
                </div>
                
                {/* 添加一些可能的相关操作 */}
                <div className="mt-6 space-y-4">
                  <div className="bg-blue-50 p-3 rounded-lg border border-blue-200">
                    <h4 className="text-sm font-medium text-blue-700 mb-1">相关资料</h4>
                    <p className="text-xs text-blue-600">
                      可以在此处添加与该次咨询相关的资料、照片或报告等。
                    </p>
                  </div>
                  
                  <div className="bg-green-50 p-3 rounded-lg border border-green-200">
                    <h4 className="text-sm font-medium text-green-700 mb-1">后续跟进</h4>
                    <p className="text-xs text-green-600">
                      可以在此处添加后续跟进计划、预约提醒或其他指导建议。
                    </p>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="hidden md:flex w-1/2 items-center justify-center p-8 bg-gray-50 text-gray-500">
              <div className="text-center">
                <svg className="h-16 w-16 text-gray-300 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
                <p>选择左侧记录查看详情</p>
              </div>
            </div>
          )}
        </div>
        
        <div className="p-4 border-t border-gray-200 flex justify-end">
          <Button onClick={onClose}>关闭</Button>
        </div>
      </div>
    </div>
  );
} 