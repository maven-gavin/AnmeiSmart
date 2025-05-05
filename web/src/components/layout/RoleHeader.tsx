import { useState } from 'react';
import { authService } from '@/lib/authService';
import { roleOptions } from '@/lib/mockData';
import UserInfoBar from '@/components/chat/UserInfoBar'
import RoleSelector from '@/components/ui/RoleSelector';

export default function RoleHeader() {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const currentUser = authService.getCurrentUser();
  const currentRole = currentUser?.currentRole;
  
  // 获取当前角色信息
  const roleInfo = roleOptions.find(r => r.id === currentRole);
  
  // 检查用户是否有多个角色
  const hasMultipleRoles = currentUser?.roles && currentUser.roles.length > 1;
  
  const handleLogout = async () => {
    await authService.logout();
    window.location.href = '/';
  };
  
  if (!currentUser || !roleInfo) {
    return null;
  }
  
  return (
    <header className="sticky top-0 z-10 border-b border-gray-200 bg-white shadow-sm">
      <div className=" flex h-16 items-center justify-between">
        <div className="flex items-center">
          <img 
            src="/logo.svg" 
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
          
          {/* 角色标识 */}
          <div className="ml-6 rounded-full bg-orange-100 px-3 py-1 text-sm font-medium text-orange-700">
            {roleInfo.name}
          </div>
        </div>
        
        <div className="relative">
          <button 
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="flex items-center space-x-2 rounded-lg p-2 hover:bg-gray-100"
          > 
            <UserInfoBar />
          </button>
          
          {dropdownOpen && (
            <div className="absolute right-0 mt-2 w-56 origin-top-right rounded-md bg-white shadow-lg ring-1 ring-black ring-opacity-5">
              <div className="p-2">
                <div className="border-b border-gray-100 pb-2">
                  <p className="px-4 py-2 text-sm text-gray-500">已登录为 {currentUser.name}</p>
                </div>
                
                {hasMultipleRoles && (
                  <div className="border-b border-gray-100 py-2">
                    <p className="px-4 py-1 text-xs text-gray-500">切换角色</p>
                    {currentUser.roles.map(role => {
                      const roleInfo = roleOptions.find(r => r.id === role);
                      if (!roleInfo) return null;
                      
                      return (
                        <button
                          key={role}
                          onClick={() => {
                            authService.switchRole(role);
                            setDropdownOpen(false);
                            window.location.href = roleInfo.path;
                          }}
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