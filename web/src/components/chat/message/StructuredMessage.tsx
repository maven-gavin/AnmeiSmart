'use client';

import React from 'react';
import { Message, StructuredMessageContent } from '@/types/chat';

interface StructuredMessageProps {
  message: Message;
  onAction?: (action: string, data: any) => void;
}

const StructuredMessage: React.FC<StructuredMessageProps> = ({
  message,
  onAction
}) => {
  const content = message.content as StructuredMessageContent;

  const renderServiceRecommendation = (data: { services: any[] }) => {
    return (
      <div className="p-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-3">{content.title}</h3>
        
        <div className="space-y-3">
          {data.services.map((service, index) => (
            <div key={index} className="border border-gray-200 rounded-lg p-3 hover:bg-gray-50 transition-colors">
              <div className="flex justify-between items-start mb-2">
                <h4 className="font-medium text-gray-900">{service.name}</h4>
                <span className="text-blue-600 font-semibold">¥{service.price}</span>
              </div>
              <p className="text-sm text-gray-600 mb-2">{service.description}</p>
              <div className="text-xs text-gray-500">
                时长：{service.duration} 分钟 | 适合：{service.suitableFor}
              </div>
            </div>
          ))}
        </div>

        {content.actions?.primary && (
          <button
            onClick={() => onAction?.(content.actions!.primary!.action, content.actions!.primary!.data)}
            className="w-full mt-4 bg-blue-600 text-white py-2 px-4 rounded-lg font-medium 
                     hover:bg-blue-700 transition-colors"
          >
            {content.actions.primary.text}
          </button>
        )}
      </div>
    );
  };

  const renderCustomCard = () => {
    return (
      <div className="p-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-3">{content.title}</h3>
        {content.subtitle && (
          <p className="text-gray-600 mb-3">{content.subtitle}</p>
        )}
        
        {/* 渲染自定义数据 */}
        <div className="bg-gray-50 rounded-lg p-3 mb-3">
          <pre className="text-sm text-gray-700 whitespace-pre-wrap">
            {JSON.stringify(content.data, null, 2)}
          </pre>
        </div>

        {/* 渲染组件 */}
        {content.components?.map((component, index) => (
          <div key={index} className="mb-2">
            {component.type === 'text' && (
              <p className="text-sm text-gray-700">{component.content}</p>
            )}
            {component.type === 'button' && (
              <button
                onClick={() => onAction?.(component.action?.type || 'custom', component.action?.data)}
                className="px-3 py-1 bg-blue-100 text-blue-700 rounded text-sm hover:bg-blue-200 transition-colors"
              >
                {component.content}
              </button>
            )}
            {component.type === 'divider' && (
              <hr className="border-gray-200" />
            )}
          </div>
        ))}
      </div>
    );
  };

  const renderCardContent = () => {
    switch (content.card_type) {
      case 'service_recommendation':
        return renderServiceRecommendation(content.data as { services: any[] });
      
      case 'consultation_summary':
      case 'custom':
      default:
        return renderCustomCard();
    }
  };

  return (
    <div className="max-w-sm mx-auto">
      {renderCardContent()}
    </div>
  );
};

export default StructuredMessage; 