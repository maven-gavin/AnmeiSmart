import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * 设备类型枚举
 */
export enum DeviceType {
  MOBILE = 'mobile',
  TABLET = 'tablet',
  DESKTOP = 'desktop'
}

/**
 * 设备信息接口
 */
export interface DeviceInfo {
  type: DeviceType;
  isMobile: boolean;
  isTablet: boolean;
  isDesktop: boolean;
  userAgent: string;
  deviceId: string;
  platform: string;
  screenWidth: number;
  screenHeight: number;
  ip?: string;
}

/**
 * 简化的设备类型检测
 */
export function detectDeviceType(): DeviceType {
  if (typeof window === 'undefined') {
    return DeviceType.DESKTOP;
  }

  const userAgent = navigator.userAgent.toLowerCase();
  const screenWidth = window.screen.width;
  
  // 简化的移动设备检测
  if (/android|webos|iphone|ipod|blackberry|iemobile|opera mini|mobile/i.test(userAgent) || screenWidth < 768) {
    return DeviceType.MOBILE;
  }
  
  // 简化的平板检测
  if (/ipad|tablet/i.test(userAgent) || (screenWidth >= 768 && screenWidth <= 1024)) {
    return DeviceType.TABLET;
  }
  
  return DeviceType.DESKTOP;
}

/**
 * 简化的设备ID生成
 */
export function generateDeviceId(): string {
  if (typeof window === 'undefined') {
    return 'ssr-device-' + Date.now();
  }

  try {
    // 优先使用localStorage中已存储的设备ID
    const storedDeviceId = localStorage.getItem('device_id');
    if (storedDeviceId) {
      return storedDeviceId;
    }

    // 简化的设备指纹
    const features = [
      navigator.userAgent,
      navigator.language,
      screen.width,
      screen.height,
      new Date().getTimezoneOffset()
    ].join('|');
    
    // 简单哈希
    let hash = 0;
    for (let i = 0; i < features.length; i++) {
      const char = features.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash;
    }
    
    const deviceId = `device_${Math.abs(hash)}_${Date.now()}`;
    localStorage.setItem('device_id', deviceId);
    return deviceId;
  } catch (error) {
    // 回退方案
    const fallbackId = `device_fallback_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    try {
      localStorage.setItem('device_id', fallbackId);
    } catch (e) {
      // 忽略localStorage错误
    }
    return fallbackId;
  }
}

/**
 * 获取设备信息
 */
export async function getDeviceInfo(): Promise<DeviceInfo> {
  const deviceType = detectDeviceType();
  const deviceId = generateDeviceId();

  const deviceInfo: DeviceInfo = {
    type: deviceType,
    isMobile: deviceType === DeviceType.MOBILE,
    isTablet: deviceType === DeviceType.TABLET,
    isDesktop: deviceType === DeviceType.DESKTOP,
    userAgent: typeof window !== 'undefined' ? navigator.userAgent : 'Server-Side',
    deviceId,
    platform: typeof window !== 'undefined' ? navigator.platform : 'Server',
    screenWidth: typeof window !== 'undefined' ? window.screen.width : 0,
    screenHeight: typeof window !== 'undefined' ? window.screen.height : 0,
    ip: 'unknown' // 简化：不再获取IP
  };

  return deviceInfo;
}

/**
 * 简化的WebSocket设备配置
 */
export function getWebSocketDeviceConfig(deviceInfo: DeviceInfo) {
  // 统一配置，不再区分设备类型
  return {
    connectionTimeout: 20000,
    heartbeatInterval: 45000,
    reconnectInterval: 2000,
    maxReconnectDelay: 30000
  };
}

/**
 * 格式化设备信息
 */
export function formatDeviceInfo(deviceInfo: DeviceInfo): string {
  return `${deviceInfo.type.toUpperCase()} | ${deviceInfo.platform} | ${deviceInfo.screenWidth}x${deviceInfo.screenHeight} | ID: ${deviceInfo.deviceId.substring(0, 12)}...`;
}
