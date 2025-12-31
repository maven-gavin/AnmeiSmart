import { useState, useEffect } from 'react';

/**
 * 检测窗口宽度是否小于指定断点
 * 使用 matchMedia API 优化性能，并在初始化时读取，减少首次渲染闪动
 * @param breakpoint 断点值，默认 768px（移动端）
 * @returns 是否小于断点
 */
export function useMediaQuery(breakpoint: number = 768): boolean {
  // 在客户端初始化时立即读取，避免首次渲染闪动
  const [isMobile, setIsMobile] = useState<boolean>(() => {
    if (typeof window === 'undefined') {
      return false;
    }
    // 使用与 matchMedia 一致的逻辑：max-width: ${breakpoint - 1}px
    return window.innerWidth <= (breakpoint - 1);
  });

  useEffect(() => {
    // 服务端渲染时直接返回
    if (typeof window === 'undefined') {
      return;
    }

    // 使用 matchMedia API 优化性能
    const mediaQuery = window.matchMedia(`(max-width: ${breakpoint - 1}px)`);
    
    // 更新状态函数
    const handleChange = (e: MediaQueryListEvent | MediaQueryList) => {
      setIsMobile(e.matches);
    };

    // 初始检查（matchMedia 支持直接调用）
    handleChange(mediaQuery);

    // 监听变化（使用 addEventListener，兼容新旧 API）
    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', handleChange);
      return () => {
        mediaQuery.removeEventListener('change', handleChange);
      };
    } else {
      // 兼容旧版浏览器（使用 addListener）
      mediaQuery.addListener(handleChange);
      return () => {
        mediaQuery.removeListener(handleChange);
      };
    }
  }, [breakpoint]);

  return isMobile;
}

