# 安美智享 - API 服务

这是安美智享(AnmeiSmart)智能医美服务系统的后端API服务，基于FastAPI框架开发。

## 技术栈

- FastAPI - 高性能异步API框架
- SQLAlchemy - ORM框架
- PostgreSQL - 关系型数据库
- MongoDB - 非关系型数据库
- Pydantic - 数据验证
- JWT - 用户认证

## 环境需求

- Python 3.12 或更高版本
- PostgreSQL 15或更高版本
- MongoDB 6.0或更高版本

## 安装步骤

1. 克隆代码库
2. 创建并激活虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows
```

3. 安装依赖

```bash
pip install -r requirements.txt
```

4. 配置环境变量

创建 `.env`文件，参考 `env.example`文件，设置以下环境变量:

```
DATABASE_URL=postgresql://用户名:密码@localhost:5432/AnmeiSmart
MONGODB_URL=mongodb://localhost:27017
SECRET_KEY=你的密钥
```

5. 初始化数据库

```bash
python scripts/init_db.py
```

6. 启动服务

```bash
uvicorn main:app --reload
```

## API文档

启动服务后，可以访问以下URL查看API文档:

- Swagger UI: http://localhost:8000/api/v1/docs
- ReDoc: http://localhost:8000/api/v1/redoc

## 认证API

### 登录

```
POST /api/v1/auth/login
```

请求体:

```json
{
  "username": "user@example.com",
  "password": "password"
}
```

响应:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 注册

```
POST /api/v1/auth/register
```

请求体:

```json
{
  "email": "newuser@example.com",
  "username": "newuser",
  "password": "password",
  "roles": ["customer"]
}
```

### 获取当前用户信息

```
GET /api/v1/auth/me
```

请求头:

```
Authorization: Bearer your_access_token
```

### 获取用户角色

```
GET /api/v1/auth/roles
```

请求头:

```
Authorization: Bearer your_access_token
```

## 用户管理API

### 获取用户列表

```
GET /api/v1/users
```

### 创建用户

```
POST /api/v1/users
```

请求体:

```json
{
  "email": "newuser@example.com",
  "username": "newuser",
  "password": "password",
  "roles": ["admin", "consultant"],
  "phone": "13800138000"
}
```

### 更新用户

```
PUT /api/v1/users/{user_id}
```

### 获取角色列表

```
GET /api/v1/users/roles/all
```

## AI服务API

### 获取AI回复

```
POST /api/v1/ai/chat
```

请求体:

```json
{
  "conversation_id": "会话ID",
  "content": "用户问题内容",
  "type": "text",
  "sender_id": "用户ID",
  "sender_type": "customer"
}
```

响应:

```json
{
  "id": "msg_xxx",
  "conversation_id": "会话ID",
  "content": "AI回复内容",
  "type": "text",
  "sender_id": "ai",
  "sender_type": "ai",
  "timestamp": "2024-01-01T00:00:00",
  "is_read": false,
  "is_important": false
}
```

## AI服务配置

AI服务需要在环境变量中设置以下参数:

```
# AI服务配置
AI_API_KEY=your_ai_api_key
AI_MODEL=default
AI_API_BASE_URL=https://api.example.com

# OpenAI配置（可选）
OPENAI_API_KEY=your_openai_api_key
OPENAI_API_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-3.5-turbo
```

在不设置API密钥的情况下，系统会使用内置知识库提供医美领域的基础问答服务。

## 开发指南

- 添加新的API端点: 在 `app/api/v1/endpoints`目录创建新文件
- 添加新的数据库模型: 在 `app/db/models`目录创建新文件
- 添加新的Pydantic模型: 在 `app/schemas`目录创建新文件

## 测试

运行单元测试:

```bash
pytest
```

## 部署

1. 构建Docker镜像

```bash
docker build -t anmeismart-api .
```

2. 运行容器

```bash
docker run -d -p 8000:8000 --name anmeismart-api anmeismart-api
```

## 项目结构

```
api/
├── migrations/            # 数据库迁移
├── app/
│   ├── core/          # 核心配置
│   │   ├── config.py  # 应用配置
│   │   └── security.py # 安全工具
│   ├── db/           # 数据库模型和工具
│   ├── schemas/       # Pydantic模型（数据验证和序列化）
│   ├── api/          # API路由
│   └── services/     # 业务逻辑
├── tests/            # 单元测试
├── scripts/          # 工具脚本
├── main.py          # 应用入口
└── requirements.txt  # 项目依赖
```

## API端点

- `/api/v1/auth/login` - 用户登录
- `/api/v1/auth/register` - 用户注册
- `/api/v1/auth/me` - 获取当前用户信息
- `/api/v1/auth/roles` - 获取用户角色
- `/api/v1/users/` - 用户管理
  - GET / - 获取用户列表
  - POST / - 创建用户
  - PUT /{user_id} - 更新用户信息
  - GET /{user_id} - 获取指定用户信息
- `/api/v1/users/roles/all` - 获取所有角色

## 开发规范

1. 代码质量

   - 所有函数必须有类型注解
   - 禁止使用Any类型
   - 所有API端点必须有文档字符串
   - 单元测试覆盖率要求≥80%
2. Git提交规范

   - feat: 新功能
   - fix: 修复bug
   - docs: 文档更新
   - style: 代码格式
   - refactor: 重构
   - test: 测试相关
   - chore: 构建过程或辅助工具的变动

## 运行测试

```powershell
# Windows
.\scripts\test.ps1

# Linux/Mac
./scripts/test.sh
```

## 数据库

1. PostgreSQL

   - 用于结构化数据存储
   - 用户信息、预约记录等
2. MongoDB

   - 用于非结构化数据
   - 用户行为日志、系统日志等

   - 向量数据库
   - 用于相似搜索和AI推荐

## 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 许可证

MIT

## Redis配置

### 环境变量配置

Redis配置通过环境变量管理，支持两种配置方式：

#### 方式1：使用REDIS_URL（推荐）
```bash
REDIS_URL=redis://:password@host:port/db
```

#### 方式2：使用分离配置参数
```bash
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_password
REDIS_DB=0
```

### 配置步骤

1. 复制环境变量示例文件：
```bash
cp env.example .env
```

2. 编辑`.env`文件，修改Redis配置：
```bash
# Redis配置
REDIS_URL=redis://:difyai123456@localhost:6379
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=difyai123456
REDIS_DB=0
```

3. 确保Redis服务已启动：
```bash
# 使用Docker启动Redis
docker run -d --name redis -p 6379:6379 redis:7-alpine redis-server --requirepass difyai123456

# 或使用本地Redis服务
redis-server --requirepass difyai123456
```

### WebSocket分布式架构

项目使用Redis Pub/Sub实现分布式WebSocket架构，支持：
- 跨实例消息广播
- 多设备连接管理
- 在线状态检测
- 设备类型区分

### 安全注意事项

- ⚠️ **生产环境**：请修改默认密码
- ⚠️ **网络安全**：建议使用VPC内网或加密连接
- ⚠️ **权限控制**：Redis实例应限制访问权限

## 推送通知服务

### 当前状态

项目当前使用**日志记录推送服务**，所有推送通知都会在日志中记录，适合开发和测试环境。

### 配置说明

在`.env`文件中配置推送服务类型：
```bash
# 推送通知配置
NOTIFICATION_PROVIDER=logging  # 当前使用日志记录服务
```

### 支持的消息类型

- ✅ 聊天消息推送
- ✅ 顾问回复通知
- ✅ 系统通知
- ✅ 设备特定推送（mobile/desktop）
- ✅ 在线/离线状态检测

### 推送策略

- **在线用户**：通过WebSocket实时推送到所有设备
- **离线用户**：记录推送日志（生产环境将发送真实推送）
- **移动端优先**：重要消息优先推送到移动设备
- **设备区分**：支持按设备类型精确推送

### 日志示例

```
INFO  📱 推送通知 [mobile] [优先级: high]: user_123
INFO     标题: 顾问回复
INFO     内容: 您好，关于您的咨询问题...
```

### TODO: 未来扩展计划

#### 真实推送服务集成
- **Firebase FCM**：支持Android和Web推送
- **Apple APNs**：支持iOS推送
- **第三方服务**：极光推送、友盟推送等

#### 高级功能
- 用户推送偏好设置
- 推送模板管理
- 推送统计和监控
- 时间段控制（免打扰模式）
- 推送失败重试机制

#### 配置示例（未来使用）
```bash
# Firebase FCM配置
NOTIFICATION_PROVIDER=firebase
FIREBASE_CREDENTIALS_PATH=/path/to/firebase-credentials.json

# Apple APNs配置
APNS_CERTIFICATE_PATH=/path/to/apns-certificate.p12
APNS_CERTIFICATE_PASSWORD=your_certificate_password
```
