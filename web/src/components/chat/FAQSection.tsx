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
  { id: 'faq1', question: '双眼皮手术恢复时间?', answer: '一般1-2周基本恢复，完全恢复需1-3个月。', tags: ['双眼皮', '恢复', '手术'] },
  { id: 'faq2', question: '医美项目价格咨询', answer: '我们提供多种套餐，价格从XX起，可根据您的需求定制。', tags: ['价格', '套餐', '咨询'] },
  { id: 'faq3', question: '术后护理注意事项', answer: '术后需避免剧烈运动，保持伤口清洁，按医嘱服药。', tags: ['术后', '护理', '注意事项'] },
  { id: 'faq4', question: '玻尿酸能维持多久?', answer: '根据注射部位和产品不同，一般可维持6-18个月。', tags: ['玻尿酸', '持续时间', '效果'] },
  { id: 'faq5', question: '肉毒素注射有副作用吗?', answer: '常见副作用包括注射部位疼痛、轻微肿胀，通常数天内消退。', tags: ['肉毒素', '副作用', '注射'] },
  { id: 'faq6', question: '医美手术前需要准备什么?', answer: '术前需进行相关检查，避免服用影响凝血的药物，遵医嘱调整饮食。', tags: ['术前', '准备', '检查'] },
  { id: 'faq7', question: '哪些人不适合做医美手术?', answer: '孕妇、有严重疾病、自身免疫性疾病患者等不适合。具体需医生评估。', tags: ['禁忌', '不适合', '评估'] },
  { id: 'faq8', question: '光子嫩肤后多久可以化妆?', answer: '一般建议术后24小时内不化妆，48小时后可轻微化妆。', tags: ['光子嫩肤', '化妆', '术后'] },
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
    onSelectFAQ(faq.question);
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

  // 基于聊天记录推荐FAQ - 移除useCallback，改为普通函数
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
        
        <div className="flex flex-col gap-2">
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