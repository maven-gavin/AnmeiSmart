'use client';

import { useState, useEffect } from 'react';
import { type CustomerProfile } from '@/types/chat';
import { getCustomerProfile } from '@/service/chatService';
import { Button } from '@/components/ui/button';

interface RiskNotesViewerProps {
  customerId: string;
  onClose: () => void;
}

type RiskSeverity = 'all' | 'high' | 'medium' | 'low';

export default function RiskNotesViewer({ customerId, onClose }: RiskNotesViewerProps) {
  const [profile, setProfile] = useState<CustomerProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [filterSeverity, setFilterSeverity] = useState<RiskSeverity>('all');
  const [selectedRisk, setSelectedRisk] = useState<CustomerProfile['riskNotes'][0] | null>(null);
  
  // 获取客户档案
  useEffect(() => {
    const fetchProfile = async () => {
      setLoading(true);
      try {
        // 模拟API调用延迟
        await new Promise(resolve => setTimeout(resolve, 300));
        
        // 获取客户档案
        const customerProfile = getCustomerProfile(customerId);
        setProfile(customerProfile);
      } catch (error) {
        console.error('获取客户档案失败:', error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchProfile();
  }, [customerId]);
  
  // 过滤风险
  const filteredRisks = () => {
    if (!profile || !profile.riskNotes) return [];
    
    if (filterSeverity === 'all') {
      return profile.riskNotes;
    }
    
    return profile.riskNotes.filter(risk => risk.level === filterSeverity);
  };
  
  // 风险等级标签
  const getRiskLevelLabel = (level: string) => {
    switch (level) {
      case 'high':
        return '高风险';
      case 'medium':
        return '中风险';
      case 'low':
        return '低风险';
      default:
        return '未知';
    }
  };
  
  // 风险等级颜色
  const getRiskLevelColor = (level: string) => {
    switch (level) {
      case 'high':
        return 'bg-red-100 text-red-700 border-red-200';
      case 'medium':
        return 'bg-orange-100 text-orange-700 border-orange-200';
      case 'low':
        return 'bg-yellow-100 text-yellow-700 border-yellow-200';
      default:
        return 'bg-gray-100 text-gray-700 border-gray-200';
    }
  };
  
  // 查看风险详情
  const viewRiskDetails = (risk: CustomerProfile['riskNotes'][0]) => {
    setSelectedRisk(risk);
  };
  
  // 关闭风险详情
  const closeRiskDetails = () => {
    setSelectedRisk(null);
  };
  
  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
        <div className="bg-white rounded-lg shadow-xl p-8 flex flex-col items-center">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-orange-500 border-t-transparent"></div>
          <p className="mt-4 text-gray-600">加载风险提示...</p>
        </div>
      </div>
    );
  }
  
  if (!profile) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
        <div className="bg-white rounded-lg shadow-xl p-8">
          <p className="text-gray-700">未找到客户信息</p>
          <div className="mt-4 flex justify-end">
            <Button onClick={onClose}>关闭</Button>
          </div>
        </div>
      </div>
    );
  }
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] flex flex-col">
        <div className="p-4 border-b border-gray-200 flex justify-between items-center">
          <div>
            <h3 className="text-xl font-medium">风险提示</h3>
            <p className="text-sm text-gray-500 mt-1">客户：{profile.basicInfo.name}</p>
          </div>
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
          <div className={`w-full ${selectedRisk ? 'hidden md:block md:w-1/2 md:border-r' : ''} border-gray-200 overflow-y-auto`}>
            {/* 筛选器 */}
            <div className="p-4 border-b border-gray-200 bg-gray-50">
              <div className="text-sm font-medium text-gray-700 mb-2">风险等级筛选</div>
              <div className="flex flex-wrap gap-2">
                <button 
                  className={`px-3 py-1 rounded-full text-xs font-medium ${
                    filterSeverity === 'all' 
                      ? 'bg-gray-700 text-white' 
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                  onClick={() => setFilterSeverity('all')}
                >
                  全部
                </button>
                <button 
                  className={`px-3 py-1 rounded-full text-xs font-medium ${
                    filterSeverity === 'high' 
                      ? 'bg-red-500 text-white' 
                      : 'bg-red-50 text-red-700 hover:bg-red-100'
                  }`}
                  onClick={() => setFilterSeverity('high')}
                >
                  高风险
                </button>
                <button 
                  className={`px-3 py-1 rounded-full text-xs font-medium ${
                    filterSeverity === 'medium' 
                      ? 'bg-orange-500 text-white' 
                      : 'bg-orange-50 text-orange-700 hover:bg-orange-100'
                  }`}
                  onClick={() => setFilterSeverity('medium')}
                >
                  中风险
                </button>
                <button 
                  className={`px-3 py-1 rounded-full text-xs font-medium ${
                    filterSeverity === 'low' 
                      ? 'bg-yellow-500 text-white' 
                      : 'bg-yellow-50 text-yellow-700 hover:bg-yellow-100'
                  }`}
                  onClick={() => setFilterSeverity('low')}
                >
                  低风险
                </button>
              </div>
            </div>
            
            {/* 风险列表 */}
            <div className="p-4">
              {filteredRisks().length > 0 ? (
                <div className="space-y-3">
                  {filteredRisks().map((risk, index) => (
                    <div 
                      key={index}
                      className={`p-3 border rounded-lg cursor-pointer transition-all ${
                        selectedRisk === risk 
                          ? 'border-orange-500 bg-orange-50' 
                          : `border-gray-200 hover:border-${risk.level === 'high' ? 'red' : risk.level === 'medium' ? 'orange' : 'yellow'}-300`
                      }`}
                      onClick={() => viewRiskDetails(risk)}
                    >
                      <div className="flex justify-between items-center mb-2">
                        <span className="font-medium">{risk.type}</span>
                        <span className={`px-2 py-0.5 text-xs rounded-full ${
                          risk.level === 'high' 
                            ? 'bg-red-100 text-red-700' 
                            : risk.level === 'medium'
                            ? 'bg-orange-100 text-orange-700'
                            : 'bg-yellow-100 text-yellow-700'
                        }`}>
                          {getRiskLevelLabel(risk.level)}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 line-clamp-2">{risk.description}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-12 text-gray-500">
                  <svg className="h-12 w-12 text-gray-300 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  {filterSeverity === 'all' ? (
                    <p>未发现风险记录</p>
                  ) : (
                    <p>未发现{getRiskLevelLabel(filterSeverity)}记录</p>
                  )}
                </div>
              )}
            </div>
          </div>
          
          {/* 右侧详情 */}
          {selectedRisk ? (
            <div className="w-full md:w-1/2 flex flex-col overflow-hidden">
              <div className="p-4 border-b border-gray-200 bg-gray-50 flex justify-between items-center md:hidden">
                <button 
                  className="flex items-center text-sm text-gray-600"
                  onClick={closeRiskDetails}
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
                      <span className="text-lg font-medium">{selectedRisk.type}</span>
                      <span className={`ml-2 px-2 py-0.5 text-xs rounded-full ${
                        selectedRisk.level === 'high' 
                          ? 'bg-red-100 text-red-700' 
                          : selectedRisk.level === 'medium'
                          ? 'bg-orange-100 text-orange-700'
                          : 'bg-yellow-100 text-yellow-700'
                      }`}>
                        {getRiskLevelLabel(selectedRisk.level)}
                      </span>
                    </div>
                  </div>
                </div>
                
                <div className={`rounded-lg p-4 whitespace-pre-wrap ${getRiskLevelColor(selectedRisk.level)}`}>
                  {selectedRisk.description}
                </div>
                
                {/* 风险应对指南 */}
                <div className="mt-6 space-y-4">
                  <h4 className="font-medium text-gray-700">风险应对指南</h4>
                  
                  {selectedRisk.level === 'high' && (
                    <div className="bg-red-50 p-4 rounded-lg border border-red-200">
                      <h5 className="text-sm font-medium text-red-700 mb-2">高风险应对措施</h5>
                      <ul className="list-disc list-inside text-sm text-red-600 space-y-2">
                        <li>立即通知主治医生，评估是否适合进行医美项目</li>
                        <li>根据具体风险类型，准备应急预案和应对方案</li>
                        <li>考虑对治疗方案进行调整或推迟施术</li>
                        <li>确保客户已完全知情并签署风险告知书</li>
                        <li>准备替代方案供客户选择</li>
                      </ul>
                    </div>
                  )}
                  
                  {selectedRisk.level === 'medium' && (
                    <div className="bg-orange-50 p-4 rounded-lg border border-orange-200">
                      <h5 className="text-sm font-medium text-orange-700 mb-2">中度风险应对措施</h5>
                      <ul className="list-disc list-inside text-sm text-orange-600 space-y-2">
                        <li>咨询相关专业医生的建议，评估风险影响</li>
                        <li>调整治疗方案以降低风险</li>
                        <li>对客户进行详细风险说明</li>
                        <li>密切监控治疗过程中的反应</li>
                        <li>考虑采用更保守的治疗方式</li>
                      </ul>
                    </div>
                  )}
                  
                  {selectedRisk.level === 'low' && (
                    <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-200">
                      <h5 className="text-sm font-medium text-yellow-700 mb-2">低风险应对措施</h5>
                      <ul className="list-disc list-inside text-sm text-yellow-600 space-y-2">
                        <li>记录在客户档案中，以供参考</li>
                        <li>在治疗前告知客户可能的轻微影响</li>
                        <li>常规监测治疗过程中的反应</li>
                        <li>按照标准流程进行，无需特别干预</li>
                      </ul>
                    </div>
                  )}
                  
                  {/* 相关文献或案例 */}
                  <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                    <h5 className="text-sm font-medium text-blue-700 mb-2">相关文献参考</h5>
                    <p className="text-sm text-blue-600 mb-2">
                      以下内容可以帮助您更好地了解和应对此类风险情况：
                    </p>
                    <ul className="list-disc list-inside text-sm text-blue-600">
                      <li>《医美风险管理实操指南》- 风险评估章节</li>
                      <li>《常见医美并发症处理》- 第三章</li>
                      <li>医院内部培训资料：风险控制流程V2.1</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="hidden md:flex w-1/2 items-center justify-center p-8 bg-gray-50 text-gray-500">
              <div className="text-center">
                <svg className="h-16 w-16 text-gray-300 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <p>选择左侧风险查看详情</p>
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