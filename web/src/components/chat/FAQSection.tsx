'use client';

import React from 'react';

// FAQ类型定义
interface FAQ {
  id: string;
  question: string;
  answer: string;
  tags: string[];
}

interface FAQSectionProps {
  recommendedFAQs: FAQ[];
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  searchFAQs: (query: string) => void;
  insertFAQ: (faq: FAQ) => void;
  closeFAQ: () => void;
}

export default function FAQSection({
  recommendedFAQs,
  searchQuery,
  setSearchQuery,
  searchFAQs,
  insertFAQ,
  closeFAQ
}: FAQSectionProps) {
  return (
    <div className="border-t border-gray-200 bg-gray-50 p-3">
      <div className="flex justify-between items-center mb-2">
        <div className="text-sm font-medium text-gray-700">常见问题</div>
        <button 
          onClick={closeFAQ}
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
            onChange={e => {
              setSearchQuery(e.target.value);
              searchFAQs(e.target.value);
            }}
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
              onClick={() => {
                setSearchQuery('');
                // 重置FAQ
                searchFAQs('');
              }}
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
              onClick={() => insertFAQ(faq)}
            >
              <p className="font-medium text-orange-700">{faq.question}</p>
              <p className="mt-1 text-xs text-gray-500 line-clamp-1">{faq.answer}</p>
            </button>
          ))
        ) : (
          <div className="text-center py-3 text-gray-500 text-sm">
            未找到相关问题，请尝试其他关键词
          </div>
        )}
      </div>
      
      {/* 查看全部FAQ */}
      <button 
        className="mt-3 text-sm text-orange-600 hover:text-orange-700 font-medium flex items-center justify-center w-full"
        onClick={() => {
          setSearchQuery('');
          // 获取所有FAQ
          searchFAQs('');
        }}
      >
        <span>查看全部常见问题</span>
        <svg className="h-4 w-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      </button>
    </div>
  );
} 