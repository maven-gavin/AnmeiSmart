# 安美智享智能医美服务系统 - 后端API

## 技术栈
- Python 3.12
- FastAPI
- SQLAlchemy (PostgreSQL)
- MongoDB
- Weaviate
- JWT认证
- 单元测试 (pytest)

## 开发环境设置

1. 创建并激活虚拟环境:
```powershell
# Windows
python -m venv venv
.\venv\Scripts\Activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

2. 安装依赖:
```bash
# 使用uv加速安装
uv pip install -r requirements.txt
```

3. 设置环境变量:
- 复制`.env.example`为`.env`
- 修改配置项（数据库连接等）

4. 初始化数据库:
```bash
python app/db/init_db.py
```

5. 启动开发服务器:
```bash
uvicorn app.main:app --reload
```

## API文档
- Swagger UI: http://localhost:8000/api/v1/docs
- ReDoc: http://localhost:8000/api/v1/redoc

## 项目结构
```
api/
├── alembic/            # 数据库迁移
├── app/
│   ├── core/          # 核心配置
│   │   ├── config.py  # 应用配置
│   │   └── security.py # 安全工具
│   ├── crud/         # CRUD操作
│   ├── db/           # 数据库模型和工具
│   ├── models/       # Pydantic模型
│   ├── api/          # API路由
│   └── services/     # 业务逻辑
├── tests/            # 单元测试
├── scripts/          # 工具脚本
├── main.py          # 应用入口
└── requirements.txt  # 项目依赖
```

## API端点
- `/api/v1/auth/login` - 用户登录
- `/api/v1/users/` - 用户管理
  - POST / - 创建用户
  - GET /me - 获取当前用户信息
  - PUT /me - 更新当前用户信息
  - GET /{user_id} - 获取指定用户信息

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

3. Weaviate
   - 向量数据库
   - 用于相似搜索和AI推荐

## 部署
1. 准备环境变量
2. 安装依赖
3. 初始化数据库
4. 使用uvicorn或gunicorn启动:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 贡献指南
1. Fork项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 许可证
MIT 