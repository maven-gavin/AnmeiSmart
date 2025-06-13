'use client';

import { useState } from 'react';
import { ConsultationHistoryItem, Message } from '@/types/chat';
import { MessagePreview } from './MessagePreview';

interface ConsultationModalProps {
  isOpen: boolean;
  consultation: ConsultationHistoryItem | null;
  onClose: () => void;
  onPreviewMessages: (conversationId: string) => Promise<void>;
  onViewConversation: (conversationId: string) => void;
  messages: Message[];
  showMessagesPreview: boolean;
  loadingMessages: boolean;
  onTogglePreview: () => void;
}

export function ConsultationModal({
  isOpen,
  consultation,
  onClose,
  onPreviewMessages,
  onViewConversation,
  messages,
  showMessagesPreview,
  loadingMessages,
  onTogglePreview
}: ConsultationModalProps) {
  if (!isOpen || !consultation) {
    return null;
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-30 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[80vh] flex flex-col">
        {/* 弹窗头部 */}
        <div className="p-4 border-b border-gray-200 flex justify-between items-center">
          <div>
            <h3 className="text-lg font-medium">咨询详情</h3>
            <p className="text-sm text-gray-500 mt-1">{consultation.date}</p>
          </div>
          <button 
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        {/* 弹窗内容 */}
        <div className="p-4 overflow-y-auto flex-1">
          <div className="mb-4">
            <div className="text-sm text-gray-500 mb-1">咨询类型</div>
            <div className="font-medium">{consultation.type}</div>
          </div>
          
          <div className="mb-4">
            <div className="text-sm text-gray-500 mb-1">咨询内容</div>
            <div className="bg-gray-50 rounded-lg p-4 text-gray-700 whitespace-pre-wrap">
              {consultation.description}
            </div>
          </div>
          
          {/* 消息预览区域 */}
          <MessagePreview
            show={showMessagesPreview}
            messages={messages}
            loading={loadingMessages}
            onToggle={onTogglePreview}
          />
        </div>
        
        {/* 弹窗底部操作按钮 */}
        <div className="p-4 border-t border-gray-200">
          <div className="flex justify-between">
            <div className="space-x-2">
              <button
                onClick={() => onPreviewMessages(consultation.id)}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors flex items-center"
              >
                <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
                {showMessagesPreview ? "收起消息" : "快速预览"}
              </button>
              
              <button
                onClick={() => onViewConversation(consultation.id)}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors flex items-center"
              >
                <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
                查看完整会话
              </button>
            </div>
            
            <button
              onClick={onClose}
              className="px-4 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition-colors"
            >
              关闭
            </button>
          </div>
        </div>
      </div>
    </div>
  );
} 