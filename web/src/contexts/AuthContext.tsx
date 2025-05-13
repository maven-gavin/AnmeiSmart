'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { AuthUser, UserRole } from '@/types/auth';
import { authService } from '@/lib/authService';

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

  // 初始化时检查本地存储的认证信息
  useEffect(() => {
    const initAuth = () => {
      try {
        const storedUser = authService.getCurrentUser();
        const storedToken = authService.getToken();
        
        if (storedUser && storedToken) {
          setUser(storedUser);
          setToken(storedToken);
        }
      } catch (err) {
        console.error('初始化认证状态失败', err);
      } finally {
        setLoading(false);
      }
    };

    initAuth();
  }, []);

  // 登录
  const login = async (username: string, password: string) => {
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
  };

  // 退出登录
  const logout = async () => {
    setLoading(true);
    
    try {
      await authService.logout();
      setUser(null);
      setToken(null);
      
      // 重定向到登录页
      if (!pathname.startsWith('/login')) {
        router.push('/login');
      }
    } catch (err) {
      console.error('退出登录失败', err);
    } finally {
      setLoading(false);
    }
  };

  // 切换角色
  const switchRole = async (role: UserRole) => {
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
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        error,
        login,
        logout,
        switchRole,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

// 自定义钩子，方便在组件中使用
export function useAuth() {
  const context = useContext(AuthContext);
  
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
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
      return <div className="flex h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-gray-300 border-t-orange-500"></div>
      </div>;
    }
    
    return user ? <Component {...props} /> : null;
  };
} 