import { Page } from '@playwright/test';
import { apiClient } from '@/service/apiClient';

/**
 * 顾客用户登录
 */
export async function loginAsCustomer(page: Page, email: string): Promise<void> {
  await page.goto('/login');
  
  // 适配 Shadcn/UI 组件
  await page.getByLabel('邮箱').fill(email);
  await page.getByLabel('密码').fill('password123'); // 假设密码
  
  // Shadcn 的按钮通常会有特定的类或属性
  await page.getByRole('button', { name: '登录' }).click();
  
  // 等待导航完成，基于 Next.js 路由
  await page.waitForURL('**/customer/**');
}

/**
 * 顾问用户登录
 */
export async function loginAsConsultant(page: Page, email: string): Promise<void> {
  await page.goto('/login');
  
  // 适配 Shadcn/UI 组件
  await page.getByLabel('邮箱').fill(email);
  await page.getByLabel('密码').fill('password123'); // 假设密码
  
  await page.getByRole('button', { name: '登录' }).click();
  
  // 等待导航完成
  await page.waitForURL('**/consultant/**');
}

/**
 * 创建测试会话 - 使用 apiClient
 */
export async function createTestConversation(): Promise<string> {
  try {
    // 使用 apiClient 创建会话
    const response = await apiClient.post('conversations', {
      customer_email: 'customer1@example.com', 
      title: `测试会话 ${new Date().toISOString()}`
    });
    
    if (!response.ok) {
      console.error('创建会话响应错误:', response.status, response.data);
      throw new Error(`创建会话失败: ${response.status}`);
    }
    
    return response.data.id;
  } catch (error) {
    console.error('创建测试会话失败:', error);
    // 如果创建失败，返回一个已知存在的会话ID
    return '1'; // 默认会话ID
  }
}

/**
 * 获取会话消息 - 通过API
 */
export async function getConversationMessages(conversationId: string): Promise<any[]> {
  try {
    const response = await apiClient.get(`conversations/${conversationId}/messages`);
    if (!response.ok) {
      throw new Error(`获取会话消息失败: ${response.status}`);
    }
    return response.data.messages || [];
  } catch (error) {
    console.error('获取会话消息失败:', error);
    return [];
  }
}

/**
 * 在页面中设置认证状态 - 适用于 Next.js 的认证
 */
export async function setupAuth(page: Page, userEmail: string, userRole: 'customer' | 'consultant'): Promise<void> {
  // 使用 localStorage 或 cookies 根据您的实际身份验证实现
  // 示例：为 Context API 设置认证状态
  await page.evaluate(({ email, role }) => {
    localStorage.setItem('authToken', 'test-token'); // 模拟令牌
    localStorage.setItem('user', JSON.stringify({
      id: '123',
      email,
      name: email.split('@')[0],
      currentRole: role
    }));
  }, { email: userEmail, role: userRole });
  
  // 刷新页面使认证状态生效
  await page.reload();
}

/**
 * 等待特定的UI状态 - 优化异步等待
 */
export async function waitForChatReady(page: Page): Promise<void> {
  // 等待聊天容器加载完成 - Shadcn/UI 通常有特定类名
  await page.waitForSelector('.flex-1.overflow-y-auto', { state: 'visible' });
  
  // 等待WebSocket连接状态指示器不可见（如果有）
  const hasConnectionError = await page.getByText('连接服务器失败').isVisible();
  if (hasConnectionError) {
    // 如果显示连接错误，点击重新连接
    await page.getByRole('button', { name: '重新连接' }).click();
    // 等待连接建立
    await page.waitForTimeout(1000);
  }
} 