# 端到端测试指南

本目录包含使用Playwright实现的端到端测试，用于验证应用功能在真实环境中的表现。

## 前提条件

1. 项目依赖已安装：`npm install`
2. 后端API服务在本地运行并可访问
3. 前端应用在开发模式下运行：`npm run dev`

## 安装Playwright浏览器

在首次运行测试前，需要安装Playwright浏览器：

```bash
npx playwright install
```

## 运行测试

### 运行所有测试

```bash
npm run test:e2e
```

### 运行特定测试

```bash
npx playwright test chat/ai-response.spec.ts
```

### 调试模式

```bash
npm run test:e2e:debug
```

### 使用UI界面

```bash
npm run test:e2e:ui
```

## 测试用例说明

### 聊天功能测试

1. **顾客发送文本消息，AI应答**
   - 位置：`e2e/chat/ai-response.spec.ts`
   - 测试内容：顾客发送消息后，AI正常回复，验证消息持久化

2. **顾客发送文本消息，顾问应答**
   - 位置：`e2e/chat/consultant-response.spec.ts`
   - 测试内容：顾客发送消息后，顾问接管并回复，验证消息持久化

## 注意事项

1. 测试依赖于特定用户账号存在：
   - 顾客账号：customer1@example.com
   - 顾问账号：zhang@example.com

2. 测试会创建真实会话，可能会遗留测试数据。如需清理，可以运行以下代码：

```typescript
import { cleanupAllTestSessions } from '../helpers/setupTestConversation';

// 清理所有测试会话
await cleanupAllTestSessions();
```

3. 测试失败截图和视频会保存在 `playwright-report` 目录 