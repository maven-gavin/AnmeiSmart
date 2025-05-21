/**
 * 测试配置文件
 */

module.exports = {
  // API服务配置
  api: {
    baseUrl: 'http://127.0.0.1:8000',
    apiPrefix: '/api/v1',
    // 认证相关端点
    auth: {
      login: '/api/v1/auth/login',
      register: '/api/v1/auth/register',
      refresh: '/api/v1/auth/refresh',
    },
    // 聊天相关端点
    chat: {
      createConversation: '/api/v1/chat/conversations',
      getConversations: '/api/v1/chat/conversations',
      getConversation: (id) => `/api/v1/chat/conversations/${id}`,
      getMessages: (id) => `/api/v1/chat/conversations/${id}/messages`,
      sendMessage: (id) => `/api/v1/chat/conversations/${id}/messages`,
      websocket: (userId) => `/api/v1/chat/ws/${userId}`,
    }
  },
  
  // 前端服务配置
  frontend: {
    baseUrl: 'http://127.0.0.1:3000',
    routes: {
      login: '/login',
      customerChat: (conversationId) => `/customer/chat?conversationId=${conversationId}`,
      consultantChat: (conversationId) => `/consultant/chat?conversationId=${conversationId}`,
      customerProfile: '/customer/profile',
      consultantDashboard: '/consultant/dashboard',
    }
  },
  
  // 测试用户
  users: {
    customer: {
      email: 'customer1@example.com',
      password: '123456@Test',
      name: '测试顾客',
      id: '1',
      role: 'customer'
    },
    consultant: {
      email: 'zhang@example.com',
      password: '123456@Test',
      name: '张顾问',
      id: '3',
      role: 'consultant'
    },
    doctor: {
      email: 'doctor1@example.com',
      password: '123456@Test',
      name: '测试医生',
      id: '2',
      role: 'doctor'
    }
  },
  
  // 测试数据
  testData: {
    defaultConversationId: '1',
    testQuery: '双眼皮手术恢复时间?',
    testReply: '双眼皮手术恢复期通常为1-2周。手术后3-7天拆线，2周内可能有轻微肿胀，1个月后基本恢复自然状态，3-6个月达到最终效果。',
    expectedKeywords: ['恢复', '双眼皮', '手术', '时间', '周'],
    testImages: [
      '/test-assets/test-image-1.jpg',
      '/test-assets/test-image-2.jpg'
    ]
  },
  
  // 超时配置
  timeouts: {
    pageLoad: 5000,          // 页面加载超时
    ajaxRequest: 10000,       // AJAX请求超时
    aiResponse: 15000,        // AI响应超时
    consultantResponse: 10000, // 顾问响应超时
    animation: 2000,          // 动画过渡时间
    elementAppear: 5000,      // 元素出现超时
    websocket: {
      connect: 5000,          // WebSocket连接超时
      message: 8000,          // WebSocket消息接收超时
      reconnect: 3000,        // WebSocket重连间隔
    }
  },
  
  // 测试环境
  environment: {
    retryCount: 2,            // 测试重试次数
    screenshotOnFailure: true, // 测试失败截图
    debugMode: false,         // 调试模式
    logLevel: 'info',         // 日志级别: debug, info, warn, error
  }
}; 