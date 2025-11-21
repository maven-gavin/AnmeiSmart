import React from 'react';
import { Badge } from '@/components/ui/badge';

interface RoleBadgeProps {
  role: string;
  className?: string;
}

export const RoleBadge: React.FC<RoleBadgeProps> = ({ role, className }) => {
  const getRoleStyle = (roleName: string) => {
    const styles: Record<string, string> = {
      admin: 'bg-red-100 text-red-800 border-red-200 hover:bg-red-200',
      consultant: 'bg-blue-100 text-blue-800 border-blue-200 hover:bg-blue-200',
      doctor: 'bg-green-100 text-green-800 border-green-200 hover:bg-green-200',
      customer: 'bg-purple-100 text-purple-800 border-purple-200 hover:bg-purple-200',
      operator: 'bg-yellow-100 text-yellow-800 border-yellow-200 hover:bg-yellow-200'
    };
    
    return styles[roleName] || 'bg-gray-100 text-gray-800 border-gray-200 hover:bg-gray-200';
  };

  const getRoleLabel = (roleName: string) => {
    const labels: Record<string, string> = {
      admin: '管理员',
      consultant: '顾问',
      doctor: '医生',
      customer: '客户',
      operator: '运营'
    };
    return labels[roleName] || roleName;
  };

  return (
    <Badge variant="outline" className={`${getRoleStyle(role)} ${className}`}>
      {getRoleLabel(role)}
    </Badge>
  );
};

