import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './src/__tests__/e2e',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 1,
  workers: process.env.CI ? 1 : 1,
  reporter: [
    ['html', { open: 'never' }],
    ['list']
  ],
  use: {
    baseURL: 'http://127.0.0.1:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    viewport: { width: 1280, height: 720 },
    navigationTimeout: 30000,
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  timeout: 60000,
  
  // 测试需要先手动启动后端和前端服务
  // 后端: cd api && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
  // 前端: cd web && npm run dev
  webServer: {
    command: 'echo "请确保后端和前端服务已启动"',
    url: 'http://127.0.0.1:3000',
    reuseExistingServer: true,
    timeout: 5000,
  },
}); 