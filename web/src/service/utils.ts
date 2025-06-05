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
 * 检测设备类型
 * @returns 设备类型
 */
export function detectDeviceType(): DeviceType {
  if (typeof window === 'undefined') {
    return DeviceType.DESKTOP; // SSR环境默认为桌面端
  }

  const userAgent = navigator.userAgent.toLowerCase();
  const screenWidth = window.screen.width;
  
  // 平板检测 - 基于用户代理和屏幕尺寸
  const isTabletUA = /ipad|android(?!.*mobile)|tablet|kindle|silk|playbook|blackberry.*tablet/i.test(userAgent);
  const isTabletScreen = screenWidth >= 768 && screenWidth <= 1024;
  
  if (isTabletUA || (isTabletScreen && /touch/i.test(userAgent))) {
    return DeviceType.TABLET;
  }
  
  // 移动设备检测
  const isMobileUA = /android|webos|iphone|ipod|blackberry|iemobile|opera mini|mobile/i.test(userAgent);
  const isMobileScreen = screenWidth < 768;
  
  if (isMobileUA || isMobileScreen) {
    return DeviceType.MOBILE;
  }
  
  return DeviceType.DESKTOP;
}

/**
 * 生成设备唯一标识
 * 基于浏览器指纹和用户代理信息
 * @returns 设备ID
 */
export function generateDeviceId(): string {
  if (typeof window === 'undefined') {
    return 'ssr-device-' + Date.now(); // SSR环境
  }

  try {
    // 优先使用localStorage中已存储的设备ID
    const storedDeviceId = localStorage.getItem('device_id');
    if (storedDeviceId) {
      return storedDeviceId;
    }

    // 生成基于浏览器特征的设备指纹
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    
    // Canvas指纹
    if (ctx) {
      ctx.textBaseline = 'top';
      ctx.font = '14px Arial';
      ctx.fillText('Device fingerprint', 2, 2);
    }
    const canvasFingerprint = canvas.toDataURL();
    
    // 收集设备特征
    const features = [
      navigator.userAgent,
      navigator.language,
      navigator.platform,
      screen.width,
      screen.height,
      screen.colorDepth,
      new Date().getTimezoneOffset(),
      !!window.sessionStorage,
      !!window.localStorage,
      canvasFingerprint.substring(0, 50) // 只取前50个字符
    ].join('|');
    
    // 简单哈希算法生成设备ID
    let hash = 0;
    for (let i = 0; i < features.length; i++) {
      const char = features.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // 转换为32位整数
    }
    
    const deviceId = `device_${Math.abs(hash)}_${Date.now()}`;
    
    // 存储到localStorage
    localStorage.setItem('device_id', deviceId);
    
    return deviceId;
  } catch (error) {
    console.warn('生成设备ID失败，使用fallback方法:', error);
    // fallback方法
    const fallbackId = `device_fallback_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    try {
      localStorage.setItem('device_id', fallbackId);
    } catch (e) {
      // 如果localStorage不可用，直接返回
    }
    return fallbackId;
  }
}

/**
 * 获取客户端IP地址
 * @returns Promise<string | undefined>
 */
export async function getClientIP(): Promise<string | undefined> {
  try {
    // 方法1: 使用公共IP服务 (推荐用于生产环境)
    const response = await fetch('https://api.ipify.org?format=json', {
      timeout: 5000
    } as any);
    
    if (response.ok) {
      const data = await response.json();
      return data.ip;
    }
  } catch (error) {
    console.warn('通过ipify获取IP失败:', error);
  }
  
  try {
    // 方法2: 备用服务
    const response = await fetch('https://jsonip.com', {
      timeout: 5000
    } as any);
    
    if (response.ok) {
      const data = await response.json();
      return data.ip;
    }
  } catch (error) {
    console.warn('通过jsonip获取IP失败:', error);
  }
  
  try {
    // 方法3: 使用WebRTC获取本地IP（可能被浏览器策略限制）
    return await getLocalIP();
  } catch (error) {
    console.warn('通过WebRTC获取IP失败:', error);
  }
  
  return undefined;
}

/**
 * 通过WebRTC获取本地IP地址
 * @returns Promise<string | undefined>
 */
async function getLocalIP(): Promise<string | undefined> {
  return new Promise((resolve) => {
    if (typeof window === 'undefined' || !window.RTCPeerConnection) {
      resolve(undefined);
      return;
    }

    const pc = new RTCPeerConnection({
      iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
    });

    const timeout = setTimeout(() => {
      pc.close();
      resolve(undefined);
    }, 3000);

    pc.onicecandidate = (event) => {
      if (event.candidate) {
        const candidate = event.candidate.candidate;
        const ipMatch = candidate.match(/(\d+\.\d+\.\d+\.\d+)/);
        if (ipMatch) {
          clearTimeout(timeout);
          pc.close();
          resolve(ipMatch[1]);
        }
      }
    };

    // 创建数据通道以触发ICE候选者收集
    pc.createDataChannel('test');
    pc.createOffer()
      .then(offer => pc.setLocalDescription(offer))
      .catch(() => {
        clearTimeout(timeout);
        pc.close();
        resolve(undefined);
      });
  });
}

/**
 * 获取完整的设备信息
 * @returns Promise<DeviceInfo>
 */
export async function getDeviceInfo(): Promise<DeviceInfo> {
  const deviceType = detectDeviceType();
  const deviceId = generateDeviceId();
  
  let ip: string | undefined;
  try {
    ip = await getClientIP();
  } catch (error) {
    console.warn('获取IP地址失败:', error);
  }

  const deviceInfo: DeviceInfo = {
    type: deviceType,
    isMobile: deviceType === DeviceType.MOBILE,
    isTablet: deviceType === DeviceType.TABLET,
    isDesktop: deviceType === DeviceType.DESKTOP,
    userAgent: typeof window !== 'undefined' ? navigator.userAgent : '',
    deviceId,
    platform: typeof window !== 'undefined' ? navigator.platform : '',
    screenWidth: typeof window !== 'undefined' ? window.screen.width : 0,
    screenHeight: typeof window !== 'undefined' ? window.screen.height : 0,
    ip
  };

  return deviceInfo;
}

/**
 * 获取WebSocket配置的设备优化参数
 * 根据设备类型返回优化的WebSocket配置
 * @param deviceInfo 设备信息
 * @returns WebSocket配置参数
 */
export function getWebSocketDeviceConfig(deviceInfo: DeviceInfo) {
  // 移动设备配置 - 更长的超时时间
  if (deviceInfo.isMobile) {
    return {
      connectionTimeout: 30000,      // 移动端30秒超时
      heartbeatInterval: 60000,      // 移动端60秒心跳
      reconnectInterval: 3000,       // 移动端3秒重连间隔
      maxReconnectDelay: 45000       // 移动端最大45秒重连延迟
    };
  }
  
  // 平板设备配置 - 中等超时时间
  if (deviceInfo.isTablet) {
    return {
      connectionTimeout: 25000,      // 平板25秒超时
      heartbeatInterval: 50000,      // 平板50秒心跳
      reconnectInterval: 2500,       // 平板2.5秒重连间隔
      maxReconnectDelay: 35000       // 平板最大35秒重连延迟
    };
  }
  
  // 桌面设备配置 - 标准配置
  return {
    connectionTimeout: 20000,        // 桌面20秒超时
    heartbeatInterval: 45000,        // 桌面45秒心跳
    reconnectInterval: 2000,         // 桌面2秒重连间隔
    maxReconnectDelay: 30000         // 桌面最大30秒重连延迟
  };
}

/**
 * 格式化设备信息用于日志或显示
 * @param deviceInfo 设备信息
 * @returns 格式化的设备信息字符串
 */
export function formatDeviceInfo(deviceInfo: DeviceInfo): string {
  return `${deviceInfo.type.toUpperCase()} | ${deviceInfo.platform} | ${deviceInfo.screenWidth}x${deviceInfo.screenHeight} | ID: ${deviceInfo.deviceId.substring(0, 12)}... | IP: ${deviceInfo.ip || 'unknown'}`;
}
