'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { useAuthContext } from '@/contexts/AuthContext';

// 测试账号配置
const TEST_ACCOUNTS = [
  {
    id: 'qinglong',
    name: '青龙',
    icon: '🐉',
    username: 'customer3@qq.com',
    password: 'Sh@nghai1',
    color: 'from-blue-500 to-blue-600',
    hoverColor: 'hover:from-blue-600 hover:to-blue-700',
    position: 'top',
  },
  {
    id: 'baihu',
    name: '白虎',
    icon: '🐅',
    username: 'admin@anmeismart.com',
    password: 'Admin@123456',
    color: 'from-gray-400 to-gray-500',
    hoverColor: 'hover:from-gray-500 hover:to-gray-600',
    position: 'right',
  },
  {
    id: 'zhuque',
    name: '朱雀',
    icon: '🦅',
    username: 'customer1@example.com',
    password: '123456@Test',
    color: 'from-red-500 to-red-600',
    hoverColor: 'hover:from-red-600 hover:to-red-700',
    position: 'bottom',
  },
  {
    id: 'xuanwu',
    name: '玄武',
    icon: '🐢',
    username: 'zhang@example.com',
    password: '123456@Test',
    color: 'from-green-600 to-green-700',
    hoverColor: 'hover:from-green-700 hover:to-green-800',
    position: 'left',
  },
  {
    id: 'qilin',
    name: '麒麟',
    icon: '🦌',
    username: 'wang@example.com',
    password: '123456@Test',
    color: 'from-orange-500 to-orange-600',
    hoverColor: 'hover:from-orange-600 hover:to-orange-700',
    position: 'center',
  },
];

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
  const [showForm, setShowForm] = useState(false); // 控制表单显示

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

  const handleLogin = async (accountUsername: string, accountPassword: string) => {
    setLoading(true);
    setError('');
    
    try {
      // 使用AuthContext的login方法
      await login(accountUsername, accountPassword);
      
      // 获取跳转URL（如果有）
      const params = new URLSearchParams(window.location.search);
      const returnUrl = params.get('returnUrl');
      
      if (returnUrl) {
        router.push(decodeURIComponent(returnUrl));
      } else {
        router.push('/tasks');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '登录失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!username || !password) {
      setError('请输入用户名和密码');
      return;
    }
    
    await handleLogin(username, password);
  };

  const isLoading = loading || authLoading;
  const errorMessage = error || authError;

  // 测试账号快捷登录界面
  if (!showForm) {
    const centerAccount = TEST_ACCOUNTS.find(acc => acc.position === 'center')!;
    const topAccount = TEST_ACCOUNTS.find(acc => acc.position === 'top')!;
    const rightAccount = TEST_ACCOUNTS.find(acc => acc.position === 'right')!;
    const bottomAccount = TEST_ACCOUNTS.find(acc => acc.position === 'bottom')!;
    const leftAccount = TEST_ACCOUNTS.find(acc => acc.position === 'left')!;

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
                  if (logoSrc === '/logo.ico') {
                    setLogoSrc('/logo.png');
                  } else {
                    setLogoError(true);
                  }
                }}
              />
            )}
          </div>
          <h1 className="text-2xl font-bold text-gray-800">安美智享</h1>
          <p className="text-gray-500">智能服务平台</p>
        </div>

        {errorMessage && (
          <div className="mb-6 rounded-md bg-red-50 p-3 text-sm text-red-500">
            {errorMessage}
          </div>
        )}

        {/* 五神兽登录按钮布局 */}
        <div className="relative mx-auto h-80 w-80 flex items-center justify-center">
          {/* 上方：青龙 */}
          <button
            onClick={() => handleLogin(topAccount.username, topAccount.password)}
            disabled={isLoading}
            className={`absolute top-0 left-1/2 flex h-20 w-20 -translate-x-1/2 flex-col items-center justify-center rounded-full bg-gradient-to-br ${topAccount.color} ${topAccount.hoverColor} shadow-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed active:scale-95`}
            title={topAccount.name}
          >
            <span className="text-3xl">{topAccount.icon}</span>
            <span className="mt-1 text-xs font-medium text-white">{topAccount.name}</span>
          </button>

          {/* 右侧：白虎 */}
          <button
            onClick={() => handleLogin(rightAccount.username, rightAccount.password)}
            disabled={isLoading}
            className={`absolute right-0 top-1/2 flex h-20 w-20 -translate-y-1/2 flex-col items-center justify-center rounded-full bg-gradient-to-br ${rightAccount.color} ${rightAccount.hoverColor} shadow-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed active:scale-95`}
            title={rightAccount.name}
          >
            <span className="text-3xl">{rightAccount.icon}</span>
            <span className="mt-1 text-xs font-medium text-white">{rightAccount.name}</span>
          </button>

          {/* 下方：朱雀 */}
          <button
            onClick={() => handleLogin(bottomAccount.username, bottomAccount.password)}
            disabled={isLoading}
            className={`absolute bottom-0 left-1/2 flex h-20 w-20 -translate-x-1/2 flex-col items-center justify-center rounded-full bg-gradient-to-br ${bottomAccount.color} ${bottomAccount.hoverColor} shadow-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed active:scale-95`}
            title={bottomAccount.name}
          >
            <span className="text-3xl">{bottomAccount.icon}</span>
            <span className="mt-1 text-xs font-medium text-white">{bottomAccount.name}</span>
          </button>

          {/* 左侧：玄武 */}
          <button
            onClick={() => handleLogin(leftAccount.username, leftAccount.password)}
            disabled={isLoading}
            className={`absolute left-0 top-1/2 flex h-20 w-20 -translate-y-1/2 flex-col items-center justify-center rounded-full bg-gradient-to-br ${leftAccount.color} ${leftAccount.hoverColor} shadow-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed active:scale-95`}
            title={leftAccount.name}
          >
            <span className="text-3xl">{leftAccount.icon}</span>
            <span className="mt-1 text-xs font-medium text-white">{leftAccount.name}</span>
          </button>

          {/* 中心：麒麟 */}
          <button
            onClick={() => handleLogin(centerAccount.username, centerAccount.password)}
            disabled={isLoading}
            className={`relative z-10 flex h-24 w-24 flex-col items-center justify-center rounded-full bg-gradient-to-br ${centerAccount.color} ${centerAccount.hoverColor} shadow-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed active:scale-95`}
            title={centerAccount.name}
          >
            <span className="text-4xl">{centerAccount.icon}</span>
            <span className="mt-1 text-sm font-semibold text-white">{centerAccount.name}</span>
            {isLoading && (
              <span className="absolute inset-0 flex items-center justify-center rounded-full bg-black/20">
                <span className="h-6 w-6 animate-spin rounded-full border-2 border-white border-t-transparent"></span>
              </span>
            )}
          </button>
        </div>

        <div className="mt-12 text-center">
          <button
            onClick={() => setShowForm(true)}
            className="text-sm text-gray-400 hover:text-gray-600 underline"
            disabled={isLoading}
          >
            使用账号密码登录
          </button>
        </div>
      </div>
    );
  }

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
        </form>

        <div className="mt-4 text-center">
          <button
            onClick={() => setShowForm(false)}
            className="text-sm text-gray-400 hover:text-gray-600 underline"
            disabled={isLoading}
          >
            返回测试账号登录
          </button>
        </div>
    </div>
  );
} 