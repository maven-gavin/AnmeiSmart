'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import RoleSelector from '@/components/ui/RoleSelector';
import { UserRole } from '@/types/auth';
import { useAuth } from '@/contexts/AuthContext';

export default function LoginForm() {
  const router = useRouter();
  const { login, error: authError, loading: authLoading } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showRoleSelector, setShowRoleSelector] = useState(false);
  const [availableRoles, setAvailableRoles] = useState<UserRole[]>([]);

  // 从URL参数中获取错误信息和跳转URL
  useEffect(() => {
    // 获取当前URL参数
    const params = new URLSearchParams(window.location.search);
    const errorMsg = params.get('error');
    
    // 如果有错误信息，设置错误状态
    if (errorMsg) {
      setError(decodeURIComponent(errorMsg));
    }
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!username || !password) {
      setError('请输入用户名和密码');
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      // 使用AuthContext的login方法
      await login(username, password);
      
      // 获取当前用户信息
      const user = JSON.parse(localStorage.getItem('auth_user') || '{}');
      
      // 获取跳转URL（如果有）
      const params = new URLSearchParams(window.location.search);
      const returnUrl = params.get('returnUrl');
      
      // 如果用户有多个角色，显示角色选择器
      if (user.roles && user.roles.length > 1) {
        setAvailableRoles(user.roles);
        setShowRoleSelector(true);
      } else if (user.roles && user.roles.length === 1) {
        // 只有一个角色时，直接跳转到对应角色的页面或returnUrl
        if (returnUrl) {
          router.push(decodeURIComponent(returnUrl));
        } else {
          const role = user.roles[0];
          const path = role === 'consultant' ? '/consultant' : 
                      role === 'doctor' ? '/doctor' : 
                      role === 'admin' ? '/admin' :
                      role === 'operator' ? '/operator' : 
                      role === 'customer' ? '/customer' : '/other';
          router.push(path);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '登录失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  const handleRoleSelect = (role: UserRole) => {
    // RoleSelector 组件会自行处理路由导航
  };

  const isLoading = loading || authLoading;
  const errorMessage = error || authError;

  return (
    <div className="mx-auto max-w-md rounded-xl bg-white p-8 shadow-md">
      <div className="mb-8 text-center">
        <div className="mx-auto mb-4 h-16 w-16 flex items-center justify-center">
          <img 
            src="/logo.ico" 
            alt="安美智享" 
            className="h-16 w-16" 
            onError={(e) => {
              // 如果SVG加载失败，尝试使用PNG，最后使用文本替代
              const target = e.target as HTMLImageElement;
              if (target.src.endsWith('logo.svg')) {
                target.src = '/logo.png';
              } else if (target.src.endsWith('logo.png')) {
                target.onerror = null; // 防止循环错误
                // 创建一个圆形的替代图标
                const parent = target.parentElement as HTMLElement;
                parent.innerHTML = '';
                parent.style.backgroundColor = '#FF9800';
                parent.style.borderRadius = '50%';
                parent.style.color = '#FFFFFF';
                parent.style.fontSize = '32px';
                parent.style.fontWeight = 'bold';
                parent.innerText = '@';
              }
            }}
          />
        </div>
        <h1 className="text-2xl font-bold text-gray-800">安美智享</h1>
        <p className="text-gray-500">医美智能服务平台</p>
      </div>
      
      {showRoleSelector ? (
        <div>
          <h2 className="mb-4 text-center text-lg font-medium text-gray-800">选择角色</h2>
          <RoleSelector onRoleSelect={handleRoleSelect} />
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label 
              htmlFor="username" 
              className="mb-2 block text-sm font-medium text-gray-700"
            >
              手机号/邮箱
            </label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-orange-500 focus:outline-none"
              placeholder="请输入手机号或邮箱"
              disabled={isLoading}
            />
          </div>
          
          <div>
            <label 
              htmlFor="password" 
              className="mb-2 block text-sm font-medium text-gray-700"
            >
              密码
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-orange-500 focus:outline-none"
              placeholder="请输入密码"
              disabled={isLoading}
            />
          </div>
          
          <div className="flex justify-between text-sm">
            <label className="flex items-center">
              <input 
                type="checkbox" 
                className="mr-2 h-4 w-4 text-orange-500"
              />
              记住我
            </label>
            <a href="#" className="text-orange-500 hover:underline">
              忘记密码？
            </a>
          </div>
          
          {errorMessage && (
            <div className="rounded-md bg-red-50 p-3 text-sm text-red-500">
              {errorMessage}
            </div>
          )}
          
          <Button
            type="submit"
            className="w-full"
            disabled={isLoading}
          >
            {isLoading ? (
              <span className="flex items-center justify-center">
                <span className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"></span>
                登录中...
              </span>
            ) : (
              '登录'
            )}
          </Button>
          
          <div className="mt-4 text-center text-sm text-gray-500">
            <p>演示账号：zhang@example.com</p>
            <p>演示密码：123456@Test</p>
            <p>管理员账号：admin@anmeismart.com</p>
            <p>管理员密码：Admin@123456</p>
            <p className="mt-2 font-medium text-orange-600">顾客账号：customer1@example.com / 123456@Test</p>
          </div>
        </form>
      )}
    </div>
  );
} 