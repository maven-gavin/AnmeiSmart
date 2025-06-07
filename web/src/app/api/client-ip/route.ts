import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    // 尝试从各种头部获取真实客户端IP
    const forwarded = request.headers.get('x-forwarded-for');
    const realIp = request.headers.get('x-real-ip');
    const clientIp = request.headers.get('x-client-ip');
    const forwardedFor = request.headers.get('forwarded');
    
    let ip: string | null = null;
    
    // 优先级顺序：x-real-ip > x-forwarded-for > x-client-ip > forwarded
    if (realIp) {
      ip = realIp;
    } else if (forwarded) {
      // x-forwarded-for 可能包含多个IP，取第一个
      ip = forwarded.split(',')[0]?.trim();
    } else if (clientIp) {
      ip = clientIp;
    } else if (forwardedFor) {
      // 解析 Forwarded 头部（RFC 7239）
      const match = forwardedFor.match(/for=([^;,\s]+)/);
      if (match) {
        ip = match[1];
        // 移除可能的引号和端口号
        ip = ip.replace(/["\[\]]/g, '').split(':')[0];
      }
    }
    
    // 如果没有找到转发的IP，尝试其他方法
    if (!ip) {
      // 尝试从URL中获取（如果有的话）
      const url = new URL(request.url);
      const searchParams = url.searchParams;
      const urlIp = searchParams.get('ip');
      
      if (urlIp) {
        ip = urlIp;
      } else {
        // 最后使用默认值
        ip = 'unknown';
      }
    }
    
    // 清理IP地址
    if (ip && ip !== 'unknown') {
      // 移除IPv6的前缀
      if (ip.startsWith('::ffff:')) {
        ip = ip.substring(7);
      }
      
      // 验证IP格式
      const ipv4Regex = /^(\d{1,3}\.){3}\d{1,3}$/;
      const ipv6Regex = /^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$/;
      
      if (!ipv4Regex.test(ip) && !ipv6Regex.test(ip)) {
        ip = 'invalid';
      }
    }
    
    return NextResponse.json({ 
      ip: ip || 'unknown',
      headers: {
        'x-forwarded-for': forwarded,
        'x-real-ip': realIp,
        'x-client-ip': clientIp,
        'forwarded': forwardedFor
      }
    });
    
  } catch (error) {
    console.error('获取客户端IP失败:', error);
    return NextResponse.json({ 
      ip: 'error',
      error: 'Failed to get client IP' 
    }, { status: 500 });
  }
} 