# Agent配置常量管理文档

## 📋 概述

本文档说明了Agent配置默认值的统一管理方案，避免在多处硬编码相同的值。

## 🎯 设计目标

1. **单一数据源**：所有默认值在一个地方定义
2. **易于维护**：修改默认值只需要改一个地方
3. **环境可配置**：支持通过环境变量覆盖默认值
4. **类型安全**：前后端都有类型检查

---

## 📁 前端实现

### 配置位置：`web/src/config/index.ts`

```typescript
// Agent配置默认值
export const AGENT_DEFAULT_BASE_URL = process.env.NEXT_PUBLIC_AGENT_DEFAULT_BASE_URL || 'http://localhost:8000/v1';
export const AGENT_DEFAULT_TIMEOUT = 30;
export const AGENT_DEFAULT_MAX_RETRIES = 3;
```

### 使用方式

所有需要Agent默认配置的地方，从`@/config`导入：

```typescript
import { AGENT_DEFAULT_BASE_URL, AGENT_DEFAULT_TIMEOUT, AGENT_DEFAULT_MAX_RETRIES } from '@/config';

// 使用示例
const [baseUrl, setBaseUrl] = useState(AGENT_DEFAULT_BASE_URL);
const [timeoutSeconds, setTimeoutSeconds] = useState(AGENT_DEFAULT_TIMEOUT);
const [maxRetries, setMaxRetries] = useState(AGENT_DEFAULT_MAX_RETRIES);
```

### 已更新的文件

1. ✅ `web/src/config/index.ts` - 定义常量
2. ✅ `web/src/app/agents/setup/page.tsx` - Agent设置页面
3. ✅ `web/src/components/settings/AgentConfigPanel.tsx` - Agent配置面板

---

## 🐍 后端实现

### 配置位置：`api/app/core/config.py`

```python
class Settings(BaseSettings):
    """应用配置类"""
    
    # Agent配置默认值
    AGENT_DEFAULT_BASE_URL: str = "http://localhost:8000/v1"
    AGENT_DEFAULT_TIMEOUT: int = 30
    AGENT_DEFAULT_MAX_RETRIES: int = 3
```

### 使用方式

在需要使用默认值的地方，导入并使用：

```python
from app.core.config import get_settings

settings = get_settings()

# 在数据库模型中使用
base_url = Column(String(1024), nullable=False, 
                  default=lambda: settings.AGENT_DEFAULT_BASE_URL, 
                  comment="Agent API基础URL")

# 在Pydantic Schema中使用
baseUrl: str = Field(default_factory=lambda: settings.AGENT_DEFAULT_BASE_URL, 
                     description="Agent API基础URL")
```

### 已更新的文件

1. ✅ `api/app/core/config.py` - 定义常量
2. ✅ `api/app/ai/infrastructure/db/agent_config.py` - 数据库模型
3. ✅ `api/app/ai/schemas/ai.py` - Pydantic Schema

---

## 🌍 环境变量配置

### 前端环境变量

在`.env.local`文件中可以覆盖默认值：

```bash
# Agent配置
NEXT_PUBLIC_AGENT_DEFAULT_BASE_URL=https://api.dify.ai/v1
```

### 后端环境变量

在`.env`文件中可以覆盖默认值：

```bash
# Agent配置
AGENT_DEFAULT_BASE_URL=https://api.dify.ai/v1
AGENT_DEFAULT_TIMEOUT=60
AGENT_DEFAULT_MAX_RETRIES=5
```

---

## 📝 最佳实践

### ✅ 推荐做法

```typescript
// ✅ 好：使用常量
import { AGENT_DEFAULT_BASE_URL } from '@/config';
const baseUrl = AGENT_DEFAULT_BASE_URL;
```

```python
# ✅ 好：使用配置
from app.core.config import get_settings
settings = get_settings()
base_url = settings.AGENT_DEFAULT_BASE_URL
```

### ❌ 避免做法

```typescript
// ❌ 坏：硬编码
const baseUrl = 'http://localhost:8000/v1';
```

```python
# ❌ 坏：硬编码
base_url = "http://localhost:8000/v1"
```

---

## 🔄 迁移指南

如果需要修改默认值，按以下步骤操作：

### 1. 修改本地开发默认值

**前端**：修改 `web/src/config/index.ts`

```typescript
export const AGENT_DEFAULT_BASE_URL = 'http://localhost:8000/v1';  // 修改这里
```

**后端**：修改 `api/app/core/config.py`

```python
AGENT_DEFAULT_BASE_URL: str = "http://localhost:8000/v1"  # 修改这里
```

### 2. 修改生产环境配置

通过环境变量设置：

```bash
# 前端 .env.production
NEXT_PUBLIC_AGENT_DEFAULT_BASE_URL=https://api.your-domain.com/v1

# 后端 .env
AGENT_DEFAULT_BASE_URL=https://api.your-domain.com/v1
```

### 3. 更新现有数据库记录（如果需要）

```sql
-- 批量更新现有记录
UPDATE agent_configs 
SET base_url = 'http://localhost:8000/v1'
WHERE base_url = 'http://localhost/v1';
```

---

## 🎯 总结

通过统一管理Agent配置常量，我们实现了：

- ✅ **单一数据源**：所有默认值集中管理
- ✅ **易于维护**：修改一处生效全局
- ✅ **环境灵活**：支持环境变量覆盖
- ✅ **类型安全**：前后端都有类型定义
- ✅ **最佳实践**：符合配置管理的标准模式

## 📚 相关文档

- [Agent配置管理](./agent-chat-complete-implementation-guide.md)
- [环境配置说明](../README.md)

