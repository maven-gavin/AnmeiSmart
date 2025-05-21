'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
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

  // 校验并刷新Token
  const validateAndRefreshToken = async () => {
    try {
      const currentToken = authService.getToken();
      
      // 如果没有token，直接返回
      if (!currentToken) return;
      
      // 检查token是否过期或即将过期
      if (authService.isTokenExpired(currentToken)) {
        console.log('Token已过期或即将过期，尝试刷新');
        try {
          // 尝试刷新token
          const newToken = await authService.refreshToken();
          setToken(newToken);
          console.log('Token刷新成功');
        } catch (err) {
          console.error('Token刷新失败，需要重新登录', err);
          // 刷新失败，执行登出操作
          await logout();
        }
      }
    } catch (err) {
      console.error('验证Token时出错', err);
    }
  };

  // 初始化时检查本地存储的认证信息
  useEffect(() => {
    const initAuth = async () => {
      try {
        const storedUser = authService.getCurrentUser();
        const storedToken = authService.getToken();
        
        // 设置初始状态
        setUser(storedUser);
        setToken(storedToken);
        
        if (storedUser && storedToken) {
          // 验证token有效性，但不要在这里重定向，避免闪烁
          if (authService.isTokenExpired(storedToken)) {
            console.log('存储的Token已过期，尝试刷新');
            try {
              // 尝试刷新token，但保持当前状态不变，避免闪烁
              const newToken = await authService.refreshToken();
              setToken(newToken);
            } catch (err) {
              console.error('Token刷新失败，需要重新登录', err);
              // 刷新失败，清除认证信息，但不立即重定向
              await authService.logout();
              setUser(null);
              setToken(null);
            }
          }
        }
      } catch (err) {
        console.error('初始化认证状态失败', err);
      } finally {
        setLoading(false);
      }
    };

    // 只有在第一次加载时执行初始化
    initAuth();
    
    // 设置定时器，定期检查token
    const interval = setInterval(validateAndRefreshToken, 5 * 60 * 1000); // 每5分钟检查一次
    setTokenCheckInterval(interval);
    
    return () => {
      // 清理定时器
      if (tokenCheckInterval) {
        clearInterval(tokenCheckInterval);
      }
    };
  }, []);

  // 添加单独的重定向逻辑，与初始化状态分离
  useEffect(() => {
    // 只有在确认加载完成后才检查重定向
    if (!loading) {
      const needsLogin = !user && !pathname.startsWith('/login');
      if (needsLogin) {
        console.log('用户未登录，重定向到登录页');
        router.push('/login');
      }
    }
  }, [user, loading, pathname, router]);

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
      
      // 清除token检查定时器
      if (tokenCheckInterval) {
        clearInterval(tokenCheckInterval);
        setTokenCheckInterval(null);
      }
      
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