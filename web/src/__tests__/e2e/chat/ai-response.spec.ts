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

test.describe('聊天功能 - AI应答', () => {
  // 在所有测试前创建测试会话
  test.beforeAll(async () => {
    // 创建测试会话
    testConversationId = await createTestConversation();
    console.log(`测试会话ID创建成功: ${testConversationId}`);
  });

  test('顾客发送文本消息，AI正常应答', async ({ browser }) => {
    // 创建浏览器上下文
    const customerContext = await browser.newContext();
    const consultantContext = await browser.newContext();
    
    // 创建页面
    const customerPage = await customerContext.newPage();
    const consultantPage = await consultantContext.newPage();
    
    try {
      // 1. 顾客登录
      await loginAsCustomer(customerPage, 'customer1@example.com');
      
      // 2. 顾客导航到测试会话页面
      await customerPage.goto(`/customer/chat?conversationId=${testConversationId}`);
      await waitForChatReady(customerPage);
      
      // 3. 获取初始消息数量，用于后续验证
      const initialMessages = await getConversationMessages(testConversationId);
      const initialMessageCount = initialMessages.length;
      
      // 4. 顾客发送测试消息
      const testMessage = '双眼皮手术恢复时间?';
      
      // 使用 Shadcn/UI 定位输入框和按钮
      await customerPage.getByPlaceholder('输入消息...').fill(testMessage);
      await customerPage.getByRole('button', { name: '发送' }).click();
      
      // 5. 验证顾客消息显示
      // 使用 data-testid 的选择器更可靠，如果您已实现
      await expect(
        customerPage.locator('.flex.justify-end').filter({ hasText: testMessage })
      ).toBeVisible({ timeout: 5000 });
      
      // 6. 验证是否显示发送中状态
      await expect(
        customerPage.getByText('发送中')
      ).toBeVisible({ timeout: 3000 });
      
      // 7. 等待AI回复（最多等待15秒）
      // AI回复通常在左侧显示，带有AI头像
      const aiResponseLocator = customerPage.locator('.flex.justify-start').filter({ hasText: /恢复|手术|双眼皮|一般/ });
      await expect(
        aiResponseLocator,
        'AI应该在15秒内回复'
      ).toBeVisible({ timeout: 15000 });
      
      // 8. 获取AI回复文本
      const aiResponseElement = customerPage.locator('.flex.justify-start p').first();
      const aiResponseText = await aiResponseElement.textContent();
      
      // 9. 验证AI回复内容相关
      expect(aiResponseText, 'AI回复不应为空').toBeTruthy();
      const relevantTerms = ['恢复', '手术', '双眼皮', '时间', '周'];
      const isRelevant = relevantTerms.some(term => 
        aiResponseText?.toLowerCase().includes(term)
      );
      expect(isRelevant, 'AI回复应与问题相关').toBeTruthy();
      
      // 10. 顾问登录并进入同一会话
      await loginAsConsultant(consultantPage, 'zhang@example.com');
      await consultantPage.goto(`/consultant/chat?conversationId=${testConversationId}`);
      await waitForChatReady(consultantPage);
      
      // 11. 验证顾问能看到顾客消息
      await expect(
        consultantPage.getByText(testMessage)
      ).toBeVisible({ timeout: 5000 });
      
      // 12. 验证顾问能看到AI回复
      // 由于AI回复可能很长，只匹配前20个字符
      const aiPreviewText = aiResponseText?.substring(0, 20).trim() || '';
      if (aiPreviewText) {
        await expect(
          consultantPage.getByText(aiPreviewText, { exact: false })
        ).toBeVisible({ timeout: 5000 });
      }
      
      // 13. 刷新顾客页面，验证历史记录持久化
      await customerPage.reload();
      await waitForChatReady(customerPage);
      
      // 14. 验证刷新后消息仍然存在
      await expect(
        customerPage.getByText(testMessage)
      ).toBeVisible({ timeout: 5000 });
      
      // 15. 验证刷新后AI回复仍然存在
      if (aiPreviewText) {
        await expect(
          customerPage.getByText(aiPreviewText, { exact: false })
        ).toBeVisible({ timeout: 5000 });
      }
      
      // 16. 通过API验证消息记录
      const updatedMessages = await getConversationMessages(testConversationId);
      expect(updatedMessages.length, '应该有新消息添加到会话中').toBeGreaterThan(initialMessageCount);
      
      // 17. 验证最新消息内容
      const customerMessageFound = updatedMessages.some(msg => 
        msg.content.includes(testMessage) && 
        msg.sender.type === 'customer'
      );
      expect(customerMessageFound, '顾客消息应该存在于数据库中').toBeTruthy();
      
      // 至少有一条AI回复
      const aiMessageFound = updatedMessages.some(msg => 
        msg.sender.type === 'ai' && 
        msg.content && typeof msg.content === 'string' &&
        relevantTerms.some(term => msg.content.toLowerCase().includes(term))
      );
      expect(aiMessageFound, 'AI回复应该存在于数据库中').toBeTruthy();
      
    } finally {
      // 清理资源
      await customerPage.close();
      await consultantPage.close();
      await customerContext.close();
      await consultantContext.close();
    }
  });
}); 