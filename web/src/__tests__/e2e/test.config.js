/** @type {import('./test.config').E2ETestConfig} */
const config = {
  api: {
    baseUrl: process.env.E2E_API_BASE_URL || 'http://127.0.0.1:8000/api/v1',
    auth: {
      login: '/auth/login',
    },
    chat: {
      createConversation: '/chat/conversations',
      getMessages: (conversationId) => `/chat/conversations/${conversationId}/messages`,
    },
  },
  users: {
    customer: {
      id: process.env.E2E_CUSTOMER_ID || 'customer-test-id',
      email: process.env.E2E_CUSTOMER_EMAIL || 'customer@test.com',
      password: process.env.E2E_CUSTOMER_PASSWORD || 'password123',
    },
    consultant: {
      email: process.env.E2E_CONSULTANT_EMAIL || 'consultant@test.com',
      password: process.env.E2E_CONSULTANT_PASSWORD || 'password123',
    },
  },
  timeouts: {
    pageLoad: 30000,
    elementAppear: 10000,
    aiResponse: 60000,
    ajaxRequest: 15000,
  },
  testData: {
    testQuery: '我想咨询一下服务项目',
    expectedKeywords: ['服务', '咨询'],
  },
};

module.exports = config;
