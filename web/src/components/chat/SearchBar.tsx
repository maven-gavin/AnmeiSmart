'use client';

import React from 'react';

interface SearchBarProps {
  searchTerm: string;
  setSearchTerm: (term: string) => void;
  searchResults: any[];
  selectedMessageId: string | null;
  setSelectedMessageId: (id: string | null) => void;
  searchChatMessages: (term: string) => void;
  goToNextSearchResult: () => void;
  goToPreviousSearchResult: () => void;
  closeSearch: () => void;
}

export default function SearchBar({
  searchTerm,
  setSearchTerm,
  searchResults,
  selectedMessageId,
  setSelectedMessageId,
  searchChatMessages,
  goToNextSearchResult,
  goToPreviousSearchResult,
  closeSearch
}: SearchBarProps) {
  return (
    <div className="border-b border-gray-200 bg-white p-2 shadow-sm">
      <div className="flex items-center">
        <div className="relative flex-1">
          <input
            type="text"
            value={searchTerm}
            onChange={e => {
              setSearchTerm(e.target.value);
              searchChatMessages(e.target.value);
            }}
            placeholder="搜索聊天记录..."
            className="w-full rounded-lg border border-gray-200 pl-10 pr-4 py-2 text-sm focus:border-orange-500 focus:outline-none"
            autoFocus
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
          {searchTerm && (
            <button
              className="absolute right-10 top-2.5 text-gray-400 hover:text-gray-600"
              onClick={() => {
                setSearchTerm('');
                setSelectedMessageId(null);
              }}
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
        
        <div className="ml-2 flex space-x-1">
          <div className="flex items-center ml-2 text-xs text-gray-500">
            {searchResults.length > 0 && selectedMessageId && (
              <span>
                {searchResults.findIndex(m => m.id === selectedMessageId) + 1}/{searchResults.length}
              </span>
            )}
          </div>
          
          <button
            className="p-1.5 text-gray-500 hover:text-gray-700 rounded-md hover:bg-gray-100 disabled:opacity-50"
            disabled={searchResults.length === 0}
            onClick={goToPreviousSearchResult}
            title="上一个结果"
          >
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          
          <button
            className="p-1.5 text-gray-500 hover:text-gray-700 rounded-md hover:bg-gray-100 disabled:opacity-50"
            disabled={searchResults.length === 0}
            onClick={goToNextSearchResult}
            title="下一个结果"
          >
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>
          
          <button
            className="p-1.5 text-gray-500 hover:text-gray-700 rounded-md hover:bg-gray-100"
            onClick={closeSearch}
            title="关闭搜索"
          >
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
} 