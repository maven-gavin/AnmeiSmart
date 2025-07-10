# Dify集成完整指南

本指南详细介绍了AnmeiSmart项目中Dify多Agent功能的架构设计、安全实现、优化过程和使用方法。

## 📋 目录

1. [功能概述](#-功能概述)
2. [架构设计](#-架构设计)
3. [安全实现](#-安全实现)
4. [快速开始](#-快速开始)
5. [开发使用](#-开发使用)
6. [监控维护](#-监控维护)
7. [故障排除](#-故障排除)
8. [最佳实践](#-最佳实践)

## 🎯 功能概述

AnmeiSmart的Dify集成功能提供：

- **多连接管理**：支持连接多个Dify实例，API密钥加密存储
- **应用自动发现**：自动获取Dify中的应用列表并同步
- **智能Agent分类**：将应用分配给不同的业务功能类型
- **动态切换**：无需重启即可切换Agent配置
- **类型化管理**：为不同场景配置专门的Agent
- **安全防护**：API密钥加密存储，响应数据掩码保护

### Agent类型说明

| Agent类型 | 用途 | 适用场景 |
|----------|------|----------|
| `general_chat` | 通用聊天 | 日常对话、基础咨询 |
| `beauty_plan` | 医美方案生成 | 个性化方案制定 |
| `consultation` | 咨询总结 | 对话分析、内容总结 |
| `customer_service` | 客服支持 | 客户服务、问题解答 |
| `medical_advice` | 医疗建议 | 专业医疗咨询 |

## 🏗️ 架构设计

### 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   API Layer     │    │  Service Layer  │    │  Database Model │
│                 │    │                 │    │                 │
│ - 掩码显示      │────│ - 业务逻辑      │────│ - 自动加密      │
│ - 数据验证      │    │ - 数据转换      │    │ - hybrid_property│
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
┌─────────────────────────────────┼─────────────────────────────────┐
│              Dify Integration Layer                                │
│                                 │                                 │
│  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐  │
│  │ AgentManager    │   │ DifyServiceFactory│  │ Encryption Core │  │
│  │ - Agent缓存     │───│ - 统一实例创建   │  │ - API密钥加密   │  │
│  │ - 类型映射      │   │ - 配置管理       │  │ - 安全解密      │  │
│  │ - 健康检查      │   │ - 错误处理       │  │ - 向后兼容      │  │
│  └─────────────────┘   └─────────────────┘   └─────────────────┘  │
│                                 │                                 │
│  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐  │
│  │ DifyService     │   │ DifyAPIClient   │   │DifyConnection   │  │
│  │ - 消息处理      │───│ - HTTP客户端    │───│ Service         │  │
│  │ - 对话管理      │   │ - 连接测试      │   │ - 连接管理      │  │
│  │ - 错误重试      │   │ - 应用同步      │   │ - 状态同步      │  │
│  └─────────────────┘   └─────────────────┘   └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 核心组件

#### 1. AI服务限界上下文
```
api/app/services/ai/
├── __init__.py              # AI服务抽象接口
├── ai_service.py            # AI服务主类
├── openai_service.py        # OpenAI实现
├── dify_service.py          # Dify实现
├── dify_client.py           # Dify API客户端
├── dify_factory.py          # Dify服务工厂
├── dify_connection_service.py # Dify连接管理
└── agent_manager.py         # Agent管理器
```

#### 2. 数据库模型设计
- **统一命名**：全部使用snake_case命名约定
- **类型安全**：使用枚举类型（SyncStatus, AgentType）
- **索引优化**：为常用查询添加复合索引
- **数据完整性**：唯一约束和检查约束
- **安全存储**：API密钥自动加密存储

#### 3. 安全机制
- **加密算法**：Fernet (AES-128 + HMAC-SHA256)
- **密钥管理**：PBKDF2 + 固定盐值
- **向后兼容**：安全解密机制支持未加密数据
- **响应保护**：API响应中密钥自动掩码

## 🔒 安全实现

### API密钥加密存储

#### 核心加密类
```python
class APIKeyEncryption:
    """API密钥加密解密工具类"""
    
    def encrypt(self, plaintext: str) -> str:
        """加密明文，返回Base64编码的加密字符串"""
    
    def decrypt(self, encrypted_text: str) -> str:
        """解密密文，返回明文字符串"""
    
    def safe_decrypt(self, encrypted_text: str) -> str:
        """安全解密，支持向后兼容"""
    
    def is_encrypted(self, text: str) -> bool:
        """检查文本是否已加密"""
```

#### 数据库模型透明加密
```python
class DifyConnection(BaseModel):
    # 存储加密的API密钥
    _encrypted_api_key = Column("api_key", Text, nullable=False)
    
    @hybrid_property
    def api_key(self) -> str:
        """获取解密后的API密钥"""
        return safe_decrypt_api_key(self._encrypted_api_key)
    
    @api_key.setter
    def api_key(self, value: str) -> None:
        """设置API密钥（自动加密）"""
        self._encrypted_api_key = encrypt_api_key(value)
```

#### 安全特性
- ✅ **加密强度**：AES-128 + HMAC-SHA256
- ✅ **密钥随机性**：每次加密结果不同
- ✅ **数据完整性**：HMAC保证数据未被篡改
- ✅ **向后兼容**：支持未加密数据读取
- ✅ **响应安全**：API响应中密钥被掩码
- ✅ **错误处理**：解密失败优雅降级

### 环境配置

#### 可选：设置自定义加密密钥
```bash
# 生成新密钥
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# 设置环境变量
export ENCRYPTION_KEY="your_generated_key_here"
```

## 🚀 快速开始

### 1. 启动本地Dify实例

```bash
# 克隆Dify仓库
git clone https://github.com/langgenius/dify.git
cd dify/docker

# 启动Dify服务
docker-compose up -d

# 访问 http://localhost/install 完成初始化
```

### 2. 在Dify中创建应用

#### 医美方案生成Agent
```
应用类型：Agent
应用名称：医美方案专家
描述：专门为客户制定个性化医美方案的智能助手

系统提示词：
你是一名专业的医美顾问助手，专门帮助客户制定个性化医美方案。

工作流程：
1. 收集用户基本信息（年龄、性别、肤质等）
2. 了解美容目标和期望效果
3. 评估预算和时间安排
4. 询问医疗史和禁忌症
5. 判断信息完整性
6. 生成个性化方案
7. 根据反馈优化方案

必须确保收集到所有必要信息才能生成方案。
```

#### 通用聊天Agent
```
应用类型：Agent
应用名称：通用助手
描述：处理一般性对话和医美咨询的智能助手

系统提示词：
你是安美智享的智能客服助手，熟悉医美相关知识，能够：
1. 回答医美相关问题
2. 提供治疗建议
3. 解答用户疑问
4. 引导用户使用系统功能

请保持专业、友好的服务态度。
```

#### 咨询总结Agent
```
应用类型：Agent
应用名称：咨询总结专家
描述：分析和总结咨询内容的智能助手

系统提示词：
你是专业的咨询总结分析师，能够：
1. 分析咨询对话内容
2. 提取关键信息
3. 生成结构化总结
4. 识别客户需求和关注点
5. 提供后续建议

请以专业、客观的方式进行分析。
```

### 3. 配置AnmeiSmart集成

1. 启动AnmeiSmart服务：
```bash
# 后端
cd api
source venv/bin/activate
python run_dev.py

# 前端
cd web
npm run dev
```

2. 以管理员身份登录系统
3. 进入 **系统设置 > Dify管理**
4. 点击 **添加连接** 创建Dify连接：

```
连接名称：本地Dify实例
API基础URL：http://localhost/v1
API密钥：app-xxxxxxxxxxxx（自动加密存储）
描述：本地开发环境的Dify实例
设为默认连接：✅
```

5. 点击 **测试** 验证连接
6. 点击 **同步** 获取应用列表

### 4. 配置Agent映射

为每个应用配置对应的功能类型：

1. 选择 **医美方案专家** 应用
2. 点击 **配置为Agent**
3. 设置：
   - Agent类型：`医美方案生成`
   - 描述：为客户制定个性化医美方案
   - 设为该类型默认Agent：✅

## 🛠️ 开发使用

### 统一的服务工厂

```python
from app.services.ai.dify_factory import DifyServiceFactory

# 从AI模型配置创建服务实例
service = DifyServiceFactory.create_from_ai_model_config(ai_config)

# 从连接配置创建服务实例
service = DifyServiceFactory.create_from_connection(connection, app_id)

# 从环境配置创建服务实例
service = DifyServiceFactory.create_from_env_config(env_config)
```

### Agent管理器使用

```python
from app.services.ai.agent_manager import get_agent_manager
from app.db.models.system import AgentType

# 获取Agent管理器
agent_manager = get_agent_manager(db)

# 使用医美方案Agent
beauty_agent = agent_manager.get_agent_by_type(AgentType.BEAUTY_PLAN)
if beauty_agent:
    response = await beauty_agent.generate_response("帮我制定一个面部美容方案", [])

# 使用通用聊天Agent
chat_agent = agent_manager.get_agent_by_type(AgentType.GENERAL_CHAT)
if chat_agent:
    response = await chat_agent.generate_response("你好", [])

# 根据名称使用特定Agent
specific_agent = agent_manager.get_agent_by_name("医美方案专家")
```

### 医美方案服务集成

```python
class BeautyPlanService:
    def __init__(self, db: Session):
        self.db = db
        self.agent_manager = get_agent_manager(db)
    
    def _get_beauty_plan_agent(self):
        """获取医美方案专用Agent"""
        agent = self.agent_manager.get_agent_by_type(AgentType.BEAUTY_PLAN)
        if not agent:
            # 降级到通用Agent
            agent = self.agent_manager.get_agent_by_type(AgentType.GENERAL_CHAT)
        return agent
    
    async def generate_plan(self, user_info: dict):
        agent = self._get_beauty_plan_agent()
        return await agent.generate_response(prompt, [])
```

### 安全的API密钥操作

```python
# 创建连接（自动加密）
connection = DifyConnection(
    name="我的连接",
    api_base_url="https://api.dify.ai",
    api_key="sk-my-secret-key"  # 自动加密存储
)
db.add(connection)
db.commit()

# 读取密钥（自动解密）
connection = db.query(DifyConnection).first()
api_key = connection.api_key  # 自动解密返回明文

# 高级用法：直接操作加密数据
encrypted = connection.get_api_key_encrypted()
connection.set_api_key_raw(encrypted_value)
```

## 📊 监控维护

### 日志监控

#### 关键日志事件
- `使用派生密钥进行加密，建议设置环境变量 ENCRYPTION_KEY`
- `解密失败，返回原文（可能是未加密数据）`
- `Agent健康检查失败`
- `Dify连接同步失败`

#### 监控指标
```python
# 监控Agent健康状态
async def check_agent_health():
    agent_manager = get_agent_manager(db)
    for agent_type in AgentType:
        agent = agent_manager.get_agent_by_type(agent_type)
        if agent:
            health = await agent.health_check()
            logger.info(f"Agent {agent_type}: {'健康' if health else '异常'}")

# 监控连接状态
async def check_connections():
    connections = db.query(DifyConnection).filter(DifyConnection.is_active == True).all()
    for conn in connections:
        try:
            client = DifyAPIClient(conn.api_base_url, conn.api_key)
            result = await client.test_connection()
            logger.info(f"连接 {conn.name}: {'正常' if result['success'] else '异常'}")
        except Exception as e:
            logger.error(f"连接 {conn.name} 检查失败: {e}")
```

### 数据备份与恢复

#### 查看加密状态
```sql
-- 检查哪些密钥已加密
SELECT 
    name,
    LENGTH(api_key) as key_length,
    CASE 
        WHEN api_key LIKE 'Z0FBQUFBQm%' THEN '已加密'
        ELSE '未加密或无密钥'
    END as encryption_status
FROM dify_connections;
```

#### 手动加密剩余数据
```python
from app.core.encryption import get_encryption
from app.db.models.system import DifyConnection

encryption = get_encryption()

# 查找未加密的连接
for conn in db.query(DifyConnection).all():
    raw_key = conn.get_api_key_encrypted()
    if raw_key and not encryption.is_encrypted(raw_key):
        conn.api_key = raw_key  # 触发自动加密
        print(f"已加密连接 {conn.name} 的API密钥")

db.commit()
```

## 🧪 测试验证

### 运行集成测试

```bash
cd api
source venv/bin/activate

# 运行加密存储测试
python -m pytest tests/core/test_encryption.py -v

# 运行数据库模型测试
python -m pytest tests/models/test_system_encryption.py -v

# 运行端到端测试
python test_dify_integration.py
```

### 测试覆盖

- ✅ **加密工具类**：23个测试用例全部通过
- ✅ **数据库模型**：API密钥自动加密/解密
- ✅ **端到端集成**：完整业务流程验证
- ✅ **安全验证**：加密强度和数据保护
- ✅ **向后兼容**：未加密数据处理

## 🔧 故障排除

### 常见问题

#### 1. 连接测试失败
```
❌ 连接失败: 连接错误: Connection refused
```
**解决方案：**
- 确保Dify服务正在运行：`docker-compose ps`
- 检查API基础URL是否正确
- 验证网络连接和防火墙设置

#### 2. API密钥验证失败
```
❌ 同步失败: 401 Unauthorized
```
**解决方案：**
- 检查API密钥是否正确（自动解密验证）
- 确认API密钥有足够权限
- 重新生成API密钥并更新配置

#### 3. 加密解密异常
```
ERROR 解密失败: InvalidToken
```
**解决方案：**
- 检查ENCRYPTION_KEY环境变量
- 验证数据库中的加密数据完整性
- 重新加密损坏的数据

#### 4. Agent健康检查失败
```
❌ Agent健康检查失败
```
**解决方案：**
- 检查Dify应用状态
- 验证应用ID配置
- 重新同步应用列表

### 日志分析

```bash
# 查看详细日志
tail -f api/logs/app.log | grep -E "(Dify|Agent|encryption)"

# 检查数据库状态
psql -h localhost -U postgres -d anmeismart
SELECT name, sync_status, is_active FROM dify_connections;
SELECT model_name, agent_type, enabled FROM ai_model_configs WHERE provider = 'dify';
```

## 🔄 最佳实践

### 1. 安全管理
- **密钥保护**：在生产环境设置独立的ENCRYPTION_KEY
- **权限控制**：限制API密钥权限范围
- **定期轮换**：定期更新API密钥和加密密钥
- **访问日志**：记录所有敏感操作

### 2. 连接管理
- **环境隔离**：为不同环境配置不同连接
- **健康监控**：定期检查连接状态
- **故障切换**：配置备用连接
- **性能优化**：监控响应时间和成功率

### 3. Agent配置
- **类型映射**：为每种业务场景配置专门Agent
- **默认策略**：设置合理的默认Agent和降级策略
- **提示优化**：定期优化Agent提示词
- **版本管理**：记录Agent配置变更历史

### 4. 监控运维
- **性能监控**：监控Agent响应时间和成功率
- **资源管理**：定期清理Agent缓存
- **数据备份**：备份重要配置和对话数据
- **容量规划**：根据使用情况调整资源配置

### 5. 开发规范
- **错误处理**：实现完善的错误处理和重试机制
- **日志记录**：记录关键操作和异常信息
- **测试覆盖**：编写充分的单元测试和集成测试
- **文档维护**：保持文档与代码同步

## 📈 后续扩展

### 计划中的功能
- **性能监控**：Agent响应时间和成功率统计
- **负载均衡**：多实例自动负载分配
- **A/B测试**：不同Agent配置的效果对比
- **自动重试**：失败请求自动重试机制
- **费用追踪**：API调用成本统计

### 扩展开发
- **新Agent类型**：根据业务需求扩展Agent分类
- **自定义适配器**：支持其他AI服务提供商
- **工具函数**：为Agent配置专用工具和插件
- **多模态支持**：图片、语音等多媒体内容处理

## 🏆 技术成果

本Dify集成方案实现了：

✅ **完整架构**：清晰的限界上下文和组件设计
✅ **安全防护**：API密钥加密存储和响应掩码
✅ **代码优化**：消除重复，统一管理，提高质量
✅ **测试覆盖**：全面的单元、集成和端到端测试
✅ **文档完善**：详细的使用指南和最佳实践
✅ **生产就绪**：错误处理、监控、维护机制完备

该实现为AnmeiSmart项目的AI功能提供了坚实的基础，确保了系统的安全性、可维护性和可扩展性。

---

*最后更新：2024年7月* 