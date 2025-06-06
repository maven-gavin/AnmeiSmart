# 项目开发SOP（标准操作流程）

## 1. 需求与规划

- 明确项目目标、核心功能、用户群体，参考《项目蓝图.md》
- 组织需求评审会议，确认需求边界与优先级
- 输出需求文档、原型图（UIUX需求文档）、里程碑计划（规划）

## 2. 架构与设计

- 技术选型：前端（React/Next.js/TS）、后端（FastAPI/Python）、数据库、AI服务
- 绘制系统架构图、数据流图、ER图
- 设计API接口文档（OpenAPI）
- UI/UX设计：输出高保真原型，评审交互流程
- 安全设计：权限模型、数据加密、合规要求

## 3. 目录结构规范

- 前端项目结构：
  - web/src/app/ - 基于Next.js的页面路由与客户端组件
  - web/src/components/ - 共享UI组件
  - web/src/service/ - API客户端与各端服务接口
  - web/src/contexts/ - 全局状态管理
  - web/src/types/ - TypeScript类型定义
- 后端项目结构：
  - api/app/api/ - FastAPI路由与接口定义
  - api/app/core/ - 核心功能与配置
  - api/app/services/ - 业务服务
  - api/app/db/ - 数据库模型与连接
  - api/app/models/ - Pydantic数据模型

## 4. 开发流程

- 代码仓库初始化（如Git），规范分支管理（main/dev/feature/hotfix）
- 采用敏捷开发，迭代周期1-2周，定期站会同步进度
- 前端：组件化开发，TS类型覆盖≥95%，严格XSS防护
- 后端：接口开发，类型注解100%，禁用Any，单元测试覆盖≥80%
- AI/算法：模型集成、推理接口、效果验证
- 数据库：表结构迁移、数据初始化脚本
- 代码评审：每次合并需2人以上Code Review

## 5. 测试流程

- 单元测试、集成测试、端到端测试，关键路径全覆盖
- 性能测试：接口延迟<50ms，前端首屏<1s
- 安全测试：SQL注入、XSS、权限绕过等
- 用户验收测试（UAT）：邀请核心用户参与体验

## 6. 部署与上线

- 环境准备：云服务器、Docker、CI/CD流水线
- 自动化部署脚本，支持一键回滚
- 上线前数据备份、灰度发布、监控接入
- 上线后健康检查、日志监控、异常告警

## 7. 维护与迭代

- 定期安全更新、依赖升级、漏洞修复
- 监控系统运行，定期输出运营/技术报告
- 收集用户反馈，持续优化产品体验
- 重大变更需评审、测试、灰度发布

## 8. 命名与编码规范

- 文件命名：
  - React组件：PascalCase（如UserProfile.tsx）
  - 工具函数：camelCase（如apiClient.ts）
  - 常量/类型：PascalCase（如UserRole.ts）
- 变量命名：
  - 普通变量：camelCase
  - 常量：UPPER_SNAKE_CASE
  - React组件：PascalCase
- 代码风格：
  - 使用ESLint和Prettier保持一致的代码风格
  - 后端使用Black格式化工具
  - 提交前运行代码检查

## 9. 文档与规范

- 所有设计、开发、测试、运维文档需同步维护
- 代码注释、README、API文档齐全
- 重要决策、变更需记录在案，便于追溯
- 项目结构更改需更新FILE_MAP.md

---

> 本SOP适用于"安美智享"智能医美服务系统全栈开发，确保项目高质量、可追溯、可持续交付。
