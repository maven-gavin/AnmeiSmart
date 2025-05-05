import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { UserRole } from '@/types/auth';
import { authService } from '@/lib/authService';
import { roleOptions } from '@/lib/mockData';

interface RoleSelectorProps {
  onRoleSelect?: (role: UserRole) => void;
  className?: string;
}

export default function RoleSelector({ onRoleSelect, className = '' }: RoleSelectorProps) {
  const router = useRouter();
  const currentUser = authService.getCurrentUser();
  const [selectedRole, setSelectedRole] = useState<UserRole | undefined>(
    currentUser?.currentRole
  );

  // 过滤出当前用户拥有的角色
  const availableRoles = roleOptions.filter(role => 
    currentUser?.roles.includes(role.id)
  );

  const handleRoleSelect = async (role: UserRole) => {
    try {
      setSelectedRole(role);
      
      // 切换用户角色
      if (currentUser) {
        await authService.switchRole(role);
      }
      
      // 调用回调
      if (onRoleSelect) {
        onRoleSelect(role);
      }
      
      // 导航到对应角色的首页
      const selectedRoleOption = roleOptions.find(r => r.id === role);
      if (selectedRoleOption) {
        router.push(selectedRoleOption.path);
      }
    } catch (error) {
      console.error('角色切换失败', error);
    }
  };

  if (!currentUser || availableRoles.length === 0) {
    return null;
  }

  return (
    <div className={`p-4 ${className}`}>
      <h3 className="mb-4 text-lg font-medium text-gray-800">选择角色</h3>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 md:grid-cols-3">
        {availableRoles.map((role) => (
          <button
            key={role.id}
            onClick={() => handleRoleSelect(role.id)}
            className={`flex items-center rounded-lg border p-3 transition-all hover:border-orange-500 hover:bg-orange-50 ${
              selectedRole === role.id 
                ? 'border-orange-500 bg-orange-50' 
                : 'border-gray-200'
            }`}
          >
            <div 
              className={`mr-3 flex h-10 w-10 items-center justify-center rounded-full ${
                selectedRole === role.id 
                  ? 'bg-orange-500 text-white' 
                  : 'bg-gray-100 text-gray-500'
              }`}
            >
              {/* 使用图标或首字母作为图标 */}
              {role.name.charAt(0)}
            </div>
            <div>
              <p className="font-medium text-gray-800">{role.name}</p>
              <p className="text-sm text-gray-500">
                {role.id === 'advisor' 
                  ? '客户沟通与方案推荐'
                  : role.id === 'doctor'
                  ? '方案录入与风险评估'
                  : '数据分析与审核管理'}
              </p>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
} 