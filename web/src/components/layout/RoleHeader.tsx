'use client';

import { useState, useEffect } from 'react';
import { authService, roleOptions } from '@/service/authService';
import UserInfoBar from '@/components/chat/UserInfoBar';
import { UserRole, AuthUser, Role } from '@/types/auth';
import { WebSocketStatus } from '@/components/WebSocketStatus';
import { useWebSocket } from '@/contexts/WebSocketContext';
import dynamic from 'next/dynamic';

const DigitalHumanToolbar = dynamic(() => import('@/components/layout/DigitalHumanToolbar').then(mod => mod.DigitalHumanToolbar), {
  ssr: false,
  loading: () => <div className="h-12 flex-1 mx-6 bg-gray-50 rounded-xl animate-pulse" />
});

const DigitalHumanDrawer = dynamic(() => import('@/components/layout/DigitalHumanDrawer').then(mod => mod.DigitalHumanDrawer), {
  ssr: false
});
import { DigitalHuman } from '@/types/digital-human';

export default function RoleHeader() {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(null);
  const [roleDetails, setRoleDetails] = useState<Role[]>([]);
  const [isClient, setIsClient] = useState(false);
  const [isLoggingOut, setIsLoggingOut] = useState(false);
  const websocketState = useWebSocket();
  
  // 数字人相关状态
  const [expandedDigitalHuman, setExpandedDigitalHuman] = useState<DigitalHuman | null>(null);
  const [allDigitalHumans, setAllDigitalHumans] = useState<DigitalHuman[]>([]);
  
  // 在组件挂载时确保当前用户信息是最新的
  useEffect(() => {
    setIsClient(true);
    const user = authService.getCurrentUser();
    if (user) {
      setCurrentUser(user);
      // 获取动态角色详情
      authService.getRoleDetails().then(roles => {
        if (roles && roles.length > 0) {
          setRoleDetails(roles);
        }
      });
    }
  }, []);

  // 处理数字人选择
  const handleDigitalHumanSelect = (item: DigitalHuman) => {
    if (expandedDigitalHuman?.id === item.id) {
      // 如果点击已展开的，则关闭
      setExpandedDigitalHuman(null);
    } else {
      // 否则展开新的
      setExpandedDigitalHuman(item);
    }
  };
  
  // 获取角色显示信息（优先使用动态详情，降级使用静态配置）
  const getRoleDisplayInfo = (roleName: string) => {
    const dynamicRole = roleDetails.find(r => r.name === roleName);
    const staticOption = roleOptions.find(r => r.id === roleName);
    
    return {
      name: dynamicRole?.displayName || staticOption?.name || roleName,
      path: staticOption?.path || '/tasks'
    };
  };

  // 获取当前角色信息
  const currentRole = currentUser?.currentRole;
  const currentRoleInfo = currentRole ? getRoleDisplayInfo(currentRole) : null;
  
  // 检查用户是否有多个角色
  const hasMultipleRoles = currentUser?.roles && currentUser.roles.length > 1;
  
  // 角色切换处理函数
  const handleRoleSwitch = async (role: UserRole) => {
    try {
      await authService.switchRole(role);
      setDropdownOpen(false);
      
      window.location.href = '/tasks';
    } catch (error) {
      console.error('角色切换失败', error);
    }
  };
  
  const handleLogout = async () => {
    try {
      // 添加loading状态
      setIsLoggingOut(true);
      // 等待logout完成
      await authService.logout();
      // 登出成功后跳转到登录页
      window.location.href = '/login';
    } catch (error) {
      console.error('登出失败', error);
      // 即使出错也尝试跳转到登录页
      window.location.href = '/login';
    } finally {
      setIsLoggingOut(false);
    }
  };
  
  // 始终返回相同的HTML结构，无论是否有用户信息
  return (
    <header className="sticky top-0 z-10 border-b border-gray-200 bg-white shadow-sm">
      {/* 移动端：只显示数字人工具栏 */}
      <div className="flex h-14 items-center px-3 md:hidden">
        {isClient && (
          <DigitalHumanToolbar 
            selectedId={expandedDigitalHuman?.id}
            onSelect={handleDigitalHumanSelect}
            onLoaded={setAllDigitalHumans}
            searchVariant="collapsible"
            className="mx-0"
          />
        )}
      </div>

      {/* 桌面端：完整头部 */}
      <div className="hidden h-16 items-center justify-between px-4 md:flex">
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
          {/* 不在头部展示“当前角色”徽章（避免出现截图标识1的“客户”文案） */}
          
          {/* 全局 WebSocket 状态指示器 */}
          {websocketState.isEnabled && (
            <div className="ml-4">
              <WebSocketStatus 
                isConnected={websocketState.isConnected}
                connectionStatus={websocketState.connectionStatus}
                isEnabled={websocketState.isEnabled}
                connectionType={websocketState.connectionType}
                connect={websocketState.connect}
                disconnect={websocketState.disconnect}
              />
            </div>
          )}
        </div>
        
        {/* 数字人探索工具栏 - 位于左侧组和右侧用户头像之间 */}
        {isClient && (
          <DigitalHumanToolbar 
            selectedId={expandedDigitalHuman?.id}
            onSelect={handleDigitalHumanSelect}
            onLoaded={setAllDigitalHumans}
          />
        )}
        
        <div className="relative flex-shrink-0">
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
                      const info = getRoleDisplayInfo(role);
                      
                      return (
                        <button
                          key={role}
                          onClick={() => handleRoleSwitch(role)}
                          className={`w-full px-4 py-2 text-left text-sm hover:bg-orange-50 ${
                            currentRole === role ? 'font-medium text-orange-500' : 'text-gray-700'
                          }`}
                        >
                          {info.name}
                        </button>
                      );
                    })}
                  </div>
                )}
                
                <div className="border-b border-gray-100 py-2">
                  <button
                    onClick={() => {
                      setDropdownOpen(false);
                      window.location.href = '/profile';
                    }}
                    className="w-full flex items-center px-4 py-2 text-left text-sm text-gray-700 hover:bg-orange-50"
                  >
                    <svg 
                      className="mr-3 h-4 w-4 text-gray-400" 
                      fill="none" 
                      stroke="currentColor" 
                      viewBox="0 0 24 24"
                    >
                      <path 
                        strokeLinecap="round" 
                        strokeLinejoin="round" 
                        strokeWidth={2} 
                        d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" 
                      />
                    </svg>
                    个人中心
                  </button>
                </div>
                
                <div className="py-1">
                  <button
                    onClick={handleLogout}
                    className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-orange-50"
                    disabled={isLoggingOut}
                  >
                    {isLoggingOut ? (
                      <div className="flex items-center">
                        <div className="h-4 w-4 mr-2 animate-spin rounded-full border-2 border-gray-300 border-t-orange-500"></div>
                        <span>退出中...</span>
                      </div>
                    ) : (
                      "退出登录"
                    )}
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
      
      {/* 数字人聊天抽屉 */}
      <DigitalHumanDrawer
        isOpen={!!expandedDigitalHuman}
        digitalHuman={expandedDigitalHuman}
        onClose={() => setExpandedDigitalHuman(null)}
        onDigitalHumanChange={setExpandedDigitalHuman}
        allDigitalHumans={allDigitalHumans}
      />
    </header>
  );
} 