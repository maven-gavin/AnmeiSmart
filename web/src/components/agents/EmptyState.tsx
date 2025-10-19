'use client';

import { MessageCircle } from 'lucide-react';
import type { AgentConfig } from '@/service/agentConfigService';
import { UserInputForm } from './UserInputForm';
import type { ApplicationParameters } from '@/types/agent-chat';

interface EmptyStateProps {
  agentConfig: AgentConfig;
  appConfig: ApplicationParameters;
  onSendMessage?: (message: string, formData?: Record<string, any>) => void;
}

export function EmptyState({ agentConfig, appConfig, onSendMessage }: EmptyStateProps) {
  // 格式化开场白文本，支持编号列表等格式
  const formatOpeningStatement = (text: string) => {
    // 处理编号列表格式 (1. 2. 3.)
    const numberedListRegex = /^(\d+\.\s+.*)$/gm;
    const lines = text.split('\n');
    
    return lines.map((line, index) => {
      const trimmedLine = line.trim();
      
      // 检查是否是编号列表项
      if (numberedListRegex.test(trimmedLine)) {
        return (
          <div key={index} className="flex items-start mb-2">
            <span className="text-blue-600 font-medium mr-2 flex-shrink-0">
              {trimmedLine.match(/^\d+\./)?.[0]}
            </span>
            <span className="text-blue-800">
              {trimmedLine.replace(/^\d+\.\s+/, '')}
            </span>
          </div>
        );
      }
      
      // 普通文本行
      if (trimmedLine) {
        return (
          <p key={index} className="text-blue-800 leading-relaxed mb-2">
            {trimmedLine}
          </p>
        );
      }
      
      // 空行
      return <br key={index} />;
    });
  };

  // 处理推荐问题点击
  const handleSuggestedQuestionClick = (question: string) => {
    if (onSendMessage) {
      onSendMessage(question);
    }
  };

  // 处理表单提交
  const handleFormSubmit = (formData: Record<string, any>) => {
    if (onSendMessage) {
      // 如果有开场白，直接开始对话；否则发送表单数据
      const message = appConfig?.opening_statement || '开始对话';
      onSendMessage(message, formData);
    }
  };

  // 检查是否有用户输入表单
  const hasUserInputForm = appConfig?.user_input_form && appConfig.user_input_form.length > 0;

  // 如果有开场白，优先显示开场白
  if (appConfig?.opening_statement) { 
    return (
      <div className="flex h-full items-center justify-center p-6">
        <div className="max-w-2xl w-full space-y-6">
          <div className="text-center">
            <MessageCircle className="mx-auto h-12 w-12 text-blue-500" />
            <h3 className="mt-3 text-lg font-medium text-gray-900">
              {agentConfig.appName}
            </h3>
          </div>

          {/* 用户输入表单（如果有） */}
          {hasUserInputForm && (
            <UserInputForm
              fields={appConfig.user_input_form!}
              onSubmit={handleFormSubmit}
            />
          )}
          
          {/* 开场白消息气泡 */}
          <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
            <div className="flex items-start">
              <div className="flex-shrink-0">
                <MessageCircle className="h-5 w-5 text-blue-500 mt-0.5" />
              </div>
              <div className="ml-3 flex-1">
                <div className="text-sm text-gray-800 leading-relaxed">
                  {formatOpeningStatement(appConfig.opening_statement)}
                </div>
              </div>
            </div>
          </div>

          {/* 推荐问题 */}
          {appConfig.suggested_questions && appConfig.suggested_questions.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-3">推荐问题：</h4>
              <div className="space-y-2">
                {appConfig.suggested_questions.map((question, index) => (
                  <button
                    key={index}
                    onClick={() => handleSuggestedQuestionClick(question)}
                    className="block w-full text-left text-sm text-blue-600 hover:text-blue-800 hover:bg-blue-50 p-2 rounded-md transition-colors duration-200"
                  >
                    {question}
                  </button>
                ))}
              </div>
            </div>
          )}

          <p className="text-center text-sm text-gray-500">
            输入您的问题开始对话
          </p>
        </div>
      </div>
    );
  }

  // 默认显示状态
  return (
    <div className="flex h-full items-center justify-center">
      <div className="text-center">
          <div>
            <MessageCircle className="mx-auto h-16 w-16 text-gray-300" />
            <h3 className="mt-4 text-lg font-medium text-gray-900">
              与 {agentConfig.appName} 开始对话
            </h3>
            <p className="mt-2 text-sm text-gray-500">
              输入您的问题，AI 助手将为您提供帮助
            </p>
          </div>
      </div>
    </div>
  );
}

