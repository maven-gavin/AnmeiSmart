'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode, useCallback, useMemo } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { AuthUser, UserRole } from '@/types/auth';
import { authService } from '@/service/authService';

interface AuthContextType {
  user: AuthUser | null;
  token: string | null;
  loading: boolean;
  error: string | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  switchRole: (role: UserRole) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [tokenCheckInterval, setTokenCheckInterval] = useState<NodeJS.Timeout | null>(null);

  // 校验并刷新Token，使用useCallback优化
  const validateAndRefreshToken = useCallback(async () => {
    try {
      // 使用authService.getValidToken代替手动检查和刷新逻辑
      const validToken = await authService.getValidToken();
      
      // 如果返回有效token，更新状态
      if (validToken) {
        setToken(validToken);
      } else {
        // 如果没有有效token（refreshToken失败或没有token），清除用户状态
        setUser(null);
        setToken(null);
        
        // 如果不在登录页面，重定向到登录页
        if (!pathname.startsWith('/login')) {
          router.push('/login');
        }
      }
    } catch (err) {
      console.error('验证Token时出错', err);
      setError('认证会话暂时异常，请稍后再试');
    }
  }, [pathname, router]);

  // 登录函数，使用useCallback优化
  const login = useCallback(async (username: string, password: string) => {
    setLoading(true);
    setError(null);
    
    try {
      const { user, token } = await authService.login({ username, password });
      setUser(user);
      setToken(token);
    } catch (err) {
      setError(err instanceof Error ? err.message : '登录失败');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // 退出登录函数，使用useCallback优化
  const logout = useCallback(async () => {
    setLoading(true);
    
    try {
      await authService.logout();
      setUser(null);
      setToken(null);
      setError(null);
      
      if (tokenCheckInterval) {
        clearInterval(tokenCheckInterval);
        setTokenCheckInterval(null);
      }
      
      if (!pathname.startsWith('/login')) {
        router.push('/login');
      }
    } catch (err) {
      console.error('退出登录失败', err);
    } finally {
      setLoading(false);
    }
  }, [pathname, router, tokenCheckInterval]);

  // 切换角色函数，使用useCallback优化
  const switchRole = useCallback(async (role: UserRole) => {
    if (!user) {
      setError('用户未登录');
      return;
    }
    
    setLoading(true);
    
    try {
      const updatedUser = await authService.switchRole(role);
      setUser(updatedUser);
    } catch (err) {
      setError(err instanceof Error ? err.message : '角色切换失败');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [user]);

  // 初始化认证状态
  useEffect(() => {
    const initAuth = async () => {
      try {
        const storedUser = authService.getCurrentUser();
        // 使用getValidToken替代手动检查token有效性
        const validToken = await authService.getValidToken();
        
        setUser(storedUser);
        setToken(validToken);
        
        // 如果没有有效token但有存储的用户信息，清除用户信息
        if (!validToken && storedUser) {
          setUser(null);
        }
      } catch (err) {
        console.error('初始化认证状态失败', err);
        // 出错时清除状态
        setUser(null);
        setToken(null);
      } finally {
        setLoading(false);
      }
    };

    initAuth();
    
    // 定期检查token
    const interval = setInterval(validateAndRefreshToken, 10 * 60 * 1000);
    setTokenCheckInterval(interval);
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [validateAndRefreshToken]);

  // 路由保护逻辑
  useEffect(() => {
    if (!loading) {
      const needsLogin = !user && !pathname.startsWith('/login');
      if (needsLogin) {
        router.push('/login');
      }
    }
  }, [user, loading, pathname, router]);

  // 使用useMemo优化Context值，避免不必要的重渲染
  const contextValue = useMemo(() => ({
    user,
    token,
    loading,
    error,
    login,
    logout,
    switchRole,
  }), [user, token, loading, error, login, logout, switchRole]);

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
}

// 自定义钩子，方便在组件中使用
export function useAuth() {
  const context = useContext(AuthContext);
  
  if (context === undefined) {
    throw new Error('useAuth必须在AuthProvider内部使用');
  }
  
  return context;
}

// 受保护路由高阶组件
export function withAuth<P extends object>(Component: React.ComponentType<P>) {
  return function ProtectedRoute(props: P) {
    const { user, loading } = useAuth();
    const router = useRouter();
    const pathname = usePathname();
    
    useEffect(() => {
      if (!loading && !user && !pathname.startsWith('/login')) {
        router.push('/login');
      }
    }, [user, loading, router, pathname]);
    
    if (loading) {
      return (
        <div className="flex h-screen items-center justify-center">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-gray-300 border-t-orange-500"></div>
        </div>
      );
    }
    
    return user ? <Component {...props} /> : null;
  };
} 