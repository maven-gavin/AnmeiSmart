import { test, expect } from '@playwright/test';
import { 
  loginAsCustomer, 
  loginAsConsultant, 
  createTestConversation,
  getConversationMessages,
  waitForChatReady
} from './test-utils';

// 定义测试会话ID
let testConversationId: string;

test.describe('聊天功能 - 顾问应答', () => {
  // 在所有测试前创建测试会话
  test.beforeAll(async () => {
    // 创建测试会话
    testConversationId = await createTestConversation();
    console.log(`测试会话ID创建成功: ${testConversationId}`);
  });

  test('顾客发送文本消息，顾问正常应答', async ({ browser }) => {
    // 创建浏览器上下文
    const customerContext = await browser.newContext();
    const consultantContext = await browser.newContext();
    
    // 创建页面
    const customerPage = await customerContext.newPage();
    const consultantPage = await consultantContext.newPage();
    
    try {
      // 1. 顾客登录
      await loginAsCustomer(customerPage, 'customer1@example.com');
      
      // 2. 顾问登录
      await loginAsConsultant(consultantPage, 'zhang@example.com');
      
      // 3. 顾客导航到测试会话页面
      await customerPage.goto(`/customer/chat?conversationId=${testConversationId}`);
      await waitForChatReady(customerPage);
      
      // 4. 顾问导航到测试会话页面
      await consultantPage.goto(`/consultant/chat?conversationId=${testConversationId}`);
      await waitForChatReady(consultantPage);
      
      // 5. 获取初始消息数量，用于后续验证
      const initialMessages = await getConversationMessages(testConversationId);
      const initialMessageCount = initialMessages.length;
      
      // 6. 顾客发送测试消息
      const testMessage = '双眼皮手术大概多少钱?';
      
      // 使用 Shadcn/UI 定位输入框和按钮
      await customerPage.getByPlaceholder('输入消息...').fill(testMessage);
      await customerPage.getByRole('button', { name: '发送' }).click();
      
      // 7. 验证顾客消息显示在顾客界面
      await expect(
        customerPage.locator('.flex.justify-end').filter({ hasText: testMessage })
      ).toBeVisible({ timeout: 5000 });
      
      // 8. 顾问应该能看到顾客消息
      await expect(
        consultantPage.locator('.flex.justify-start').filter({ hasText: testMessage })
      ).toBeVisible({ timeout: 5000 });
      
      // 9. 顾问接管聊天
      // 假设有一个按钮或切换模式的开关
      await consultantPage.getByRole('button', { name: '接管聊天' }).click();
      
      // 等待聊天模式切换指示器
      await expect(
        consultantPage.getByText('已接管聊天', { exact: false })
      ).toBeVisible({ timeout: 3000 });
      
      // 10. 顾问输入并发送回复
      const consultantResponse = '一般来说双眼皮手术价格在3000-8000元之间，具体价格取决于手术方式、医院级别和医生经验等因素。您可以预约面诊获取更精准的方案和报价。';
      await consultantPage.getByPlaceholder('输入消息...').fill(consultantResponse);
      await consultantPage.getByRole('button', { name: '发送' }).click();
      
      // 11. 验证顾问回复在顾问界面显示
      await expect(
        consultantPage.locator('.flex.justify-end').filter({ hasText: consultantResponse.substring(0, 20) })
      ).toBeVisible({ timeout: 5000 });
      
      // 12. 验证顾问回复在顾客界面显示
      await expect(
        customerPage.locator('.flex.justify-start').filter({ hasText: consultantResponse.substring(0, 20) })
      ).toBeVisible({ timeout: 5000 });
      
      // 13. 刷新顾客页面，验证历史记录持久化
      await customerPage.reload();
      await waitForChatReady(customerPage);
      
      // 14. 验证刷新后顾客消息仍然存在
      await expect(
        customerPage.getByText(testMessage)
      ).toBeVisible({ timeout: 5000 });
      
      // 15. 验证刷新后顾问回复仍然存在
      await expect(
        customerPage.getByText(consultantResponse.substring(0, 20), { exact: false })
      ).toBeVisible({ timeout: 5000 });
      
      // 16. 刷新顾问页面，验证历史记录持久化
      await consultantPage.reload();
      await waitForChatReady(consultantPage);
      
      // 17. 验证刷新后顾客消息在顾问界面仍然存在
      await expect(
        consultantPage.getByText(testMessage)
      ).toBeVisible({ timeout: 5000 });
      
      // 18. 验证刷新后顾问回复在顾问界面仍然存在
      await expect(
        consultantPage.getByText(consultantResponse.substring(0, 20), { exact: false })
      ).toBeVisible({ timeout: 5000 });
      
      // 19. 通过API验证消息记录
      const updatedMessages = await getConversationMessages(testConversationId);
      expect(updatedMessages.length, '应该有新消息添加到会话中').toBeGreaterThan(initialMessageCount);
      
      // 20. 验证最新消息内容
      // 顾客消息存在于数据库
      const customerMessageFound = updatedMessages.some(msg => 
        msg.content.includes(testMessage) && 
        msg.sender.type === 'customer'
      );
      expect(customerMessageFound, '顾客消息应该存在于数据库中').toBeTruthy();
      
      // 顾问回复存在于数据库
      const consultantMessageFound = updatedMessages.some(msg => 
        msg.content.includes(consultantResponse.substring(0, 20)) && 
        msg.sender.type === 'consultant'
      );
      expect(consultantMessageFound, '顾问回复应该存在于数据库中').toBeTruthy();
      
    } finally {
      // 清理资源
      await customerPage.close();
      await consultantPage.close();
      await customerContext.close();
      await consultantContext.close();
    }
  });
}); 