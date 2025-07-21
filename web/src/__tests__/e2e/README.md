# 安美智享自动化测试说明

本目录包含安美智享项目的端到端(E2E)自动化测试。这些测试使用Playwright框架实现，主要覆盖聊天功能的核心用例。

## 测试结构

```
e2e/                           # 端到端测试目录
├── chat/                      # 聊天功能测试
│   ├── ai-customer-conversation.spec.ts   # 客户与AI对话测试
│   ├── basic-nav.spec.ts                  # 基本页面导航测试
│   ├── consultant-response.spec.ts        # 顾问应答测试
│   └── test-utils.ts                      # 测试工具函数
├── setup-tests.ps1            # Windows测试环境设置脚本
├── setup-tests.sh             # Linux/Mac测试环境设置脚本
├── test.config.js             # 测试配置文件
└── README.md                  # 本说明文件
```

## 测试设计思路

### 角色分离与交互模式

测试采用了严格的角色分离设计，模拟真实业务场景中的客户-顾问交互模式：

1. **客户视角**：
   - 客户登录系统，创建咨询会话
   - 客户发送咨询消息，等待回复
   - 客户接收顾问/AI回复，可继续提问

2. **顾问视角**：
   - 顾问登录系统，查看待处理咨询
   - 顾问可接管AI自动回复的会话
   - 顾问回复客户咨询问题

### 多浏览器上下文

每个测试使用独立的浏览器上下文，分别模拟客户和顾问：

```typescript
// 创建浏览器上下文 - 客户和顾问分别有独立的浏览器会话
const customerContext = await browser.newContext();
const consultantContext = await browser.newContext();

// 创建页面
const customerPage = await customerContext.newPage();
const consultantPage = await consultantContext.newPage();
```

这种设计允许测试真实模拟两个用户同时在线交互的场景。

### 认证令牌分离

测试使用分离的认证令牌管理，确保客户和顾问有各自独立的身份：

```typescript
// 客户令牌
let customerToken: string | null = null;

// 顾问令牌
let consultantToken: string | null = null;

// 分别登录获取令牌
await loginCustomerAPIAndGetToken();
await loginConsultantAPIAndGetToken();
```

## 会话创建流程

### 符合业务逻辑的会话创建

测试按照实际业务流程设计会话创建逻辑：

1. **优先使用客户身份创建会话**：
   ```typescript
   // 由客户创建测试会话（符合业务逻辑：客户发起咨询）
   testConversationId = await createCustomerTestConversation();
   ```

2. **后备方案 - 顾问身份创建会话**：
   ```typescript
   // 如果客户创建失败，尝试使用顾问创建
   return createConsultantTestConversation();
   ```

## 运行测试方法

### 自动化测试环境设置

提供了自动化脚本帮助设置测试环境：

```powershell
# 在Windows系统中
cd web
npm run test:e2e:setup

# 在Linux/Mac系统中
cd web
bash src/__tests__/e2e/setup-tests.sh
```

### 运行测试命令

```powershell
# 运行所有测试
npm run test:e2e

# 只运行顾问应答测试
npm run test:e2e -- src/__tests__/e2e/chat/consultant-response.spec.ts

# 在UI调试模式中运行
npm run test:e2e:ui
```

## 常见测试问题与解决方案

### 1. API端点404错误

**问题**: 测试时出现404错误，无法创建会话或获取消息。

**原因**: API路由配置中聊天相关端点使用了`/api/v1/chat`前缀，而测试代码中使用了错误的路径。

**修复方法**:
- 确保使用正确的API端点: `/api/v1/chat/conversations`
- 使用`test.config.js`中定义的端点配置，确保一致性

### 2. 认证令牌过期

**问题**: 测试过程中API请求返回401未授权错误。

**原因**: 认证令牌过期或无效。

**修复方法**:
- 测试前自动重新获取令牌
- 捕获401错误并自动重新登录

### 3. 浏览器渲染问题

**问题**: 测试中无法找到UI元素。

**原因**: 页面加载未完成或元素未渲染。

**修复方法**:
- 使用`waitForChatReady`函数等待页面加载完成
- 增加等待超时时间
- 对关键元素使用显式等待

### 4. WebSocket连接问题

**问题**: 测试中消息无法实时更新。

**原因**: WebSocket连接失败或断开。

**修复方法**:
- 增加WebSocket连接状态检测
- 实现自动重连机制
- 测试开始前验证WebSocket服务可用性 