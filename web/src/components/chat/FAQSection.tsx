'use client';

import React, { useState, useEffect, useCallback, useMemo } from 'react';

// FAQ类型定义
export interface FAQ {
  id: string;
  question: string;
  answer: string;
  tags: string[];
}

interface FAQSectionProps {
  onSelectFAQ: (question: string) => void; // FAQ选择回调
  messages?: Array<{content: string}>;
}

// 完整的FAQ数据
const allFAQs: FAQ[] = [
  { id: 'faq1', question: '订单交期延误了怎么办？', answer: '系统会自动生成交期核查工单，分派给PMC部门，2小时内给出交期反馈。同时我会在今天16:00前给您回复最新进展。', tags: ['交期', '延误', '催货', '工单'] },
  { id: 'faq2', question: '能给我报个含税价吗？', answer: '我需要先确认您的数量、交期和付款条款，然后为您生成正式报价单。系统会自动创建报价申请工单，24小时内给您正式报价。', tags: ['报价', '含税', '价格', '折扣'] },
  { id: 'faq3', question: '你们的产品能替代XX品牌吗？', answer: '我需要了解您的应用场景、工况条件和数量等信息。系统会生成技术澄清工单，由FAE团队评估替代可行性，并提供ROHS/材质证明等资料。', tags: ['替代', '技术选型', '认证', '材质'] },
  { id: 'faq4', question: '这批货有质量问题，要你们赔偿', answer: '非常抱歉给您带来困扰。系统已自动创建高优先级质量异常工单，QE团队会在4小时内初步响应。我会立即回访收集批次信息，按流程评估处理方案。', tags: ['质量', '不良', '索赔', '异常'] },
  { id: 'faq5', question: '能便宜10%吗？给个底价', answer: '我需要先了解您的具体需求（数量、交期、付款方式），然后为您申请正式报价。系统会创建报价申请工单，由报价部门在24小时内给出合规报价单。', tags: ['折扣', '价格', '报价', '底价'] },
  { id: 'faq6', question: '需要ROHS认证和材质证明', answer: '没问题。系统会生成技术澄清工单，FAE团队会为您提供完整的认证资料。请提供应用场景和工况信息，以便我们给出最准确的替代方案。', tags: ['认证', 'ROHS', '材质证明', '技术'] },
  { id: 'faq7', question: '能保证明天一定到货吗？', answer: '我会立即核查当前出货节点和物流安排，给您确认最准确的到货时间。如果时间紧张，我们也可以提供替代方案（如加急或分批发货）。', tags: ['交期', '承诺', '到货', '物流'] },
  { id: 'faq8', question: '把你们的工艺参数和图纸发给我', answer: '我可以先提供产品手册、技术白皮书和认证报告等公开资料。如需详细的工艺参数和图纸，需要您签署NDA后，系统会创建资料申请工单，由法务和研发部门审核后提供。', tags: ['图纸', '工艺参数', '保密', '资料'] },
  { id: 'faq9', question: '你们有类似客户案例吗？', answer: '我可以提供公开的产品应用案例和技术白皮书。如需详细的客户案例和项目资料，需要签署保密协议后，系统会走资料申请流程，由相关部门审核后提供。', tags: ['客户案例', '案例', '资料', '保密'] },
  { id: 'faq10', question: '质量问题的赔偿金额怎么算？', answer: '我们会先收集完整的批次信息、不良品照片和检测报告等证据，QE团队会在4小时内初步评估。具体的赔偿方案需要按公司流程评估，我会及时跟进并向您反馈处理进展。', tags: ['索赔', '赔偿', '质量', '流程'] },
];

export default function FAQSection({
  onSelectFAQ,
  messages = []
}: FAQSectionProps) {
  // 内部管理的显示状态
  const [isVisible, setIsVisible] = useState(false);
  // 内部管理的搜索状态
  const [searchQuery, setSearchQuery] = useState('');
  // 推荐的FAQ状态
  const [recommendedFAQs, setRecommendedFAQs] = useState<FAQ[]>(allFAQs.slice(0, 3));

  // 内部化的FAQ选择处理
  const handleSelectFAQ = (faq: FAQ) => {
    onSelectFAQ(faq.answer); // 传入答案而不是问题
    setIsVisible(false); // 选择后自动关闭
  };

  // 内部化的显示控制
  const toggleVisibility = () => {
    setIsVisible(!isVisible);
  };

  // 内部化的关闭处理
  const handleClose = () => {
    setIsVisible(false);
  };

  // 使用useMemo缓存消息内容，避免不必要的重新计算
  const messagesHash = useMemo(() => {
    return messages.map(msg => msg.content || '').join('|');
  }, [messages]);

  // 基于聊天记录推荐FAQ 
  const recommendFAQsBasedOnChat = useCallback((msgs: Array<{content: string}>) => {
    if (msgs.length === 0) {
      return allFAQs.slice(0, 3);
    }
    
    // 获取最近的5条消息用于分析
    const recentMessages = msgs
      .slice(-5)
      .map(msg => msg.content || '')
      .join(' ')
      .toLowerCase();
    
    // 分析消息内容，匹配关键词与FAQ
    const scoredFAQs = allFAQs.map(faq => {
      let score = 0;
      
      // 检查问题是否匹配
      if (recentMessages.includes(faq.question.toLowerCase())) {
        score += 5;
      }
      
      // 检查标签是否匹配
      faq.tags.forEach(tag => {
        if (recentMessages.includes(tag.toLowerCase())) {
          score += 3;
        }
      });
      
      // 内容匹配度
      const answerWords = faq.answer.toLowerCase().split(/\s+/);
      answerWords.forEach(word => {
        if (word.length > 3 && recentMessages.includes(word)) {
          score += 1;
        }
      });
      
      return { ...faq, score };
    });
    
    // 按匹配分数排序，选择前3个
    const topFAQs = scoredFAQs
      .sort((a: any, b: any) => b.score - a.score)
      .slice(0, 5)
      .map(({ id, question, answer, tags }) => ({ id, question, answer, tags }));
    
    return topFAQs.length > 0 ? topFAQs : allFAQs.slice(0, 3);
  }, []);

  // 计算推荐的FAQ，使用useMemo缓存结果
  const computedRecommendedFAQs = useMemo(() => {
    if (!searchQuery.trim()) {
      return recommendFAQsBasedOnChat(messages);
    }
    
    // 根据关键词过滤FAQ
    const normalizedQuery = searchQuery.toLowerCase();
    const filtered = allFAQs.filter(faq => 
      faq.question.toLowerCase().includes(normalizedQuery) || 
      faq.answer.toLowerCase().includes(normalizedQuery) ||
      faq.tags.some(tag => tag.toLowerCase().includes(normalizedQuery))
    );
    
    return filtered.length > 0 ? filtered : allFAQs.slice(0, 3);
  }, [searchQuery, messagesHash, recommendFAQsBasedOnChat]);

  // 使用useEffect更新推荐FAQ状态
  useEffect(() => {
    setRecommendedFAQs(computedRecommendedFAQs);
  }, [computedRecommendedFAQs]);

  // 内部处理搜索输入
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchQuery(value);
  };

  // 内部处理搜索清除
  const handleClearSearch = () => {
    setSearchQuery('');
  };

  // 渲染FAQ按钮
  const renderButton = () => (
    <button 
      className={`flex-shrink-0 ${isVisible ? 'text-orange-500' : 'text-gray-500 hover:text-gray-700'}`}
      onClick={toggleVisibility}
      title="常见问题"
    >
      <svg
        className="h-6 w-6"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
    </button>
  );

  // 渲染FAQ面板
  const renderPanel = () => (
    isVisible && (
      <div className="border-t border-gray-200 bg-gray-50 p-3">
        <div className="flex justify-between items-center mb-2">
          <div className="text-sm font-medium text-gray-700">常见问题</div>
          <button 
            onClick={handleClose}
            className="text-gray-500 hover:text-gray-700"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        {/* FAQ搜索 */}
        <div className="mb-3">
          <div className="relative">
            <input
              type="text"
              value={searchQuery}
              onChange={handleSearchChange}
              placeholder="搜索常见问题..."
              className="w-full rounded-lg border border-gray-200 pl-10 pr-4 py-2 text-sm focus:border-orange-500 focus:outline-none"
            />
            <svg
              className="absolute left-3 top-2.5 h-4 w-4 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
            {searchQuery && (
              <button
                className="absolute right-3 top-2.5 text-gray-400 hover:text-gray-600"
                onClick={handleClearSearch}
              >
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>
        </div>
        
        <div className="flex flex-col gap-2 max-h-96 overflow-y-auto pr-1">
          {recommendedFAQs.length > 0 ? (
            recommendedFAQs.map(faq => (
              <button
                key={faq.id}
                className="rounded-lg border border-orange-200 bg-white px-3 py-2 text-left text-sm text-gray-700 hover:bg-orange-50"
                onClick={() => handleSelectFAQ(faq)}
              >
                <p className="font-medium text-orange-700">{faq.question}</p>
                <p className="mt-1 text-xs text-gray-500 line-clamp-1">{faq.answer}</p>
              </button>
            ))
          ) : (
            <div className="rounded-lg bg-white px-3 py-2 text-center text-sm text-gray-500">
              没有找到相关问题
            </div>
          )}
        </div>
      </div>
    )
  );

  // 将按钮和面板分别暴露
  return {
    button: renderButton(),
    panel: renderPanel()
  };
} 