export interface E2ETestConfig {
  api: {
    baseUrl: string;
    auth: {
      login: string;
    };
    chat: {
      createConversation: string;
      getMessages: (conversationId: string) => string;
    };
  };
  users: {
    customer: {
      id: string;
      email: string;
      password: string;
    };
    consultant: {
      email: string;
      password: string;
    };
  };
  timeouts: {
    pageLoad: number;
    elementAppear: number;
    aiResponse: number;
    ajaxRequest: number;
  };
  testData: {
    testQuery: string;
    expectedKeywords: string[];
  };
}

declare const config: E2ETestConfig;
export default config;
