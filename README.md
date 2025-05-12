# 安美智享智能医美服务系统
- "安美智享(Anmei Smart) "——专为医美机构定制的AI智能服务平台，聚焦核心业务流程，提升服务效率与安全性。

## 技术栈
- 前端：React 18+/Next.js 15、TypeScript 6、Ant Design/Chakra UI
- 后端：Python 3.12、FastAPI、uvicorn、Pydantic
- 数据库：PostgreSQL、MongoDB、Weaviate/Neo4j
- AI服务：Dify、RAGFlow、DeepSeek、OpenAI API、Stable Diffusion

## 目录结构（建议）
```
/ (项目根目录)
├── web/      # 前端代码
├── api/       # 后端代码
├── docs/          # 文档
├── scripts/       # 脚本与工具
├── README.md      # 项目说明
└── ...
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

---
如有疑问请联系项目负责人或在Issue区讨论。 