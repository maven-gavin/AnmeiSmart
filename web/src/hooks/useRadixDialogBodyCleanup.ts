import { useEffect } from 'react';

// Radix Dialog/AlertDialog/Sheet 在极少数情况下可能不会正确清理 body 上的锁定样式
// 现象：弹窗关闭后页面无法点击（body 残留 pointer-events: none / overflow: hidden）
// 这个 hook 在弹窗关闭后做一次“安全兜底清理”，并且仅在页面上没有任何打开的 Radix overlay 时才清理，避免误伤其它弹窗
export function useRadixDialogBodyCleanup(isOpen: boolean) {
  useEffect(() => {
    const cleanupBodyIfSafe = () => {
      // 若仍有其它 Radix overlay 打开，则不要动 body 样式
      const hasAnyOpenOverlay = Boolean(
        document.querySelector('[data-slot$="-overlay"][data-state="open"]')
      );
      if (hasAnyOpenOverlay) return;

      if (document.body.style.pointerEvents === 'none') {
        document.body.style.removeProperty('pointer-events');
      }
      if (document.body.style.overflow === 'hidden') {
        document.body.style.removeProperty('overflow');
      }
    };

    // 弹窗关闭后：下一帧兜底清理（等待 Radix 完成自身清理/动画）
    if (!isOpen) {
      const frameId = requestAnimationFrame(() => {
        requestAnimationFrame(cleanupBodyIfSafe);
      });
      return () => cancelAnimationFrame(frameId);
    }

    // 弹窗仍打开时：如果组件因路由切换/条件渲染被卸载，overlay 会消失，但 body 样式可能残留
    // 因此在 unmount 时也做一次异步安全清理
    return () => {
      requestAnimationFrame(() => {
        requestAnimationFrame(cleanupBodyIfSafe);
      });
    };
  }, [isOpen]);
}


