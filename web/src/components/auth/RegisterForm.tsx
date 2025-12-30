'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { useAuthContext } from '@/contexts/AuthContext';

export default function RegisterForm() {
  const router = useRouter();
  const { register, error: authError } = useAuthContext();
  const [formData, setFormData] = useState({
    phone: '',
    username: '',
    email: '',
    password: '',
    confirmPassword: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    // 清除错误信息
    if (error) setError('');
  };

  const validateForm = () => {
    const { phone, username, email, password, confirmPassword } = formData;

    if (!phone || !username || !email || !password || !confirmPassword) {
      setError('请填写所有必填项');
      return false;
    }

    // 验证手机号格式
    const phoneRegex = /^1[3-9]\d{9}$/;
    if (!phoneRegex.test(phone)) {
      setError('请输入正确的手机号码');
      return false;
    }

    // 验证邮箱格式
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      setError('请输入正确的邮箱地址');
      return false;
    }

    // 验证用户名长度
    if (username.length < 3 || username.length > 50) {
      setError('用户名长度应在3-50个字符之间');
      return false;
    }

    // 验证密码强度
    if (password.length < 8) {
      setError('密码长度至少8个字符');
      return false;
    }

    // 验证密码包含字母和数字
    const passwordRegex = /^(?=.*[A-Za-z])(?=.*\d)/;
    if (!passwordRegex.test(password)) {
      setError('密码必须包含字母和数字');
      return false;
    }

    // 验证确认密码
    if (password !== confirmPassword) {
      setError('两次输入的密码不一致');
      return false;
    }

    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      await register({
        phone: formData.phone,
        username: formData.username,
        email: formData.email,
        password: formData.password
      });
      
      // 注册成功，跳转到任务管理
      router.push('/tasks');
    } catch (err) {
      setError(err instanceof Error ? err.message : '注册失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  const isLoading = loading;
  const errorMessage = error || authError;

  return (
    <div className="mx-auto max-w-md rounded-xl bg-white p-8 shadow-md w-full">
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
        <h1 className="text-2xl font-bold text-gray-800">注册账号</h1>
        <p className="text-gray-500">创建您的安美智享账号</p>
      </div>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label 
            htmlFor="phone" 
            className="mb-2 block text-sm font-medium text-gray-700"
          >
            手机号 *
          </label>
          <input
            id="phone"
            type="tel"
            value={formData.phone}
            onChange={(e) => handleInputChange('phone', e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-orange-500 focus:outline-none"
            placeholder="请输入手机号"
            disabled={isLoading}
          />
        </div>

        <div>
          <label 
            htmlFor="username" 
            className="mb-2 block text-sm font-medium text-gray-700"
          >
            用户名 *
          </label>
          <input
            id="username"
            type="text"
            value={formData.username}
            onChange={(e) => handleInputChange('username', e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-orange-500 focus:outline-none"
            placeholder="请输入用户名"
            disabled={isLoading}
          />
        </div>
        
        <div>
          <label 
            htmlFor="email" 
            className="mb-2 block text-sm font-medium text-gray-700"
          >
            邮箱 *
          </label>
          <input
            id="email"
            type="email"
            value={formData.email}
            onChange={(e) => handleInputChange('email', e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-orange-500 focus:outline-none"
            placeholder="请输入邮箱地址"
            disabled={isLoading}
          />
        </div>
        
        <div>
          <label 
            htmlFor="password" 
            className="mb-2 block text-sm font-medium text-gray-700"
          >
            密码 *
          </label>
          <input
            id="password"
            type="password"
            value={formData.password}
            onChange={(e) => handleInputChange('password', e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-orange-500 focus:outline-none"
            placeholder="请输入密码"
            disabled={isLoading}
          />
        </div>

        <div>
          <label 
            htmlFor="confirmPassword" 
            className="mb-2 block text-sm font-medium text-gray-700"
          >
            确认密码 *
          </label>
          <input
            id="confirmPassword"
            type="password"
            value={formData.confirmPassword}
            onChange={(e) => handleInputChange('confirmPassword', e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-orange-500 focus:outline-none"
            placeholder="请再次输入密码"
            disabled={isLoading}
          />
        </div>

        <div className="text-xs text-gray-500">
          <p>• 手机号将作为您的账号标识</p>
          <p>• 密码至少8位，需包含字母和数字</p>
          <p>• 注册即表示同意《用户协议》和《隐私政策》</p>
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
              注册中...
            </span>
          ) : (
            '注册账号'
          )}
        </Button>

        <div className="mt-4 text-center text-sm text-gray-500">
          <span>已有账号？</span>
          <button
            type="button"
            onClick={() => router.push('/login')}
            className="ml-1 text-orange-500 hover:underline"
            disabled={isLoading}
          >
            立即登录
          </button>
        </div>
      </form>
    </div>
  );
} 