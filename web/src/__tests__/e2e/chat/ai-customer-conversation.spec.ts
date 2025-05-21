import { test, expect, BrowserContext, Page } from '@playwright/test';
import { 
  loginCustomerAPIAndGetToken,
  loginConsultantAPIAndGetToken,
  createCustomerTestConversation,
  loginAsCustomer,
  loginAsConsultant,
  waitForChatReady,
  getCustomerToken,
  getConsultantToken,
  getConversationMessages
} from './test-utils';

// 导入测试配置
const config = require('../test.config');

// 定义测试会话ID
let testConversationId: string;
let customerToken: string | null = null;
let consultantToken: string | null = null;

// 测试查询和预期关键词
const TEST_QUERY = config.testData.testQuery;
const EXPECTED_KEYWORDS = config.testData.expectedKeywords;

/**
 * 测试前准备：顾客创建会话
 */
test.beforeAll(async () => {
  console.log('准备测试环境 - 顾客AI对话测试');
  
  try {
    // 1. 顾客登录获取令牌
    await loginCustomerAPIAndGetToken();
    customerToken = getCustomerToken();
    
    // 2. 顾问登录获取令牌（用于监控会话）
    await loginConsultantAPIAndGetToken();
    consultantToken = getConsultantToken();
    
    // 3. 顾客创建测试会话（符合业务流程：顾客发起咨询）
    testConversationId = await createCustomerTestConversation();
    console.log(`测试会话创建成功，ID: ${testConversationId}`);
  } catch (error) {
    console.error('测试准备阶段发生错误:', error);
    throw error; // 如果初始化失败，直接终止测试
  }
});

test.describe('聊天功能 - 顾客AI对话', () => {
  // 定义浏览器上下文和页面
  let customerContext: BrowserContext;
  let consultantContext: BrowserContext;
  let customerPage: Page;
  let consultantPage: Page;
  
  test.beforeEach(async ({ browser }) => {
    // 创建浏览器上下文 - 顾客和顾问分别有独立的浏览器会话
    customerContext = await browser.newContext();
    consultantContext = await browser.newContext();
    
    // 创建页面
    customerPage = await customerContext.newPage();
    consultantPage = await consultantContext.newPage();
    
    console.log('准备测试环境...');
    
    try {
      // 1. 顾客登录 - 通过UI正常登录
      console.log('步骤1: 顾客登录');
      await loginAsCustomer(customerPage, config.users.customer.email);
      await customerPage.goto(`/customer/chat?conversationId=${testConversationId}`);
      
      // 等待聊天界面加载
      await waitForChatReady(customerPage);
      console.log('顾客已登录并进入聊天页面');
      
      // 2. 顾问登录 - 用于监控会话
      console.log('步骤2: 顾问登录');
      await loginAsConsultant(consultantPage, config.users.consultant.email);
      await consultantPage.goto(`/consultant/chat?conversationId=${testConversationId}`);
      
      // 等待聊天界面加载
      await waitForChatReady(consultantPage);
      console.log('顾问已登录并进入同一会话页面');
      
      // 等待WebSocket连接建立
      await Promise.all([
        customerPage.waitForTimeout(2000),
        consultantPage.waitForTimeout(2000)
      ]);
      
      console.log('测试环境准备完成');
    } catch (error) {
      console.error('测试环境准备失败:', error);
      throw error; // 如果环境准备失败，应中止测试
    }
  });
  
  /**
   * 测试：顾客发送文本消息，AI正常应答
   */
  test('顾客发送文本消息，AI正常应答', async () => {
    console.log('开始测试: 顾客发送文本消息，AI正常应答');
    
    try {
      // 1. 获取初始消息数量
      console.log('步骤1: 获取初始消息数量');
      const initialMessages = await getConversationMessages(testConversationId, false);
      const initialMessageCount = initialMessages.length;
      console.log(`初始消息数量: ${initialMessageCount}`);
      
      // 2. 顾客发送测试消息
      console.log(`步骤2: 顾客发送测试消息: "${TEST_QUERY}"`);
      
      // 定位输入框
      const messageInput = customerPage.getByPlaceholder('输入消息...');
      await messageInput.waitFor({ state: 'visible', timeout: config.timeouts.elementAppear });
      
      // 填写并发送消息
      await messageInput.fill(TEST_QUERY);
      await customerPage.getByRole('button', { name: '发送' }).click();
      console.log('顾客消息已发送');
      
      // 3. 验证顾客消息显示
      console.log('步骤3: 验证顾客消息显示在界面上');
      const customerMessageLocator = customerPage.locator('.flex.justify-end').filter({ hasText: TEST_QUERY }).first();
      await expect(customerMessageLocator).toBeVisible({ timeout: config.timeouts.elementAppear });
      console.log('顾客消息已显示在顾客界面');
      
      // 4. 顾问应该能看到顾客消息
      console.log('步骤4: 验证顾问能看到顾客消息');
      const consultantSeeCustomerMsg = consultantPage.locator('.flex.justify-start').filter({ hasText: TEST_QUERY }).first();
      await expect(consultantSeeCustomerMsg).toBeVisible({ timeout: config.timeouts.elementAppear });
      console.log('顾问能看到顾客消息');
      
      // 5. 等待AI响应
      console.log(`步骤5: 等待AI响应... (最长等待时间: ${config.timeouts.aiResponse} ms)`);
      
      // 找到以AI头像开头的消息容器
      const aiResponseLocator = customerPage
        .locator('.flex.justify-start')
        .filter({ hasText: new RegExp(EXPECTED_KEYWORDS.join('|')) })
        .first();
      
      // 等待AI回复出现
      await aiResponseLocator.waitFor({ state: 'visible', timeout: config.timeouts.aiResponse });
      
      // 获取AI回复文本
      const aiResponseText = await aiResponseLocator.textContent() || '';
      console.log(`AI回复内容: "${aiResponseText.substring(0, 100)}..."`);
      
      // 验证AI回复是否包含预期关键词
      const hasRelevantContent = EXPECTED_KEYWORDS.some((keyword: string) => 
        aiResponseText.toLowerCase().includes(keyword.toLowerCase())
      );
      
      expect(hasRelevantContent, 'AI回复应包含预期关键词').toBeTruthy();
      console.log('AI回复已验证包含预期关键词');
      
      // 6. 验证顾问端也能看到AI回复
      console.log('步骤6: 验证顾问端也能看到AI回复');
      // 使用AI回复的前30个字符作为匹配依据
      const aiPreviewText = aiResponseText.substring(0, 30);
      const consultantSeeAiMsg = consultantPage.locator(`.flex:has-text("${aiPreviewText}")`).first();
      await consultantSeeAiMsg.waitFor({ state: 'visible', timeout: config.timeouts.elementAppear });
      console.log('顾问能看到AI回复');
      
      // 7. 通过API验证消息已添加到数据库
      console.log('步骤7: 验证消息已添加到数据库');
      const updatedMessages = await getConversationMessages(testConversationId, false);
      console.log(`更新后的消息数量: ${updatedMessages.length}, 初始消息数量: ${initialMessageCount}`);
      
      // 验证消息数量增加
      expect(updatedMessages.length, '消息数量应该增加').toBeGreaterThan(initialMessageCount);
      
      // 验证顾客消息存在于数据库
      const customerMessageInDB = updatedMessages.some(msg => 
        msg.content.includes(TEST_QUERY) && 
        msg.sender.type === 'customer'
      );
      expect(customerMessageInDB, '顾客消息应该存在于数据库').toBeTruthy();
      
      // 验证AI回复也存在于数据库
      const aiMessageInDB = updatedMessages.some(msg => 
        msg.content.includes(aiResponseText.substring(0, 20)) &&
        (msg.sender.type === 'ai' || msg.sender.type === 'system')
      );
      expect(aiMessageInDB, 'AI回复应该存在于数据库').toBeTruthy();
      console.log('AI回复已验证存在于数据库');
      
      console.log('测试成功完成 ✅');
    } catch (error) {
      console.error('测试执行失败:', error);
      throw error;
    }
  });
  
  /**
   * 测试清理：关闭浏览器上下文
   */
  test.afterEach(async () => {
    try {
      await customerContext.close();
      await consultantContext.close();
      console.log('已关闭浏览器上下文');
    } catch (e) {
      console.error('关闭浏览器上下文失败:', e);
    }
  });
}); 