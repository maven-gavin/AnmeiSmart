# 顾问方案推荐功能实现

## 功能概述

基于现有的 `PlanPageClient.tsx` 设计，我们完成了完整的顾问方案推荐业务的前后端实现，包括：

- 个性化方案管理（创建、编辑、分享、状态管理）
- 项目模板库管理
- 智能推荐算法
- 完整的数据库设计和API实现

## 技术架构

### 后端实现

#### 1. 数据库模型 (`api/app/db/models/consultant.py`)

- **PersonalizedPlan**: 个性化方案模型
- **ProjectTemplate**: 项目模板模型  
- **ProjectType**: 项目类型模型
- **SimulationImage**: 术前模拟图像模型
- **CustomerPreference**: 客户偏好模型
- **PlanVersion**: 方案版本控制模型

#### 2. Schema定义 (`api/app/schemas/consultant.py`)

遵循DDD规范，实现了：
- 响应Schema类（如 `PersonalizedPlanResponse`）
- 创建Schema类（如 `PersonalizedPlanCreate`）
- 更新Schema类（如 `PersonalizedPlanUpdate`）
- 所有Schema都实现了 `from_model` 静态方法用于ORM到Schema的转换

#### 3. 服务层 (`api/app/services/consultant_service.py`)

- **ConsultantService**: 顾问服务类，处理所有业务逻辑
- 包含方案管理、项目模板管理、智能推荐等功能
- 所有方法返回Schema对象，遵循DDD分层规范

#### 4. API端点 (`api/app/api/v1/endpoints/consultant.py`)

提供RESTful API接口：
- `GET /consultant/plans` - 获取所有方案
- `POST /consultant/plans` - 创建新方案
- `PUT /consultant/plans/{plan_id}` - 更新方案
- `DELETE /consultant/plans/{plan_id}` - 删除方案
- `GET /consultant/project-templates` - 获取项目模板
- `POST /consultant/recommendations` - 获取智能推荐

### 前端实现

#### 1. 服务层更新 (`web/src/service/consultantService.ts`)

- 更新了API调用以连接真实后端
- 保留了模拟数据作为回退机制
- 添加了错误处理和TypeScript类型支持

#### 2. 组件优化 (`web/src/app/consultant/plan/PlanPageClient.tsx`)

- 改进了错误处理和用户反馈
- 添加了加载状态管理
- 保持了原有的UI设计和用户体验

## 数据库设计

### 表结构

1. **personalized_plans** - 个性化方案主表
2. **project_templates** - 项目模板表
3. **project_types** - 项目类型表
4. **simulation_images** - 术前模拟图像表
5. **customer_preferences** - 客户偏好表
6. **plan_versions** - 方案版本记录表

### 外键关系

- 方案关联到顾问和客户
- 模拟图像关联到项目类型和顾问
- 客户偏好关联到客户
- 方案版本关联到方案

## 部署和测试

### 1. 数据库迁移

```bash
cd api
source venv/bin/activate
alembic upgrade head
```

### 2. 初始化测试数据

```bash
python scripts/init_consultant_data.py
```

### 3. 启动服务

**后端服务器:**
```bash
cd api
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**前端服务器:**
```bash
cd web
npm run dev
```

### 4. 访问应用

- 前端地址: http://localhost:3000
- 方案管理页面: http://localhost:3000/consultant/plan
- API文档: http://localhost:8000/docs

## 功能测试指南

### 1. 方案列表查看

- 访问 `/consultant/plan` 页面
- 查看左侧方案列表
- 测试搜索和筛选功能

### 2. 创建新方案

- 点击"创建新方案"按钮
- 填写客户信息和需求
- 提交创建，查看是否成功

### 3. 方案详情查看

- 点击方案列表中的任一方案
- 查看右侧详情展示
- 验证客户信息和项目列表显示

### 4. 方案状态管理

- 测试"分享给客户"功能
- 查看状态变化（草稿 → 已分享）

### 5. API测试

使用Postman或类似工具测试API端点：

```bash
# 获取所有方案
GET http://localhost:8000/api/v1/consultant/plans

# 创建新方案
POST http://localhost:8000/api/v1/consultant/plans
Content-Type: application/json
{
  "customer_id": "test-customer",
  "customer_name": "测试客户",
  "customer_profile": {
    "age": 28,
    "gender": "female",
    "concerns": ["双眼皮", "鼻部"],
    "budget": 20000
  },
  "projects": [],
  "estimated_timeframe": "2周"
}
```

## 特性说明

### 1. 智能推荐算法

基于客户画像（年龄、性别、关注问题、预算）自动推荐合适的项目模板：
- 年龄匹配
- 预算范围匹配（允许20%弹性）
- 关注问题匹配
- 置信度评分

### 2. 版本控制

每次方案更新都会自动创建版本记录，支持历史追踪。

### 3. 状态管理

方案支持四种状态：
- `draft` - 草稿
- `shared` - 已分享
- `accepted` - 已接受
- `rejected` - 已拒绝

### 4. 错误处理

- 前端API调用失败时自动回退到模拟数据
- 后端API提供详细的错误信息
- 用户友好的错误提示

## 扩展功能建议

1. **AI增强推荐**: 集成机器学习模型提升推荐准确性
2. **实时通知**: WebSocket实现方案状态变更通知
3. **文件上传**: 支持方案文档和图片上传
4. **权限管理**: 基于角色的访问控制
5. **数据分析**: 方案效果和客户满意度统计

## 注意事项

1. 当前使用的是测试用的顾问ID和客户ID
2. 实际部署时需要集成真实的用户认证系统
3. 项目模板数据需要根据实际业务需求调整
4. 建议添加数据备份和恢复机制

## 代码规范遵循

- **DDD分层架构**: Controller、Service、Schema分离
- **数据转换**: Service层负责ORM到Schema转换
- **错误处理**: 统一的异常处理机制
- **TypeScript**: 前端完整的类型定义
- **React最佳实践**: 组件化、Hook使用、状态管理 