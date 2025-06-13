'use client';

import { useState, useEffect } from 'react';
import { ConsultationHistoryItem, Message } from '@/types/chat';

interface MessagePreviewProps {
  show: boolean;
  messages: Message[];
  loading: boolean;
  onToggle: () => void;
}

interface ConsultationSummaryData {
  main_issues: string[];
  solutions: string[];
  follow_up_plan: string[];
  satisfaction_rating?: number;
  additional_notes?: string;
  tags: string[];
}

interface ConsultationModalProps {
  isOpen: boolean;
  consultation: ConsultationHistoryItem | null;
  conversationId?: string;
  onClose: () => void;
  onPreviewMessages: (conversationId: string) => Promise<void>;
  onViewConversation: (conversationId: string) => void;
  messages: Message[];
  showMessagesPreview: boolean;
  loadingMessages: boolean;
  onTogglePreview: () => void;
  onSaveSummary?: (summaryData: ConsultationSummaryData) => Promise<void>;
  onAIGenerate?: (conversationId: string) => Promise<ConsultationSummaryData>;
}

export function ConsultationModal({
  isOpen,
  consultation,
  conversationId,
  onClose,
  onSaveSummary,
  onAIGenerate
}: ConsultationModalProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [aiGenerating, setAiGenerating] = useState(false);
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState<{type: 'success' | 'error', message: string} | null>(null);
  const [summaryData, setSummaryData] = useState<ConsultationSummaryData>({
    main_issues: [],
    solutions: [],
    follow_up_plan: [],
    satisfaction_rating: undefined,
    additional_notes: '',
    tags: []
  });

  // 如果是新建总结且没有consultation数据
  const isNewSummary = !consultation && conversationId;

  useEffect(() => {
    if (isOpen) {
      if (consultation?.has_summary && consultation) {
        // 如果有现有总结，加载数据（这里简化处理，实际应该从API获取详细数据）
        setSummaryData({
          main_issues: [consultation.description.slice(0, 100)], // 示例数据
          solutions: [],
          follow_up_plan: [],
          satisfaction_rating: consultation.satisfaction_rating,
          additional_notes: '',
          tags: []
        });
        setIsEditing(false);
        setIsCreating(false);
      } else if (isNewSummary) {
        // 新建总结
        setIsCreating(true);
        setIsEditing(true);
        setSummaryData({
          main_issues: [],
          solutions: [],
          follow_up_plan: [],
          satisfaction_rating: undefined,
          additional_notes: '',
          tags: []
        });
      }
    }
  }, [isOpen, consultation, isNewSummary]);

  if (!isOpen) {
    return null;
  }

  const handleAIGenerate = async () => {
    if (!conversationId || !onAIGenerate) return;
    
    setAiGenerating(true);
    try {
      const aiData = await onAIGenerate(conversationId);
      setSummaryData(aiData);
    } catch (error) {
      console.error('AI生成失败:', error);
    } finally {
      setAiGenerating(false);
    }
  };

  const handleSave = async () => {
    if (!onSaveSummary) return;
    
    setSaving(true);
    try {
      await onSaveSummary(summaryData);
      setToast({ type: 'success', message: '咨询总结保存成功！' });
      setIsEditing(false);
      setIsCreating(false);
      setTimeout(() => {
        onClose();
        setToast(null);
      }, 1500);
    } catch (error) {
      console.error('保存失败:', error);
      setToast({ type: 'error', message: '保存失败，请重试' });
      setTimeout(() => setToast(null), 3000);
    } finally {
      setSaving(false);
    }
  };

  const handleAddItem = (field: keyof Pick<ConsultationSummaryData, 'main_issues' | 'solutions' | 'follow_up_plan'>) => {
    setSummaryData(prev => ({
      ...prev,
      [field]: [...prev[field], '']
    }));
  };

  const handleUpdateItem = (field: keyof Pick<ConsultationSummaryData, 'main_issues' | 'solutions' | 'follow_up_plan'>, index: number, value: string) => {
    setSummaryData(prev => ({
      ...prev,
      [field]: prev[field].map((item, i) => i === index ? value : item)
    }));
  };

  const handleRemoveItem = (field: keyof Pick<ConsultationSummaryData, 'main_issues' | 'solutions' | 'follow_up_plan'>, index: number) => {
    setSummaryData(prev => ({
      ...prev,
      [field]: prev[field].filter((_, i) => i !== index)
    }));
  };

  const renderEditableSection = (
    title: string,
    field: keyof Pick<ConsultationSummaryData, 'main_issues' | 'solutions' | 'follow_up_plan'>,
    placeholder: string,
    icon: string
  ) => (
    <div className="mb-6">
      <div className="flex items-center justify-between mb-3">
        <label className="block text-sm font-medium text-gray-700">
          {icon} {title}
        </label>
        <button
          onClick={() => handleAddItem(field)}
          className="text-sm text-orange-500 hover:text-orange-600 flex items-center"
        >
          <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          添加
        </button>
      </div>
      <div className="space-y-2">
        {summaryData[field].map((item, index) => (
          <div key={index} className="flex items-center space-x-2">
            <textarea
              value={item}
              onChange={(e) => handleUpdateItem(field, index, e.target.value)}
              placeholder={placeholder}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg resize-none"
              rows={2}
            />
            <button
              onClick={() => handleRemoveItem(field, index)}
              className="p-2 text-red-500 hover:text-red-600"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        ))}
        {summaryData[field].length === 0 && (
          <div className="text-center py-4 text-gray-500 border-2 border-dashed border-gray-300 rounded-lg">
            点击"添加"按钮开始记录{title}
          </div>
        )}
      </div>
    </div>
  );

  return (
    <div className="fixed inset-0 bg-black bg-opacity-30 z-50 flex items-center justify-center p-4">
      {/* Toast提示 */}
      {toast && (
        <div className={`fixed top-4 right-4 z-[60] px-4 py-3 rounded-lg shadow-lg max-w-sm transform transition-all duration-300 ${
          toast.type === 'success' 
            ? 'bg-green-500 text-white' 
            : 'bg-red-500 text-white'
        }`}>
          <div className="flex items-center">
            {toast.type === 'success' ? (
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            ) : (
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            )}
            {toast.message}
          </div>
        </div>
      )}
      
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] flex flex-col">
        {/* 弹窗头部 */}
        <div className="p-6 border-b border-gray-200">
          <div className="flex justify-between items-center">
            <div>
              <h3 className="text-xl font-medium">
                {isCreating ? '创建咨询总结' : isEditing ? '编辑咨询总结' : '咨询总结'}
              </h3>
              <p className="text-sm text-gray-500 mt-1">
                {consultation?.date || '当前会话'} | {consultation?.type || '咨询会话'}
              </p>
            </div>
            <div className="flex items-center space-x-2">
              {(isEditing || isCreating) && onAIGenerate && (
                <button 
                  onClick={handleAIGenerate}
                  disabled={aiGenerating}
                  className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 disabled:opacity-50 flex items-center"
                >
                  {aiGenerating ? (
                    <>
                      <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mr-1"></div>
                      生成中...
                    </>
                  ) : (
                    <>
                      ✨ AI辅助生成
                    </>
                  )}
                </button>
              )}
              <button onClick={onClose}>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
        </div>
        
        {/* 弹窗内容 */}
        <div className="p-6 overflow-y-auto flex-1">
          {isEditing || isCreating ? (
            /* 编辑模式 */
            <div className="space-y-6">
              {/* 基本信息 */}
              <div className="grid grid-cols-2 gap-4 mb-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    咨询类型
                  </label>
                  <select className="w-full px-3 py-2 border border-gray-300 rounded-lg">
                    <option value="initial">初次咨询</option>
                    <option value="follow_up">复诊咨询</option>
                    <option value="emergency">紧急咨询</option>
                    <option value="specialized">专项咨询</option>
                    <option value="other">其他</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    满意度评分
                  </label>
                  <div className="flex items-center space-x-2">
                    {[1,2,3,4,5].map(rating => (
                      <button
                        key={rating}
                        onClick={() => setSummaryData(prev => ({ ...prev, satisfaction_rating: rating }))}
                        className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                          summaryData.satisfaction_rating === rating 
                            ? 'bg-orange-500 text-white' 
                            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                        }`}
                      >
                        {rating}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* 主要问题 */}
              {renderEditableSection('客户主要问题', 'main_issues', '请描述客户提出的具体问题...', '🎯')}
              
              {/* 解决方案 */}
              {renderEditableSection('提供的解决方案', 'solutions', '请描述针对问题提供的解决方案...', '💡')}
              
              {/* 后续跟进 */}
              {renderEditableSection('后续跟进计划', 'follow_up_plan', '请描述后续需要跟进的事项...', '📋')}

              {/* 补充备注 */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  📝 补充备注
                </label>
                <textarea 
                  value={summaryData.additional_notes || ''}
                  onChange={(e) => setSummaryData(prev => ({ ...prev, additional_notes: e.target.value }))}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg resize-none"
                  placeholder="其他需要记录的信息..."
                />
              </div>
            </div>
          ) : (
            /* 查看模式 */
            <div className="space-y-6">
              {consultation && (
                <>
                  <div className="mb-4">
                    <div className="text-sm text-gray-500 mb-1">咨询类型</div>
                    <div className="font-medium">{consultation.type}</div>
                  </div>
                  
                  <div className="mb-4">
                    <div className="text-sm text-gray-500 mb-1">咨询内容概述</div>
                    <div className="bg-gray-50 rounded-lg p-4 text-gray-700 whitespace-pre-wrap">
                      {consultation.description}
                    </div>
                  </div>

                  {consultation.satisfaction_rating && (
                    <div className="mb-4">
                      <div className="text-sm text-gray-500 mb-1">满意度评分</div>
                      <div className="flex items-center">
                        <span className="text-2xl font-bold text-orange-500 mr-2">{consultation.satisfaction_rating}</span>
                        <div className="flex">
                          {[1,2,3,4,5].map(star => (
                            <svg 
                              key={star}
                              className={`w-5 h-5 ${star <= consultation.satisfaction_rating! ? 'text-yellow-400' : 'text-gray-300'}`}
                              fill="currentColor" 
                              viewBox="0 0 20 20"
                            >
                              <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                            </svg>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          )}
        </div>
        
        {/* 弹窗底部操作按钮 */}
        <div className="p-6 border-t border-gray-200">
          <div className="flex justify-between">
            <div className="space-x-3">
              {isEditing || isCreating ? (
                <>
                  <button 
                    onClick={() => {
                      setIsEditing(false);
                      setIsCreating(false);
                    }}
                    className="px-4 py-2 text-gray-600 hover:text-gray-800"
                  >
                    取消
                  </button>
                  <button 
                    onClick={handleSave}
                    disabled={saving}
                    className="px-4 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
                  >
                    {saving ? (
                      <>
                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                        保存中...
                      </>
                    ) : (
                      '保存总结'
                    )}
                  </button>
                </>
              ) : (
                <>
                  {consultation && (
                    <button 
                      onClick={() => setIsEditing(true)}
                      className="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600"
                    >
                      编辑总结
                    </button>
                  )}
                  <button
                    onClick={onClose}
                    className="px-4 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600"
                  >
                    关闭
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 