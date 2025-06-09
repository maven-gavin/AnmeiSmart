'use client';

import { useState, useEffect } from 'react';
import { type CustomerProfile as ICustomerProfile, ConsultationHistoryItem, Message } from '@/types/chat';
import { getCustomerProfile, getCustomerConsultationHistory, getConversationMessages } from '@/service/chatService';
import { useRouter } from 'next/navigation';
import ChatMessage from '@/components/chat/message/ChatMessage';

interface CustomerProfileProps {
  customerId?: string;
  conversationId?: string;
}

export default function CustomerProfile({ customerId = '101', conversationId }: CustomerProfileProps) {
  const router = useRouter();
  const [profile, setProfile] = useState<ICustomerProfile | null>(null);
  const [consultationHistory, setConsultationHistory] = useState<ConsultationHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'basic' | 'history' | 'risk'>('basic');
  const [showHistoryModal, setShowHistoryModal] = useState(false);
  const [selectedHistory, setSelectedHistory] = useState<ConsultationHistoryItem | null>(null);
  const [showMessagesPreview, setShowMessagesPreview] = useState(false);
  const [historyMessages, setHistoryMessages] = useState<Message[]>([]);
  const [loadingMessages, setLoadingMessages] = useState(false);
  
  // 从API获取客户档案
  useEffect(() => {
    const fetchProfile = async () => {
      setLoading(true);
      setError(null);
      
      try {
        console.log(`开始获取客户档案，客户ID: ${customerId}`);
        // 使用API获取客户档案
        const profileData = await getCustomerProfile(customerId);
        
        if (profileData) {
          console.log('获取客户档案成功:', profileData);
          setProfile(profileData);
          
          // 获取咨询历史
          const history = await getCustomerConsultationHistory(customerId);
          setConsultationHistory(history);
        } else {
          setError('未找到客户档案');
          console.error('未找到客户档案');
        }
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : '获取客户档案失败';
        setError(errorMessage);
        console.error('获取客户档案失败:', error);
      } finally {
        setLoading(false);
      }
    };
    
    if (customerId) {
      fetchProfile();
    } else {
      setLoading(false);
      setProfile(null);
    }
  }, [customerId]);
  
  // 打开历史咨询详情
  const openHistoryDetail = (history: ConsultationHistoryItem) => {
    setSelectedHistory(history);
    setShowHistoryModal(true);
    // 重置消息预览状态
    setShowMessagesPreview(false);
    setHistoryMessages([]);
  };
  
  // 关闭历史咨询详情
  const closeHistoryDetail = () => {
    setShowHistoryModal(false);
    setSelectedHistory(null);
    setShowMessagesPreview(false);
    setHistoryMessages([]);
  };
  
  // 查看历史会话消息
  const viewHistoryConversation = (conversationId: string) => {
    closeHistoryDetail();
    // 跳转到会话页面
    router.push(`/consultant/chat?customerId=${customerId}&conversationId=${conversationId}`);
  };
  
  // 预览历史消息
  const previewHistoryMessages = async (conversationId: string) => {
    if (showMessagesPreview && historyMessages.length > 0) {
      // 如果已经显示预览且有消息，则关闭预览
      setShowMessagesPreview(false);
      return;
    }
    
    setLoadingMessages(true);
    
    try {
      const messages = await getConversationMessages(conversationId, true);
      setHistoryMessages(messages);
      setShowMessagesPreview(true);
    } catch (error) {
      console.error('获取历史消息失败:', error);
    } finally {
      setLoadingMessages(false);
    }
  };
  
  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-orange-500 border-t-transparent"></div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-gray-500">{error}</p>
      </div>
    );
  }
  
  if (!profile) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-gray-500">没有找到客户信息</p>
      </div>
    );
  }
  
  return (
    <div className="h-full flex flex-col">
      {/* 顶部标签页 */}
      <div className="flex border-b border-gray-200 sticky top-0 bg-white">
        <button
          className={`px-4 py-2 text-sm font-medium ${
            activeTab === 'basic' 
              ? 'text-orange-500 border-b-2 border-orange-500' 
              : 'text-gray-500 hover:text-gray-700'
          }`}
          onClick={() => setActiveTab('basic')}
        >
          基本信息
        </button>
        <button
          className={`px-4 py-2 text-sm font-medium ${
            activeTab === 'history' 
              ? 'text-orange-500 border-b-2 border-orange-500' 
              : 'text-gray-500 hover:text-gray-700'
          }`}
          onClick={() => setActiveTab('history')}
        >
          咨询历史
          {consultationHistory && consultationHistory.length > 0 && (
            <span className="ml-1 rounded-full bg-orange-100 px-2 py-0.5 text-xs text-orange-600">
              {consultationHistory.length}
            </span>
          )}
        </button>
        <button
          className={`px-4 py-2 text-sm font-medium ${
            activeTab === 'risk' 
              ? 'text-orange-500 border-b-2 border-orange-500' 
              : 'text-gray-500 hover:text-gray-700'
          }`}
          onClick={() => setActiveTab('risk')}
        >
          风险提示
          {profile.riskNotes && profile.riskNotes.length > 0 && (
            <span className="ml-1 rounded-full bg-red-100 px-2 py-0.5 text-xs text-red-600">
              {profile.riskNotes.length}
            </span>
          )}
        </button>
      </div>
      
      {/* 内容区域 */}
      <div className="flex-1 overflow-y-auto p-4">
        {/* 基本信息 */}
        {activeTab === 'basic' && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-800">客户档案</h3>
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
            {consultationHistory && consultationHistory.length > 0 && (
              <div className="rounded-lg border border-gray-200 bg-white p-4">
                <div className="flex justify-between items-center mb-3">
                  <h4 className="font-medium text-gray-700">最近咨询</h4>
                  <button 
                    className="text-xs text-orange-500 hover:text-orange-600"
                    onClick={() => setActiveTab('history')}
                  >
                    查看全部
                  </button>
                </div>
                <div className="space-y-3">
                  {consultationHistory.slice(0, 2).map((history, index) => (
                    <div 
                      key={index}
                      className="rounded-lg bg-gray-50 p-3 text-sm cursor-pointer hover:bg-gray-100"
                      onClick={() => openHistoryDetail(history)}
                    >
                      <div className="mb-1 flex justify-between">
                        <span className="font-medium">{history.type}</span>
                        <span className="text-gray-500">{history.date}</span>
                      </div>
                      <p className="text-gray-600 break-words line-clamp-2">{history.description}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
        
        {/* 咨询历史 */}
        {activeTab === 'history' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-800">咨询历史</h3>
              <span className="text-sm text-gray-500">共 {consultationHistory.length} 条记录</span>
            </div>
            
            {consultationHistory && consultationHistory.length > 0 ? (
              <div className="space-y-3">
                {consultationHistory.map((history, index) => (
                  <div 
                    key={index}
                    className="rounded-lg border border-gray-200 bg-white p-4 cursor-pointer hover:border-orange-200 hover:shadow-sm transition-all"
                    onClick={() => openHistoryDetail(history)}
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
                            previewHistoryMessages(history.id);
                          }}
                          className="text-xs text-orange-500 hover:text-orange-600 mr-3 flex items-center"
                        >
                          <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                          </svg>
                          快速预览
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            viewHistoryConversation(history.id);
                          }}
                          className="text-xs text-orange-500 hover:text-orange-600 flex items-center"
                        >
                          <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                          </svg>
                          查看完整会话
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-12 text-gray-500">
                <svg className="h-12 w-12 text-gray-300 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <p>暂无咨询历史</p>
              </div>
            )}
          </div>
        )}
        
        {/* 风险提示 */}
        {activeTab === 'risk' && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-800">风险提示</h3>
            
            {profile.riskNotes && profile.riskNotes.length > 0 ? (
              <div className="space-y-4">
                <div className="rounded-lg border border-gray-200 bg-white p-4">
                  <h4 className="mb-3 text-sm font-medium text-gray-700">风险等级说明</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center">
                      <span className="inline-block h-3 w-3 rounded-full bg-red-500 mr-2"></span>
                      <span className="text-gray-700">高风险 - 需特别关注，可能对治疗造成重大影响</span>
                    </div>
                    <div className="flex items-center">
                      <span className="inline-block h-3 w-3 rounded-full bg-orange-500 mr-2"></span>
                      <span className="text-gray-700">中风险 - 需要注意并评估对治疗的影响</span>
                    </div>
                    <div className="flex items-center">
                      <span className="inline-block h-3 w-3 rounded-full bg-yellow-500 mr-2"></span>
                      <span className="text-gray-700">低风险 - 需要记录但对治疗影响较小</span>
                    </div>
                  </div>
                </div>
                
                <div className="space-y-3">
                  {profile.riskNotes.map((risk, index) => (
                    <div 
                      key={index}
                      className={`rounded-lg p-4 ${
                        risk.level === 'high' 
                          ? 'bg-red-50 border border-red-200' 
                          : risk.level === 'medium'
                          ? 'bg-orange-50 border border-orange-200'
                          : 'bg-yellow-50 border border-yellow-200'
                      }`}
                    >
                      <div className="flex items-center mb-2">
                        <span className={`inline-block h-3 w-3 rounded-full mr-2 ${
                          risk.level === 'high' ? 'bg-red-500' : 
                          risk.level === 'medium' ? 'bg-orange-500' : 'bg-yellow-500'
                        }`}></span>
                        <span className={`font-medium ${
                          risk.level === 'high' ? 'text-red-700' : 
                          risk.level === 'medium' ? 'text-orange-700' : 'text-yellow-700'
                        }`}>{risk.type}</span>
                      </div>
                      <p className={`text-sm ${
                        risk.level === 'high' ? 'text-red-600' : 
                        risk.level === 'medium' ? 'text-orange-600' : 'text-yellow-600'
                      }`}>{risk.description}</p>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-12 text-gray-500">
                <svg className="h-12 w-12 text-gray-300 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <p>未发现风险</p>
              </div>
            )}
          </div>
        )}
      </div>
      
      {/* 历史咨询详情弹窗 */}
      {showHistoryModal && selectedHistory && (
        <div className="fixed inset-0 bg-black bg-opacity-30 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[80vh] flex flex-col">
            <div className="p-4 border-b border-gray-200 flex justify-between items-center">
              <div>
                <h3 className="text-lg font-medium">咨询详情</h3>
                <p className="text-sm text-gray-500 mt-1">{selectedHistory.date}</p>
              </div>
              <button 
                onClick={closeHistoryDetail}
                className="text-gray-500 hover:text-gray-700"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            <div className="p-4 overflow-y-auto flex-1">
              <div className="mb-4">
                <div className="text-sm text-gray-500 mb-1">咨询类型</div>
                <div className="font-medium">{selectedHistory.type}</div>
              </div>
              
              <div className="mb-4">
                <div className="text-sm text-gray-500 mb-1">咨询内容</div>
                <div className="bg-gray-50 rounded-lg p-4 text-gray-700 whitespace-pre-wrap">
                  {selectedHistory.description}
                </div>
              </div>
              
              {/* 历史消息预览区域 */}
              {showMessagesPreview && (
                <div className="mt-4">
                  <div className="flex items-center justify-between mb-3">
                    <div className="text-sm font-medium text-gray-700">历史消息记录</div>
                    <button 
                      onClick={() => setShowMessagesPreview(false)}
                      className="text-xs text-gray-500 hover:text-gray-700"
                    >
                      收起
                    </button>
                  </div>
                  
                  <div className="bg-gray-50 rounded-lg p-3 max-h-[300px] overflow-y-auto border border-gray-200">
                    {historyMessages.length > 0 ? (
                      <div className="space-y-2">
                        {historyMessages.map((message, index) => (
                          <ChatMessage 
                            key={index}
                            message={message}
                            compact={true}
                          />
                        ))}
                      </div>
                    ) : loadingMessages ? (
                      <div className="flex justify-center py-8">
                        <div className="h-6 w-6 animate-spin rounded-full border-2 border-orange-500 border-t-transparent"></div>
                      </div>
                    ) : (
                      <div className="text-center py-8 text-gray-500">
                        暂无消息记录
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
            
            <div className="p-4 border-t border-gray-200">
              <div className="flex justify-between">
                <div className="space-x-2">
                  <button
                    onClick={() => previewHistoryMessages(selectedHistory.id)}
                    className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors flex items-center"
                  >
                    <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                    {showMessagesPreview ? "收起消息" : "快速预览"}
                  </button>
                  
                  <button
                    onClick={() => viewHistoryConversation(selectedHistory.id)}
                    className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors flex items-center"
                  >
                    <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                    </svg>
                    查看完整会话
                  </button>
                </div>
                
                <button
                  onClick={closeHistoryDetail}
                  className="px-4 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition-colors"
                >
                  关闭
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
} 