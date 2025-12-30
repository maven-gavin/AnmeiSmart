# 安美智享 - 前端应用

这是安美智享(AnmeiSmart)智能服务系统的前端应用，基于Next.js框架开发。

## 技术栈

- Next.js 15 - React框架，用于服务端渲染和静态网站生成
- React 19.0.0 - 用户界面库
- TypeScript 6 - 类型安全的JavaScript超集
- TailwindCSS - 实用优先的CSS框架
- Shadcn/UI - 基于TailwindCSS的组件库
- Context API - 状态管理

## 功能模块

- 顾问端：智能客服
- 医生端：患者管理
- 客户端：个人中心、聊天咨询
- 管理员端：用户管理、角色管理、系统设置、数据统计
- 运营端：数据分析、方案审核、项目管理

## 开始使用

### 环境需求

- Node.js 18.17 或更高版本
- npm 9.6.7 或更高版本

### 安装

1. 克隆代码库
2. 安装依赖:

```bash
npm install
```

### 开发

运行开发服务器:

```bash
npm run dev
```

浏览器访问 [http://localhost:3000](http://localhost:3000) 查看效果。

### 构建

创建生产构建:

```bash
npm run build
```

### 生产环境

启动生产服务器:

```bash
npm start
```

## 项目结构

```
web/
├── public/           # 静态资源
├── src/
│   ├── app/          # 页面与路由（Next.js App Router）
│   │   ├── consultant/  # 顾问端页面
│   │   ├── doctor/   # 医生端页面
│   │   ├── customer/ # 客户端页面
│   │   ├── admin/    # 管理员端页面
│   │   └── login/    # 登录页面
│   ├── components/   # 可复用组件
│   │   ├── ui/       # UI基础组件
│   │   ├── auth/     # 认证相关组件
│   │   ├── chat/     # 聊天相关组件
│   │   └── layout/   # 布局组件
│   ├── service/      # API客户端与服务
│   │   ├── apiClient.ts    # API客户端
│   │   ├── authService.ts  # 认证服务
│   │   ├── chatService.ts  # 聊天服务
│   │   ├── customerService.ts # 客户服务
│   │   ├── doctorService.ts   # 医生服务
│   │   └── consultantService.ts  # 顾问服务
│   ├── contexts/     # 全局状态
│   └── types/        # TypeScript类型定义
```

## 角色与权限

系统支持以下角色:

- 顾问: 对接客户，提供咨询服务
- 医生: 制定方案，进行治疗
- 客户: 咨询项目，接受治疗
- 管理员: 管理用户、角色、系统设置
- 运营: 数据分析，内容管理

## 主要功能

### 顾问端

- 智能客服: 多模态聊天，AI自动回复与人工接入
<!-- 方案推荐功能已下线，术前模拟功能已下线 -->

### 医生端

- 患者管理: 管理患者信息与记录

### 客户端

- 在线咨询: 与顾问在线交流

### 管理员端

- 用户管理: 创建、编辑、查询用户
- 角色管理: 管理系统角色与权限
- 系统设置: 配置系统参数

## 开发指南

1. 新增页面: 在`src/app`下创建对应路径的目录和page.tsx文件
2. 新增组件: 在`src/components`下创建，保持组件的单一职责
3. 新增API服务: 在`src/service`中扩展现有服务或添加新服务
4. 状态管理: 全局状态使用Context API，组件内状态使用useState/useReducer

## 构建与部署

### 开发环境
```bash
npm run dev
```

### 测试
```bash
npm run test
npm run lint
```

### 生产构建
```bash
npm run build
npm start
```

## 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 许可证

MIT

## 聊天功能测试改进

### 角色分离设计与实现

我们对聊天功能的自动化测试进行了重大改进，使测试更加符合实际业务场景：

1. **客户-顾问角色分离**：
   - 由客户创建会话，顾问接入会话
   - 客户和顾问分别使用独立的浏览器上下文
   - 客户和顾问各自维护独立的认证令牌

2. **会话创建符合业务流程**：
   - 优先使用客户身份创建咨询会话
   - 顾问接入客户已创建的会话
   - 双向实时消息验证机制

3. **完善的异常处理**：
   - 令牌失效自动重新获取
   - WebSocket连接断开自动重连
   - 多角色测试自动降级策略

### 运行测试方法

```powershell
# 运行所有测试
npm run test:e2e

# 只运行顾问应答测试
npm run test:e2e -- src/__tests__/e2e/chat/consultant-response.spec.ts

# 在UI调试模式中运行
npm run test:e2e:ui
```

详细的测试设计和说明请查看 [测试文档](src/__tests__/e2e/README.md)
