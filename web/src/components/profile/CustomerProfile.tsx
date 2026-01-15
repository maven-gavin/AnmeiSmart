'use client';

import { useMemo, useState } from 'react';
import { useCustomerProfile } from '@/hooks/useCustomerProfile';
import { customerService } from '@/service/customerService';
import { ConsultationHistory } from './ConsultationHistory';

interface CustomerProfileProps {
  customerId: string;
  conversationId?: string;
}

export default function CustomerProfile({ customerId, conversationId }: CustomerProfileProps) {
  const [activeTab, setActiveTab] = useState<'insights' | 'history'>('insights');
  const [newCategory, setNewCategory] = useState('need');
  const [newContent, setNewContent] = useState('');
  const [submitting, setSubmitting] = useState(false);
  
  // 使用自定义hooks管理状态和逻辑
  const { profile, consultationHistory, loading, error, refetch } = useCustomerProfile(customerId, conversationId);

  const displayProfile = useMemo(() => {
    if (profile) {
      return profile;
    }
    return {
      id: '',
      customer_id: customerId,
      life_cycle_stage: 'lead',
      industry: '',
      company_scale: '',
      ai_summary: '',
      active_insights: []
    };
  }, [profile, customerId]);

  const insights = useMemo(() => {
    return displayProfile.active_insights || [];
  }, [displayProfile.active_insights]);

  const handleAddInsight = async () => {
    const content = newContent.trim();
    if (!content) return;

    try {
      setSubmitting(true);
      await customerService.addCustomerInsight(customerId, {
        category: newCategory,
        content,
        source: 'human',
      });
      setNewContent('');
      await refetch();
    } finally {
      setSubmitting(false);
    }
  };

  const handleArchive = async (insightId: string) => {
    await customerService.archiveCustomerInsight(customerId, insightId);
    await refetch();
  };

  // 加载状态
  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="am-spinner"></div>
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

  return (
    <div className="h-full flex flex-col">
      {!profile && (
        <div className="bg-brand-soft text-brand-deep px-4 py-2 text-sm">
          档案初始化中，暂时展示默认结构
          <button className="am-btn-outline ml-3" type="button" onClick={refetch}>
            立即刷新
          </button>
        </div>
      )}
      {/* 头部/Tab */}
      <div className="sticky top-0 bg-white border-b border-gray-200">
        <div className="flex items-center justify-between px-4 py-3">
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <h3 className="text-base font-semibold text-gray-900 truncate">客户画像</h3>
              <span className="am-badge-neutral">
                {displayProfile.life_cycle_stage || 'lead'}
              </span>
            </div>
            <div className="mt-1 text-xs text-gray-500">
              {displayProfile.industry ? `行业：${displayProfile.industry}` : '行业：-'} · {displayProfile.company_scale ? `规模：${displayProfile.company_scale}` : '规模：-'}
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              className={activeTab === 'insights' ? 'am-btn-primary' : 'am-btn-outline'}
              onClick={() => setActiveTab('insights')}
              type="button"
            >
              画像流
            </button>
            <button
              className={activeTab === 'history' ? 'am-btn-primary' : 'am-btn-outline'}
              onClick={() => setActiveTab('history')}
              type="button"
            >
              会话历史
            </button>
          </div>
        </div>
      </div>
      
      {/* 内容区域 */}
      <div className="flex-1 overflow-y-auto p-4">
        {activeTab === 'insights' && (
          <div className="space-y-4">
            {/* AI 摘要 */}
            <div className="am-card p-4">
              <div className="text-sm font-medium text-gray-900">AI 摘要</div>
              <div className="mt-2 text-sm text-gray-700 whitespace-pre-wrap">
                {displayProfile.ai_summary?.trim() ? displayProfile.ai_summary : '暂无摘要（后续由 SmartBrain 自动沉淀）'}
              </div>
            </div>

            {/* 人工新增洞察 */}
            <div className="am-card p-4">
              <div className="text-sm font-medium text-gray-900">新增洞察（人工）</div>
              <div className="mt-3 grid grid-cols-1 gap-3">
                <select
                  className="am-field"
                  value={newCategory}
                  onChange={(e) => setNewCategory(e.target.value)}
                >
                  <option value="need">需求</option>
                  <option value="budget">预算</option>
                  <option value="authority">决策权</option>
                  <option value="timeline">时间表</option>
                  <option value="preference">偏好</option>
                  <option value="risk">风险</option>
                  <option value="trait">特质</option>
                  <option value="background">背景</option>
                  <option value="other">其他</option>
                </select>
                <textarea
                  className="am-field min-h-[80px]"
                  value={newContent}
                  onChange={(e) => setNewContent(e.target.value)}
                  placeholder="例如：客户明确表示更关注交付周期，倾向先试用再采购"
                />
                <div className="flex justify-end">
                  <button
                    className="am-btn-primary"
                    type="button"
                    onClick={handleAddInsight}
                    disabled={submitting || !newContent.trim()}
                  >
                    {submitting ? '提交中...' : '添加'}
                  </button>
                </div>
              </div>
            </div>

            {/* 画像流 */}
            <div className="am-card p-4">
              <div className="flex items-center justify-between">
                <div className="text-sm font-medium text-gray-900">画像流（最新在上）</div>
                <div className="text-xs text-gray-500">共 {insights.length} 条</div>
              </div>

              {insights.length === 0 ? (
                <div className="mt-6 text-sm text-gray-500">暂无洞察，等待 SmartBrain 或人工沉淀。</div>
              ) : (
                <div className="mt-4 space-y-3">
                  {insights.map((insight) => (
                    <div key={insight.id} className="rounded-lg border border-gray-200 p-3">
                      <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="am-badge-neutral">{insight.category}</span>
                            {insight.confidence != null && (
                              <span className="text-xs text-gray-500">置信度：{insight.confidence.toFixed(2)}</span>
                            )}
                          </div>
                          <div className="mt-2 text-sm text-gray-800 whitespace-pre-wrap break-words">
                            {insight.content}
                          </div>
                          <div className="mt-2 text-xs text-gray-500">
                            {insight.created_at ? new Date(insight.created_at).toLocaleString('zh-CN') : ''}{insight.source ? ` · ${insight.source}` : ''}{insight.created_by_name ? ` · ${insight.created_by_name}` : ''}
                          </div>
                        </div>

                        <button
                          type="button"
                          className="am-btn-reset"
                          onClick={() => handleArchive(insight.id)}
                        >
                          归档
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'history' && (
          <ConsultationHistory
            consultationHistory={consultationHistory}
            onOpenHistoryDetail={() => {}}
            onViewConversation={() => {}}
          />
        )}
      </div>
    </div>
  );
} 