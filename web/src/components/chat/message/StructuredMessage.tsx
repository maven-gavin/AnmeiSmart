'use client';

import React from 'react';
import { Message, StructuredMessageContent, AppointmentCardData } from '@/types/chat';
import { MessageUtils } from '@/utils/messageUtils';

interface StructuredMessageProps {
  message: Message;
  onAction?: (action: string, data: any) => void;
}

const StructuredMessage: React.FC<StructuredMessageProps> = ({
  message,
  onAction
}) => {
  const content = message.content as StructuredMessageContent;

  const renderAppointmentCard = (data: AppointmentCardData) => {
    const formatDateTime = (dateString: string) => {
      const date = new Date(dateString);
      return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    };

    const getStatusColor = (status: string) => {
      switch (status) {
        case 'confirmed': return 'text-green-600 bg-green-50';
        case 'pending': return 'text-orange-600 bg-orange-50';
        case 'cancelled': return 'text-red-600 bg-red-50';
        default: return 'text-gray-600 bg-gray-50';
      }
    };

    const getStatusText = (status: string) => {
      switch (status) {
        case 'confirmed': return '已确认';
        case 'pending': return '待确认';
        case 'cancelled': return '已取消';
        default: return '未知状态';
      }
    };

    return (
      <div className="p-4">
        {/* 卡片标题 */}
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-semibold text-gray-900">{content.title}</h3>
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(data.status)}`}>
            {getStatusText(data.status)}
          </span>
        </div>

        {/* 服务信息 */}
        <div className="bg-blue-50 rounded-lg p-3 mb-3">
          <h4 className="font-medium text-blue-900 mb-1">{data.service_name}</h4>
          <p className="text-sm text-blue-700">时长：{data.duration_minutes} 分钟</p>
          <p className="text-sm text-blue-700">价格：¥{data.price}</p>
        </div>

        {/* 时间和地点 */}
        <div className="space-y-2 mb-3">
          <div className="flex items-center text-gray-600">
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            <span className="text-sm">{formatDateTime(data.scheduled_time)}</span>
          </div>
          <div className="flex items-center text-gray-600">
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            <span className="text-sm">{data.location}</span>
          </div>
        </div>

        {/* 顾问信息 */}
        <div className="flex items-center mb-3 p-2 bg-gray-50 rounded-lg">
          <img
            src={data.consultant_avatar || '/avatars/consultant.png'}
            alt={data.consultant_name}
            className="w-8 h-8 rounded-full mr-3"
          />
          <div>
            <p className="text-sm font-medium text-gray-900">{data.consultant_name}</p>
            <p className="text-xs text-gray-500">您的专属顾问</p>
          </div>
        </div>

        {/* 备注 */}
        {data.notes && (
          <div className="mb-3 p-2 bg-yellow-50 border-l-4 border-yellow-200">
            <p className="text-sm text-yellow-800">
              <span className="font-medium">备注：</span>{data.notes}
            </p>
          </div>
        )}

        {/* 操作按钮 */}
        {content.actions && data.status === 'pending' && (
          <div className="flex gap-2 pt-3 border-t border-gray-200">
            {content.actions.primary && (
              <button
                onClick={() => onAction?.(content.actions!.primary!.action, content.actions!.primary!.data)}
                className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg font-medium 
                         hover:bg-blue-700 transition-colors text-sm"
              >
                {content.actions.primary.text}
              </button>
            )}
            {content.actions.secondary && (
              <button
                onClick={() => onAction?.(content.actions!.secondary!.action, content.actions!.secondary!.data)}
                className="flex-1 bg-gray-200 text-gray-700 py-2 px-4 rounded-lg font-medium 
                         hover:bg-gray-300 transition-colors text-sm"
              >
                {content.actions.secondary.text}
              </button>
            )}
          </div>
        )}
      </div>
    );
  };

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
      case 'appointment_confirmation':
        return renderAppointmentCard(content.data as AppointmentCardData);
      
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