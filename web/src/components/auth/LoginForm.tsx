'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { useAuthContext } from '@/contexts/AuthContext';
import { authService } from '@/service/authService';

export default function LoginForm() {
  const router = useRouter();
  const { login, error: authError, loading: authLoading } = useAuthContext();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [logoError, setLogoError] = useState(false);
  const [logoSrc, setLogoSrc] = useState('/logo.ico');
  const [mounted, setMounted] = useState(false);

  // 标记组件已挂载（仅在客户端）
  useEffect(() => {
    setMounted(true);
  }, []);

  // 从URL参数中获取错误信息（仅在客户端挂载后）
  useEffect(() => {
    if (!mounted) return;
    
    const params = new URLSearchParams(window.location.search);
    const errorMsg = params.get('error');
    if (errorMsg) {
      setError(decodeURIComponent(errorMsg));
    }
  }, [mounted]);

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
      
      // 获取当前用户信息（使用 authService 而不是直接访问 localStorage）
      const user = authService.getCurrentUser();
      
      // 获取跳转URL（如果有）
      const params = new URLSearchParams(window.location.search);
      const returnUrl = params.get('returnUrl');
      
      if (returnUrl) {
        router.push(decodeURIComponent(returnUrl));
      } else {
        //如果用户设置了首选角色，就进入首选角色，反之进入默认角色
        if (user) {
          console.log("===============", JSON.stringify(user));
          // const role = user.currentRole || (user.roles && user.roles[0]);
          // const path = role === 'consultant' ? '/consultant' : 
          //             role === 'doctor' ? '/doctor' : 
          //             role === 'admin' ? '/admin' :
          //             role === 'operator' ? '/operator' : 
          //             role === 'customer' ? '/customer' : '/other';
        }
        router.push('/home');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '登录失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  const isLoading = loading || authLoading;
  const errorMessage = error || authError;

  return (
    <div className="mx-auto max-w-md rounded-xl bg-white p-8 shadow-md">
      <div className="mb-8 text-center">
        <div className="mx-auto mb-4 h-16 w-16 flex items-center justify-center">
          {logoError ? (
            <div className="h-16 w-16 rounded-full bg-orange-500 flex items-center justify-center text-white text-3xl font-bold">
              @
            </div>
          ) : (
            <img 
              src={logoSrc} 
              alt="安美智享" 
              className="h-16 w-16" 
              onError={() => {
                // 如果当前是 .ico，尝试 .png
                if (logoSrc === '/logo.ico') {
                  setLogoSrc('/logo.png');
                } else {
                  // 如果 .png 也失败，显示替代图标
                  setLogoError(true);
                }
              }}
            />
          )}
        </div>
        <h1 className="text-2xl font-bold text-gray-800">安美智享</h1>
        <p className="text-gray-500">智能服务平台</p>
      </div>
      
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
            
            <div className="flex items-center">
              <a href="#" className="text-orange-200 hover:underline">
                忘记密码？
              </a>
              &nbsp;&nbsp;
              <button
                type="button"
                onClick={() => router.push('/register')}
                className="text-orange-500 hover:underline"
                disabled={isLoading}
              >
                注册账号
              </button>
            </div>
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
            <p className="mt-2 font-medium text-orange-600">客户账号：customer1@example.com / 123456@Test</p>
          </div>
        </form>
    </div>
  );
} 