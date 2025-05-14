'use client';

import { useState, useEffect } from 'react';
import { authService, roleOptions } from '@/service/authService';
import UserInfoBar from '@/components/chat/UserInfoBar'
import { UserRole, AuthUser } from '@/types/auth';

export default function RoleHeader() {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(null);
  const [isClient, setIsClient] = useState(false);
  
  // 在组件挂载时确保当前用户信息是最新的
  useEffect(() => {
    setIsClient(true);
    const user = authService.getCurrentUser();
    if (user) {
      setCurrentUser(user);
    }
  }, []);
  
  // 获取当前角色信息
  const currentRole = currentUser?.currentRole;
  const roleInfo = currentRole ? roleOptions.find(r => r.id === currentRole) : null;
  
  // 检查用户是否有多个角色
  const hasMultipleRoles = currentUser?.roles && currentUser.roles.length > 1;
  
  // 角色切换处理函数
  const handleRoleSwitch = async (role: UserRole) => {
    try {
      await authService.switchRole(role);
      setDropdownOpen(false);
      
      // 使用替代方式进行导航，避免直接刷新导致加载问题
      const targetRole = roleOptions.find(r => r.id === role);
      if (targetRole) {
        window.location.href = targetRole.path;
      }
    } catch (error) {
      console.error('角色切换失败', error);
    }
  };
  
  const handleLogout = async () => {
    try {
      await authService.logout();
      window.location.href = '/';
    } catch (error) {
      console.error('登出失败', error);
    }
  };
  
  // 始终返回相同的HTML结构，无论是否有用户信息
  return (
    <header className="sticky top-0 z-10 border-b border-gray-200 bg-white shadow-sm">
      <div className="flex h-16 items-center justify-between px-4">
        <div className="flex items-center">
          <img 
            src="/logo.ico" 
            alt="安美智享" 
            className="mr-3 h-10 w-10"
            onError={(e) => {
              // 如果SVG加载失败，尝试使用PNG，最后使用文本替代
              const target = e.target as HTMLImageElement;
              if (target.src.endsWith('logo.svg')) {
                target.src = '/logo.png';
              } else if (target.src.endsWith('logo.png')) {
                target.onerror = null; // 防止循环错误
                target.style.display = 'none';
              }
            }}
          />
          <h1 className="text-xl font-bold text-gray-800">安美智享</h1>
          
          {/* 角色标识 - 只在客户端且有roleInfo时显示内容 */}
          {isClient && roleInfo && (
            <div className="ml-6 rounded-full bg-orange-100 px-3 py-1 text-sm font-medium text-orange-700">
              {roleInfo.name}
            </div>
          )}
          
          {/* 占位元素，保持布局一致 */}
          {(!isClient || !roleInfo) && (
            <div className="ml-6 rounded-full bg-gray-100 px-3 py-1 text-sm font-medium text-gray-400">
              加载中...
            </div>
          )}
        </div>
        
        <div className="relative">
          {/* 将UserInfoBar移出按钮，避免嵌套不一致 */}
          <div 
            onClick={() => isClient && setDropdownOpen(!dropdownOpen)}
            className="flex items-center rounded-lg p-2 hover:bg-gray-100 cursor-pointer"
          >
            <UserInfoBar />
          </div>
          
          {isClient && currentUser && dropdownOpen && (
            <div className="absolute right-0 mt-2 w-56 origin-top-right rounded-md bg-white shadow-lg ring-1 ring-black ring-opacity-5">
              <div className="p-2">
                <div className="border-b border-gray-100 pb-2">
                  <p className="px-4 py-2 text-sm text-gray-500">已登录为 {currentUser.name}</p>
                </div>
                
                {hasMultipleRoles && currentUser.roles && (
                  <div className="border-b border-gray-100 py-2">
                    <p className="px-4 py-1 text-xs text-gray-500">切换角色</p>
                    {currentUser.roles.map((role: UserRole) => {
                      const roleInfo = roleOptions.find(r => r.id === role);
                      if (!roleInfo) return null;
                      
                      return (
                        <button
                          key={role}
                          onClick={() => handleRoleSwitch(role)}
                          className={`w-full px-4 py-2 text-left text-sm hover:bg-orange-50 ${
                            currentRole === role ? 'font-medium text-orange-500' : 'text-gray-700'
                          }`}
                        >
                          {roleInfo.name}
                        </button>
                      );
                    })}
                  </div>
                )}
                
                <div className="py-1">
                  <button
                    onClick={handleLogout}
                    className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-orange-50"
                  >
                    退出登录
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
} 