import { Page } from '@playwright/test';
import { apiClient } from '@/service/apiClient';

// 导入测试配置
const config = require('../test.config');

// 存储获取的token
let consultantToken: string | null = null;
let customerToken: string | null = null;

/**
 * 通过API登录并获取顾问令牌
 * @returns 是否登录成功
 */
export async function loginConsultantAPIAndGetToken(email: string = config.users.consultant.email, password: string = config.users.consultant.password): Promise<boolean> {
  try {
    console.log(`尝试顾问API登录: ${email}, 密码长度: ${password.length}`);
    
    // 直接使用node-fetch - 尝试使用URLSearchParams而不是JSON
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);
    
    // 使用表单提交格式 - 这是OAuth2的标准格式
    const response = await fetch(`${config.api.baseUrl}${config.api.auth.login}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData
    });

    // 读取响应内容
    const responseText = await response.text();
    console.log('顾问登录响应:', response.status, responseText.substring(0, 100) + '...');
    
    // 如果响应成功，则解析JSON获取令牌
    if (response.ok) {
      try {
        const data = JSON.parse(responseText);
        consultantToken = data.access_token;
        console.log('成功获取顾问认证令牌');
        
        // 暴露给全局对象，以便测试文件可以访问
        (global as any).consultantToken = consultantToken;
        
        return true;
      } catch (e) {
        console.error('解析顾问令牌失败:', e);
        throw new Error('解析顾问令牌失败');
      }
    } else {
      throw new Error(`顾问登录失败: ${response.status} ${responseText}`);
    }
  } catch (error) {
    console.error('顾问API登录失败:', error);
    throw error;
  }
}

/**
 * 通过API登录并获取顾客令牌
 * @returns 是否登录成功
 */
export async function loginCustomerAPIAndGetToken(email: string = config.users.customer.email, password: string = config.users.customer.password): Promise<boolean> {
  try {
    console.log(`尝试顾客API登录: ${email}, 密码长度: ${password.length}`);
    
    // 直接使用node-fetch - 尝试使用URLSearchParams而不是JSON
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);
    
    // 使用表单提交格式 - 这是OAuth2的标准格式
    const response = await fetch(`${config.api.baseUrl}${config.api.auth.login}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData
    });

    // 读取响应内容
    const responseText = await response.text();
    console.log('顾客登录响应:', response.status, responseText.substring(0, 100) + '...');
    
    // 如果响应成功，则解析JSON获取令牌
    if (response.ok) {
      try {
        const data = JSON.parse(responseText);
        customerToken = data.access_token;
        console.log('成功获取顾客认证令牌');
        
        // 暴露给全局对象，以便测试文件可以访问
        (global as any).customerToken = customerToken;
        
        return true;
      } catch (e) {
        console.error('解析顾客令牌失败:', e);
        throw new Error('解析顾客令牌失败');
      }
    } else {
      throw new Error(`顾客登录失败: ${response.status} ${responseText}`);
    }
  } catch (error) {
    console.error('顾客API登录失败:', error);
    throw error;
  }
}

/**
 * 使用顾客身份创建测试会话
 * 更符合实际业务场景：顾客发起咨询 -> 创建会话
 */
export async function createCustomerTestConversation(): Promise<string> {
  console.log('尝试使用顾客身份创建会话...');
  
  // 如果没有顾客令牌，尝试登录
  if (!customerToken) {
    const success = await loginCustomerAPIAndGetToken();
    if (!success) {
      throw new Error('无法获取顾客认证令牌');
    }
  }
  
  // 使用配置中定义的端点
  const createConversationEndpoint = config.api.chat.createConversation;
  console.log(`API端点: ${config.api.baseUrl}${createConversationEndpoint}`);
  
  // 创建会话请求
  const requestBody = {
    customer_id: config.users.customer.id,
    title: `顾客咨询 ${new Date().toISOString()}`
  };
  
  console.log('请求体:', JSON.stringify(requestBody));
  
  try {
    const response = await fetch(`${config.api.baseUrl}${createConversationEndpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${customerToken}`
      },
      body: JSON.stringify(requestBody),
    });
    
    const responseText = await response.text();
    console.log(`创建会话响应:`, response.status, responseText);
    
    if (response.ok) {
      try {
        const data = JSON.parse(responseText);
        console.log(`顾客成功创建会话:`, data);
        return data.id;
      } catch (e) {
        console.error('解析创建会话响应失败:', e);
        throw new Error('解析创建会话响应失败');
      }
    } else {
      throw new Error(`创建会话失败: ${response.status} ${responseText}`);
    }
  } catch (error) {
    console.error(`创建会话失败:`, error);
    throw error;
  }
}

/**
 * 获取会话消息
 */
export async function getConversationMessages(conversationId: string, useConsultantToken: boolean = true): Promise<any[]> {
  try {
    // 确定使用哪个令牌
    let token = useConsultantToken ? consultantToken : customerToken;
    
    // 如果没有所需令牌，尝试登录获取
    if (!token) {
      let success = false;
      if (useConsultantToken) {
        success = await loginConsultantAPIAndGetToken();
        token = consultantToken;
      } else {
        success = await loginCustomerAPIAndGetToken();
        token = customerToken;
      }
      
      if (!success || !token) {
        throw new Error(`无法获取${useConsultantToken ? '顾问' : '顾客'}认证令牌`);
      }
    }
    
    // 获取消息列表
    const messagesEndpoint = config.api.chat.getMessages(conversationId);
    
    const response = await fetch(`${config.api.baseUrl}${messagesEndpoint}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    if (response.ok) {
      const data = await response.json();
      return data;
    } else {
      const text = await response.text();
      throw new Error(`获取会话消息失败: ${response.status} ${text}`);
    }
  } catch (error) {
    console.error('获取会话消息失败:', error);
    throw error;
  }
}

/**
 * 获取顾问认证令牌
 */
export function getConsultantToken(): string | null {
  return consultantToken;
}

/**
 * 获取顾客认证令牌
 */
export function getCustomerToken(): string | null {
  return customerToken;
}


/**
 * 顾客UI登录
 */
export async function loginAsCustomer(page: Page, email: string = config.users.customer.email): Promise<void> {
  await page.goto('/login');
  await page.waitForLoadState('domcontentloaded');
  
  await page.getByLabel('邮箱').fill(email);
  await page.getByLabel('密码').fill(config.users.customer.password);
  await page.getByRole('button', { name: '登录' }).click();
  
  // 等待登录完成 - 检查URL变化或特定元素出现
  await page.waitForURL(/\/customer\//, { timeout: config.timeouts.pageLoad });
}

/**
 * 顾问UI登录
 */
export async function loginAsConsultant(page: Page, email: string = config.users.consultant.email): Promise<void> {
  await page.goto('/login');
  await page.waitForLoadState('domcontentloaded');
  
  await page.getByLabel('邮箱').fill(email);
  await page.getByLabel('密码').fill(config.users.consultant.password);
  await page.getByRole('button', { name: '登录' }).click();
  
  // 等待登录完成 - 检查URL变化或特定元素出现
  await page.waitForURL(/\/consultant\//, { timeout: config.timeouts.pageLoad });
}

/**
 * 在页面中设置身份验证令牌
 */
export async function setupAuthToken(page: Page, token: string): Promise<void> {
  await page.evaluate((authToken) => {
    localStorage.setItem('token', authToken);
  }, token);
}

/**
 * 等待聊天页面准备就绪
 */
export async function waitForChatReady(page: Page): Promise<void> {
  console.log('等待聊天界面准备就绪...');
  
  try {
    // 1. 等待页面加载完成
    await page.waitForLoadState('domcontentloaded', { timeout: config.timeouts.pageLoad });
    
    // 2. 等待主要聊天容器出现
    const chatContainer = page.locator('.chat-container, .conversation-container, .messages-container, [data-testid="chat-container"]').first();
    await chatContainer.waitFor({ state: 'visible', timeout: config.timeouts.elementAppear });
    
    // 3. 等待输入框出现 - 这通常表示聊天UI已完全加载
    const inputField = page.getByPlaceholder('输入消息...') || 
                      page.locator('textarea[placeholder], input[placeholder]').first();
    await inputField.waitFor({ state: 'visible', timeout: config.timeouts.elementAppear });
    
    // 4. 等待网络活动平静
    await page.waitForLoadState('networkidle', { timeout: config.timeouts.ajaxRequest });
    
    // 5. 给页面一些额外时间确保WebSocket连接建立
    await page.waitForTimeout(1000);
    
    console.log('聊天界面已准备就绪');
  } catch (error) {
    console.error('等待聊天界面准备就绪失败:', error);
    throw new Error('聊天界面未能正常加载');
  }
}

/**
 * 检查是否处于顾问模式
 */
export async function isConsultantMode(page: Page): Promise<boolean> {
  try {
    // 检查URL路径
    const url = page.url();
    if (url.includes('/consultant/')) {
      return true;
    }
    
    // 检查特定的顾问界面元素
    const takeoverButton = page.getByRole('button', { name: '接管聊天' });
    if (await takeoverButton.isVisible({ timeout: 1000 })) {
      return true;
    }
    
    return false;
  } catch (error) {
    console.error('检查顾问模式失败:', error);
    return false;
  }
}
