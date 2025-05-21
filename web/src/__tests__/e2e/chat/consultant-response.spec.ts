import { test, expect } from '@playwright/test';
import { 
  loginAsCustomer, 
  loginAsConsultant, 
  createCustomerTestConversation,
  getConversationMessages,
  waitForChatReady,
  loginCustomerAPIAndGetToken,
  loginConsultantAPIAndGetToken
} from './test-utils';

// 导入测试配置
const config = require('../test.config');

// 定义测试会话ID
let testConversationId: string;

test.describe('聊天功能 - 顾问应答', () => {
  // 在所有测试前准备环境
  test.beforeAll(async () => {
    console.log('准备测试环境 - 顾客和顾问交互测试');
    
    try {
      // 1. 先获取顾客认证令牌（顾客发起咨询）
      await loginCustomerAPIAndGetToken();
      
      // 2. 获取顾问认证令牌（顾问接入咨询）
      await loginConsultantAPIAndGetToken();
      
      // 3. 由顾客创建测试会话（符合业务逻辑：顾客发起咨询）
      testConversationId = await createCustomerTestConversation();
      console.log(`测试会话创建成功，ID: ${testConversationId}`);
    } catch (error) {
      console.error('测试准备阶段发生错误:', error);
      throw error; // 如果初始化失败，直接终止测试
    }
  });

  test('顾客发送文本消息，顾问正常应答', async ({ browser }) => {
    // 创建浏览器上下文 - 顾客和顾问分别有独立的浏览器会话
    const customerContext = await browser.newContext();
    const consultantContext = await browser.newContext();
    
    // 创建页面
    const customerPage = await customerContext.newPage();
    const consultantPage = await consultantContext.newPage();
    
    try {
      console.log('开始测试: 顾客发送文本消息，顾问正常应答');
      
      // 1. 顾客登录（在真实场景中，顾客通过UI登录系统）
      console.log('步骤1: 顾客登录');
      await loginAsCustomer(customerPage, config.users.customer.email);
      
      // 2. 顾问登录（在真实场景中，顾问通过UI登录系统，查看待处理的咨询）
      console.log('步骤2: 顾问登录');
      await loginAsConsultant(consultantPage, config.users.consultant.email);
      
      // 3. 顾客导航到测试会话页面（顾客访问自己的咨询会话）
      console.log('步骤3: 顾客进入咨询会话');
      await customerPage.goto(`/customer/chat?conversationId=${testConversationId}`);
      await waitForChatReady(customerPage);
      
      // 4. 顾问导航到测试会话页面（顾问查看顾客的咨询）
      console.log('步骤4: 顾问进入同一咨询会话');
      await consultantPage.goto(`/consultant/chat?conversationId=${testConversationId}`);
      await waitForChatReady(consultantPage);
      
      // 5. 记录初始消息数量
      console.log('步骤5: 获取初始消息数量');
      const initialMessages = await getConversationMessages(testConversationId);
      const initialMessageCount = initialMessages.length;
      console.log(`初始消息数量: ${initialMessageCount}`);
      
      // 6. 顾客发送测试消息（顾客提出咨询问题）
      console.log('步骤6: 顾客发送咨询消息');
      const testMessage = '双眼皮手术大概多少钱?';
      
      const customerInput = customerPage.getByPlaceholder('输入消息...');
      await customerInput.waitFor({ state: 'visible', timeout: config.timeouts.elementAppear });
      await customerInput.fill(testMessage);
      await customerPage.getByRole('button', { name: '发送' }).click();
      
      // 7. 验证顾客消息显示在顾客界面（顾客在自己的界面看到已发送的消息）
      console.log('步骤7: 验证顾客消息显示在顾客界面');
      const customerMessage = customerPage.locator('.flex.justify-end').filter({ hasText: testMessage }).first();
      await expect(customerMessage).toBeVisible({ timeout: config.timeouts.elementAppear });
      
      // 8. 验证顾问能看到顾客消息（顾问在自己的界面看到顾客发送的消息）
      console.log('步骤8: 验证顾问能看到顾客消息');
      const consultantSeeCustomerMessage = consultantPage.locator('.flex.justify-start').filter({ hasText: testMessage }).first();
      await expect(consultantSeeCustomerMessage).toBeVisible({ timeout: config.timeouts.elementAppear });
      
      // 9. 顾问接管聊天（顾问主动接管咨询，而不是由AI自动回复）
      console.log('步骤9: 顾问接管聊天');
      const takeoverButton = consultantPage.getByRole('button', { name: '接管聊天' });
      
      if (await takeoverButton.isVisible({ timeout: 3000 })) {
        await takeoverButton.click();
        
        // 等待聊天模式切换指示器
        await expect(
          consultantPage.getByText('已接管聊天', { exact: false })
        ).toBeVisible({ timeout: 3000 });
        
        console.log('顾问成功接管聊天');
      } else {
        console.log('未找到接管按钮，可能顾问已经处于接管状态');
      }
      
      // 10. 顾问输入并发送回复（顾问回答顾客的问题）
      console.log('步骤10: 顾问发送回复');
      const consultantResponse = '一般来说双眼皮手术价格在3000-8000元之间，具体价格取决于手术方式、医院级别和医生经验等因素。您可以预约面诊获取更精准的方案和报价。';
      
      const consultantInput = consultantPage.getByPlaceholder('输入消息...');
      await consultantInput.waitFor({ state: 'visible', timeout: config.timeouts.elementAppear });
      await consultantInput.fill(consultantResponse);
      await consultantPage.getByRole('button', { name: '发送' }).click();
      
      // 11. 验证顾问回复在顾问界面显示（顾问看到自己发送的消息）
      console.log('步骤11: 验证顾问回复在顾问界面显示');
      const consultantMessage = consultantPage.locator('.flex.justify-end').filter({ hasText: consultantResponse.substring(0, 20) }).first();
      await expect(consultantMessage).toBeVisible({ timeout: config.timeouts.elementAppear });
      
      // 12. 验证顾问回复在顾客界面显示（顾客收到顾问的回复）
      console.log('步骤12: 验证顾问回复在顾客界面显示');
      const customerSeeConsultantMessage = customerPage.locator('.flex.justify-start').filter({ hasText: consultantResponse.substring(0, 20) }).first();
      await expect(customerSeeConsultantMessage).toBeVisible({ timeout: config.timeouts.elementAppear });
      
      // 13. 刷新顾客页面，验证历史记录持久化（消息记录应该保存在服务器）
      console.log('步骤13: 刷新顾客页面，验证历史记录持久化');
      await customerPage.reload();
      await waitForChatReady(customerPage);
      
      // 14. 验证刷新后顾客消息仍然存在
      console.log('步骤14: 验证刷新后顾客消息仍然存在');
      await expect(
        customerPage.getByText(testMessage, { exact: false })
      ).toBeVisible({ timeout: config.timeouts.elementAppear });
      
      // 15. 验证刷新后顾问回复仍然存在
      console.log('步骤15: 验证刷新后顾问回复仍然存在');
      await expect(
        customerPage.getByText(consultantResponse.substring(0, 20), { exact: false })
      ).toBeVisible({ timeout: config.timeouts.elementAppear });
      
      // 16. 通过API验证消息记录
      console.log('步骤16: 通过API验证消息记录');
      const updatedMessages = await getConversationMessages(testConversationId);
      console.log(`更新后的消息数量: ${updatedMessages.length}, 初始消息数量: ${initialMessageCount}`);
      expect(updatedMessages.length, '应该有新消息添加到会话中').toBeGreaterThan(initialMessageCount);
      
      // 17. 验证顾客消息存在于数据库
      const customerMessageFound = updatedMessages.some(msg => 
        msg.content.includes(testMessage) && 
        msg.sender.type === 'customer'
      );
      expect(customerMessageFound, '顾客消息应该存在于数据库中').toBeTruthy();
      
      // 18. 验证顾问回复存在于数据库
      const consultantMessageFound = updatedMessages.some(msg => 
        msg.content.includes(consultantResponse.substring(0, 20)) && 
        msg.sender.type === 'consultant'
      );
      expect(consultantMessageFound, '顾问回复应该存在于数据库中').toBeTruthy();
      
      console.log('测试完成: 顾客发送文本消息，顾问正常应答 ✅');
    } catch (error) {
      console.error('测试执行失败:', error);
      throw error;
    } finally {
      // 清理资源
      await customerPage.close();
      await consultantPage.close();
      await customerContext.close();
      await consultantContext.close();
    }
  });
}); 