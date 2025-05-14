# 安美智享 - 前端应用

这是安美智享(AnmeiSmart)智能医美服务系统的前端应用，基于Next.js框架开发。

## 技术栈

- Next.js 15 - React框架，用于服务端渲染和静态网站生成
- React 19.0.0 - 用户界面库
- TypeScript 6 - 类型安全的JavaScript超集
- TailwindCSS - 实用优先的CSS框架
- Shadcn/UI - 基于TailwindCSS的组件库
- Context API - 状态管理

## 功能模块

- 顾问端：智能客服、术前模拟、方案推荐
- 医生端：治疗方案录入、用药检测、风险评估
- 顾客端：个人中心、聊天咨询、治疗记录、预约管理
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
│   │   ├── advisor/  # 顾问端页面
│   │   ├── doctor/   # 医生端页面
│   │   ├── customer/ # 顾客端页面
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
│   │   ├── customerService.ts # 顾客服务
│   │   ├── doctorService.ts   # 医生服务
│   │   └── advisorService.ts  # 顾问服务
│   ├── contexts/     # 全局状态
│   └── types/        # TypeScript类型定义
```

## 角色与权限

系统支持以下角色:

- 顾问: 对接顾客，提供医美咨询服务
- 医生: 制定医美方案，进行治疗
- 顾客: 咨询医美项目，接受治疗
- 管理员: 管理用户、角色、系统设置
- 运营: 数据分析，内容管理

## 主要功能

### 顾问端

- 智能客服: 多模态聊天，AI自动回复与人工接入
- 术前模拟: 上传客户照片，生成术后效果图
- 方案推荐: 基于客户需求，推荐个性化医美方案

### 医生端

- 治疗方案: 制定个性化治疗方案
- 风险评估: AI辅助评估治疗风险
- 患者管理: 管理患者信息与记录

### 顾客端

- 在线咨询: 与顾问在线交流
- 治疗记录: 查看历史治疗记录
- 预约管理: 预约、查看、取消治疗

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
