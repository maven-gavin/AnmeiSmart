# AnmeiSmart 医美智能系统

## 项目概述

AnmeiSmart是一个智能医疗美容管理平台，整合了人工智能客服、在线咨询、预约管理、客户关系管理等功能。

## 新增: WebSocket通信架构

本项目最近完成了WebSocket通信架构的重构，采用了更加模块化和可扩展的设计。新的WebSocket架构具有以下特点：

### 分层设计

- **核心层(Core)**: 负责基础连接管理、心跳机制、重连逻辑和序列化
- **适配层(Adapters)**: 负责消息格式转换和错误处理
- **处理层(Handlers)**: 提供各类消息的专用处理器
- **接口层(API)**: 提供统一的客户端接口

### 主要组件

- `WebSocketConnection`: 管理WebSocket连接的创建和通信
- `WebSocketHeartbeat`: 提供自动心跳机制，保持连接活跃
- `WebSocketReconnector`: 处理断线自动重连
- `WebSocketSerializer`: 处理消息的序列化和反序列化
- `MessageQueue`: 处理离线消息和消息重发
- `MessageAdapter`: 适配不同消息格式
- `MessageHandler`: 处理不同类型的消息

### 优势

1. **关注点分离**: 每个组件职责明确，降低了系统复杂度
2. **高扩展性**: 可以轻松添加新的消息处理器和适配器
3. **高性能**: 优化的消息处理流程和离线消息缓存
4. **可靠性**: 完善的重连机制和心跳检测
5. **易于集成**: 提供简洁的API，易于与现有项目集成

### 使用示例

```typescript
// 初始化WebSocket客户端
const wsClient = getWebSocketClient({
  url: 'ws://example.com/chat',
  reconnectAttempts: 5,
  debug: true
});

// 注册自定义消息处理器
wsClient.registerHandler(new CustomChatHandler());

// 连接到服务器
wsClient.connect({
  userId: 'user123',
  conversationId: 'conv456',
  token: 'auth-token'
});

// 发送消息
wsClient.sendMessage({
  action: 'message',
  content: 'Hello world',
  conversation_id: 'conv456'
});
```

## 技术栈

- 前端: Next.js, React, TypeScript, TailwindCSS
- 后端: FastAPI, Python, PostgreSQL, MongoDB
- AI: OpenAI API, Weaviate向量数据库

## 运行项目

### 后端服务

```bash
cd api
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 前端应用

```bash
cd web
npm install
npm run dev
```

## 项目结构

```
AnmeiSmart/
├── api/                 # 后端API服务
│   ├── app/             # 应用主目录
│   │   ├── api/         # API路由
│   │   │   ├── core/        # 核心配置
│   │   │   ├── db/          # 数据库模型和配置
│   │   │   ├── schemas/     # 数据验证模式
│   │   │   └── services/    # 业务服务
│   │   ├── migrations/      # 数据库迁移
│   │   └── tests/           # 测试
│   ├── web/                 # 前端应用
│   │   ├── public/          # 静态资源
│   │   └── src/             # 源代码
│   │       ├── app/         # 页面组件
│   │       ├── components/  # 可复用组件
│   │       ├── contexts/    # React上下文
│   │       ├── service/     # 服务层
│   │       └── types/       # 类型定义
│   └── docs/                # 项目文档
```

## 分支管理规范

- main：主分支，始终保持可用、可部署
- dev：开发分支，集成所有feature分支，定期合并到main
- feature/xxx：功能开发分支，命名如feature/chat、feature/simulation
- hotfix/xxx：紧急修复分支
- release/xxx：预发布分支

## 协作流程

1. 从dev分支拉取最新代码，创建feature/xxx分支开发
2. 功能开发完成后提交PR（Pull Request）到dev分支，需2人以上Code Review
3. 通过测试后合并到dev，定期同步到main
4. 重要变更需在PR中详细说明，必要时同步到docs/

## 代码规范

- 前端：TS类型覆盖≥95%，组件化、严格XSS防护
- 后端：类型注解100%，禁用Any，单元测试覆盖≥80%
- 提交信息规范：feat/bugfix/docs/chore + 描述

## 其他说明

- 建议使用pnpm管理前端依赖，uv管理后端依赖
- 所有文档、设计、决策需同步到docs/

## 环境变量设置

项目使用环境变量管理配置。请参考 `api/env.example` 文件创建自己的 `.env` 文件。

主要配置项包括：

- 数据库连接配置
- JWT认证配置
- AI服务配置

详细说明请查看示例文件中的注释。

## 自动化测试说明

### 测试驱动开发方法

项目采用测试驱动开发(TDD)方法，通过以下步骤进行功能开发：

1. **编写测试用例**：首先编写测试用例，描述功能的预期行为
2. **运行测试，验证失败**：新功能尚未实现，测试应当失败
3. **实现功能代码**：编写最简单的代码使测试通过
4. **运行测试，验证通过**：确认实现的功能符合预期
5. **重构优化**：在测试通过的基础上优化代码质量，保持测试通过

主要测试用例位于 `web/src/__tests__/e2e/`目录，使用Playwright框架实现端到端测试。

### 运行测试方法

#### 自动化测试环境设置

提供了自动化脚本帮助设置测试环境：

```powershell
# 自动检查和修复测试环境
cd web
npm run test:prepare

# 或使用测试环境设置脚本
npm run test:e2e:setup

# 或手动启动
cd api
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# 新开一个终端
cd web
npm run dev
```

#### 运行测试命令

```powershell
# 运行所有测试
npm run test:e2e

# 只运行聊天功能测试
npm run test:e2e:chat

# 只运行基本导航测试
npm run test:e2e:basic
```

### 常见测试问题与解决方案

#### 1. API端点404错误

**问题描述**：在执行测试时，创建会话相关的API调用返回404错误。

```
尝试创建会话 /api/v1/conversations... 404 {"detail":"Not Found"}
```

**原因分析**：测试工具中使用了错误的API路径，API路由配置将聊天功能设置为 `/api/v1/chat`前缀，正确的会话创建端点应为 `/api/v1/chat/conversations`。

**解决方案**：运行 `npm run test:prepare`自动修复，或修改 `web/src/__tests__/e2e/chat/test-utils.ts`中的 `endpoints`数组，确保包含正确的端点：

```typescript
const endpoints = [
  '/api/v1/chat/conversations',  // 正确的端点
  // 其他备选端点
];
```

#### 2. 聊天输入框不可见

**问题描述**：测试执行时，无法找到聊天输入框元素，导致测试跳过。

```
聊天输入框不可见，尝试查找页面内容
页面可能未正确加载聊天界面
无法找到聊天输入框，跳过消息发送测试
```

**原因分析**：可能是由于页面未正确跳转到聊天页面，或者聊天组件未正确加载。

**解决方案**：

1. 检查登录后的重定向是否正确
2. 增加页面加载的等待时间
3. 检查前端路由配置是否正确

#### 3. WebSocket连接问题

**问题描述**：测试过程中WebSocket连接建立失败，导致实时消息无法发送或接收。

**原因分析**：WebSocket服务器URL配置错误，或后端WebSocket服务未正确启动。

**解决方案**：

1. 检查 `chatService.ts`中的WebSocket URL配置
2. 确保后端API服务已启动且包含WebSocket支持
3. 检查WebSocket连接请求中是否包含必要的认证信息

### API端点参考

以下是系统主要API端点的参考：

- `POST /api/v1/auth/login` - 用户登录 (使用表单格式提交)
- `POST /api/v1/chat/conversations` - 创建聊天会话
- `GET /api/v1/chat/conversations` - 获取会话列表
- `GET /api/v1/chat/conversations/{id}` - 获取单个会话详情
- `GET /api/v1/chat/conversations/{id}/messages` - 获取会话消息
- `POST /api/v1/chat/conversations/{id}/messages` - 发送会话消息
- `WebSocket /api/v1/chat/ws/{user_id}` - WebSocket连接端点

## 主要测试场景

#### 发送普通文本消息，AI应答

**前提条件**:

* 顾客customer1@example.com已登录
* 顾问zhang@example.com已登录
* AI接管模式（系统默认模式）
* 顾客已进入会话ID为1的聊天页面
* 顾问已进入会话ID为1的聊天页面进行监控
* 当前会话已有历史消息记录

**业务流程**:

1. 顾客在聊天输入框中输入"双眼皮手术恢复时间?"
2. 顾客点击发送按钮或按下Enter键
3. 顾客端聊天窗口右侧显示该条消息，带有"我"的头像和名称标识
4. 系统将消息发送到后端服务器，消息记录保存到数据库
5. 后端服务器接收到消息后，调用AI服务
6. AI服务生成回复内容
7. 后端将AI回复保存到数据库，作为同一会话的一部分
8. 后端通过WebSocket将AI回复推送到前端
9. 顾客端聊天窗口左侧显示AI回复，带有"AI助手"的头像和名称标识
10. 顾问监控端同步看到顾客发送的消息和AI的回复
11. 顾客刷新页面，系统从数据库重新加载会话历史
12. 所有历史消息按时间顺序重新显示，包括顾客消息和AI回复

**预期结果**:

* 顾客发送的消息正确显示在聊天窗口右侧
* 显示发送中状态指示器
* AI回复在3秒内响应并显示在聊天窗口左侧
* AI回复内容与询问相关，提供双眼皮手术恢复时间的专业信息
* 整个交互过程流畅，无卡顿
* 消息记录被正确保存到数据库，刷新页面后仍完整显示所有历史消息
* AI回复被视为顾问团队的一部分，在统一的会话流中显示

**异常场景处理**:

* 网络连接中断：系统应显示连接错误提示，并在恢复连接后自动重新连接
* AI服务超时：系统应在10秒后显示"AI响应超时，请稍后再试"的提示
* 消息发送失败：系统应显示"消息发送失败"并提供重试选项
* 历史记录加载失败：系统应提示"加载历史记录失败"并提供重试选项

---

如有疑问请联系项目负责人或在Issue区讨论。
