/**
 * 数字人相关工具函数
 */
import { User, Building, Zap, Shield, Bot } from 'lucide-react';

export type DigitalHumanType = 'personal' | 'business' | 'specialized' | 'system';

export function getDigitalHumanTypeStyle(type: string): string {
  const styles: Record<string, string> = {
    personal: 'bg-blue-100 text-blue-800',
    business: 'bg-purple-100 text-purple-800',
    specialized: 'bg-green-100 text-green-800',
    system: 'bg-orange-100 text-orange-800',
  };
  return styles[type] || 'bg-gray-100 text-gray-800';
}

export function getDigitalHumanTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    personal: '个人助手',
    business: '商务助手',
    specialized: '专业助手',
    system: '系统助手',
  };
  return labels[type] || type;
}

export function getDigitalHumanTypeIcon(type: string) {
  switch (type) {
    case 'personal':
      return <User className="h-4 w-4" />;
    case 'business':
      return <Building className="h-4 w-4" />;
    case 'specialized':
      return <Zap className="h-4 w-4" />;
    case 'system':
      return <Shield className="h-4 w-4" />;
    default:
      return <Bot className="h-4 w-4" />;
  }
}

export function formatDigitalHumanDate(dateString?: string | null): string {
  if (!dateString) return '从未';
  try {
    return new Date(dateString).toLocaleString('zh-CN');
  } catch {
    return '无效日期';
  }
}


