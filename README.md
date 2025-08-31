# AnmeiSmart 安美售后智能服务平台

## 项目概述

本项目采用双系统架构设计，通过分工协作实现完整的AI驱动医美售后服务解决方案：

## 技术栈

- 前端: Next.js, React, TypeScript, TailwindCSS
- 后端: FastAPI, Python, PostgreSQL, MongoDB
- Tauri 2.0：支持桌面和移动端
- Rust：Tauri后端逻辑
- 响应式设计：适配不同屏幕尺寸
- PWA：渐进式Web应用支持

## 多端实现待实施步骤

### 第一阶段：桌面端实现

```
# 1. 安装Tauri CLI
npm install -g @tauri-apps/cli

# 2. 在项目根目录初始化Tauri
cd AnmeiSmart
mkdir desktop && cd desktop
npm create tauri-app@latest . --template vanilla-ts

# 3. 配置Tauri
```

```
// desktop/tauri.conf.json
{
  "productName": "AnmeiSmart Desktop",
  "version": "1.0.0",
  "build": {
    "frontendDist": "../web/out",
    "devUrl": "http://localhost:3000"
  },
  "app": {
    "windows": [
      {
        "title": "AnmeiSmart 医美智能系统",
        "width": 1200,
        "height": 800,
        "minWidth": 800,
        "minHeight": 600
      }
    ]
  },
  "bundle": {
    "targets": ["msi", "deb", "dmg"]
  }
}

```

### 第二阶段：移动端实现

```
# 1. 创建移动端项目
mkdir mobile && cd mobile
npm create tauri-app@latest . --template vanilla-ts

# 2. 添加移动端支持
npm run tauri android init
npm run tauri ios init
```

## 推荐实施顺序

第一步：重构现有Web代码，提取共享组件到shared/目录
第二步：实现桌面端，验证Tauri集成
第三步：适配移动端UI和交互
第四步：添加平台特定功能
第五步：完善构建和部署流程

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
├── web/                 # 前端应用
│   │   ├── public/          # 静态资源
│   │   └── src/             # 源代码
│   │       ├── app/         # 页面组件
│   │       ├── components/  # 可复用组件
│   │       ├── contexts/    # React上下文
│   │       ├── service/     # 服务层
│   │       └── types/       # 类型定义
├── docs/                # 项目文档
├── desktop/                # （待新增）：Tauri桌面应用
│   │   ├── src-tauri/         # Tauri Rust后端
│   │   ├── src/               # 共享前端代码
│   │   └── tauri.conf.json    # Tauri配置
├── mobile/                 # （待新增）：Tauri移动应用
│   │   ├── src-tauri/         # 移动端Tauri配置
│   │   ├── src/               # 移动端适配代码
│   │   └── gen/               # 生成的移动端代码
└── shared/                 # （待新增）：共享组件和逻辑
    │    ├── components/        # 跨平台UI组件
    │    ├── services/          # 共享业务逻辑
    │    ├── types/             # 共享类型定义
    │    └── utils/             # 工具函数
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
