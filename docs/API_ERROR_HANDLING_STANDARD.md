# 前后端API异常处理开发规范

## 概述

本文档定义了前后端API交互的统一异常处理规范，包括响应数据结构、错误码定义、异常处理流程等。适用于所有前后端分离的项目。

## 核心原则

1. **统一响应格式**：所有API响应使用统一的数据结构
2. **业务错误与系统错误分离**：通过错误码区分业务错误和系统错误
3. **自动错误处理**：前端自动处理错误提示，后端统一异常处理
4. **类型安全**：充分利用类型系统保证代码安全

---

## 一、API响应数据结构

### 1.1 统一响应格式

所有API响应必须遵循以下格式：

```typescript
// TypeScript 类型定义
interface ApiResponse<T> {
  code: number        // 业务状态码，0表示成功
  message: string     // 业务提示信息
  data?: T           // 业务数据（可选）
  timestamp?: string  // 响应时间戳（UTC）
}
```

```python
# Python 类型定义（Pydantic）
from typing import Generic, Optional, TypeVar
from pydantic import BaseModel, Field
from datetime import datetime

T = TypeVar("T")

class ApiResponse(BaseModel, Generic[T]):
    code: int = Field(..., description="业务状态码，0表示成功")
    message: str = Field(..., description="业务提示信息")
    data: Optional[T] = Field(default=None, description="业务数据")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="响应时间戳（UTC时间）"
    )
```

### 1.2 成功响应示例

```json
{
  "code": 0,
  "message": "操作成功",
  "data": {
    "id": "123",
    "name": "示例"
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### 1.3 错误响应示例

```json
{
  "code": 40001,
  "message": "角色名称已存在",
  "data": null,
  "timestamp": "2024-01-01T00:00:00Z"
}
```

---

## 二、错误码定义

### 2.1 错误码规范

| 错误码范围 | 错误类型 | 说明 | HTTP状态码 |
|-----------|---------|------|-----------|
| 0 | 成功 | 操作成功 | 200 |
| 40000-49999 | 业务错误 | 预期的业务错误，如验证失败、权限不足、资源不存在 | 200 |
| 50000+ | 系统错误 | 意外的系统错误，如服务器内部错误、数据库错误 | 500 |

### 2.2 标准错误码

```python
# Python 错误码定义
from enum import IntEnum

class ErrorCode(IntEnum):
    SUCCESS = 0
    VALIDATION_ERROR = 40000      # 参数验证错误
    BUSINESS_ERROR = 40001        # 业务逻辑错误
    PERMISSION_DENIED = 40003     # 权限拒绝
    NOT_FOUND = 40400            # 资源不存在
    SYSTEM_ERROR = 50000         # 系统内部错误
    NETWORK_ERROR = 50001        # 网络错误
```

```typescript
// TypeScript 错误码定义
export enum ErrorCode {
  SUCCESS = 0,
  VALIDATION_ERROR = 40000,
  BUSINESS_ERROR = 40001,
  PERMISSION_DENIED = 40003,
  NOT_FOUND = 40400,
  SYSTEM_ERROR = 50000,
  NETWORK_ERROR = 50001,
}
```

---

## 三、后端异常处理规范

### 3.1 异常类定义

```python
from typing import Any, Dict, Optional
from fastapi import status

class AppException(Exception):
    """应用统一异常基类"""
    
    def __init__(
        self,
        message: str,
        *,
        code: int,
        status_code: int,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


class BusinessException(AppException):
    """业务异常：预期的业务错误"""
    
    def __init__(
        self,
        message: str,
        *,
        code: int = ErrorCode.BUSINESS_ERROR,
        status_code: int = status.HTTP_200_OK,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message,
            code=code,
            status_code=status_code,
            details=details,
        )


class SystemException(AppException):
    """系统异常：意外的系统错误"""
    
    def __init__(
        self,
        message: str = "系统异常，请联系管理员",
        *,
        code: int = ErrorCode.SYSTEM_ERROR,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message,
            code=code,
            status_code=status_code,
            details=details,
        )
```

### 3.2 Controller异常处理模式

```python
from fastapi import APIRouter, Depends, status
from typing import List
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

def _handle_unexpected_error(message: str, exc: Exception) -> SystemException:
    """处理意外错误"""
    logger.error(f"{message}: {exc}", exc_info=True)
    return SystemException(message=message, code=ErrorCode.SYSTEM_ERROR)

@router.get("", response_model=ApiResponse[List[EntityResponse]])
async def list_entities(
    service: EntityService = Depends(get_entity_service)
) -> ApiResponse[List[EntityResponse]]:
    """获取实体列表"""
    try:
        entities = service.get_all()
        responses = [EntityResponse.model_validate(e) for e in entities]
        return ApiResponse.success(responses, message="获取成功")
    except Exception as e:
        raise _handle_unexpected_error("获取列表失败", e)

@router.post("", response_model=ApiResponse[EntityResponse], status_code=status.HTTP_201_CREATED)
async def create_entity(
    entity_in: EntityCreate,
    service: EntityService = Depends(get_entity_service)
) -> ApiResponse[EntityResponse]:
    """创建实体"""
    try:
        entity = service.create(entity_in)
        response = EntityResponse.model_validate(entity)
        return ApiResponse.success(response, message="创建成功")
    except BusinessException:
        # 业务异常直接抛出，由全局异常处理器处理
        raise
    except Exception as e:
        # 其他异常转换为系统异常
        raise _handle_unexpected_error("创建失败", e)

@router.get("/{entity_id}", response_model=ApiResponse[EntityResponse])
async def get_entity(
    entity_id: str,
    service: EntityService = Depends(get_entity_service)
) -> ApiResponse[EntityResponse]:
    """获取实体详情"""
    try:
        entity = service.get_by_id(entity_id)
        if not entity:
            raise BusinessException(
                "实体不存在",
                code=ErrorCode.NOT_FOUND,
                status_code=status.HTTP_404_NOT_FOUND
            )
        response = EntityResponse.model_validate(entity)
        return ApiResponse.success(response, message="获取成功")
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("获取详情失败", e)
```

### 3.3 Service层异常处理

```python
class EntityService:
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, data: EntityCreate) -> Entity:
        """创建实体"""
        # 业务验证
        existing = self.db.query(Entity).filter(Entity.name == data.name).first()
        if existing:
            raise BusinessException(
                "实体名称已存在",
                code=ErrorCode.VALIDATION_ERROR
            )
        
        # 创建实体
        entity = Entity(**data.model_dump())
        self.db.add(entity)
        self.db.commit()
        return entity
    
    def get_by_id(self, entity_id: str) -> Optional[Entity]:
        """根据ID获取实体"""
        return self.db.query(Entity).filter(Entity.id == entity_id).first()
```

### 3.4 全局异常处理器

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging

logger = logging.getLogger(__name__)

def _build_response(code: int, message: str, data: Any = None, status_code: int = 200) -> JSONResponse:
    """构建统一响应"""
    payload = ApiResponse.failure(code=code, message=message, data=data)
    return JSONResponse(
        status_code=status_code,
        content=payload.model_dump(exclude_none=True),
    )

async def handle_app_exception(request: Request, exc: AppException) -> JSONResponse:
    """处理应用异常"""
    if exc.code >= 50000:
        logger.error(f"系统异常: {exc.message}", exc_info=True)
    else:
        logger.warning(f"业务异常: {exc.message}")
    
    return _build_response(
        code=exc.code,
        message=exc.message,
        data=exc.details or None,
        status_code=exc.status_code,
    )

async def handle_validation_exception(request: Request, exc: RequestValidationError) -> JSONResponse:
    """处理参数验证异常"""
    logger.warning(f"参数验证失败: {exc.errors()}")
    return _build_response(
        code=ErrorCode.VALIDATION_ERROR,
        message="请求参数验证失败",
        data={"errors": exc.errors()},
        status_code=422,
    )

async def handle_unexpected_exception(request: Request, exc: Exception) -> JSONResponse:
    """处理未捕获的异常"""
    logger.exception(f"未捕获异常: {exc}")
    return _build_response(
        code=ErrorCode.SYSTEM_ERROR,
        message="系统异常，请联系管理员",
        status_code=500,
    )

def register_exception_handlers(app: FastAPI) -> None:
    """注册全局异常处理器"""
    app.add_exception_handler(AppException, handle_app_exception)
    app.add_exception_handler(RequestValidationError, handle_validation_exception)
    app.add_exception_handler(Exception, handle_unexpected_exception)
```

---

## 四、前端异常处理规范

### 4.1 API客户端错误类

```typescript
export enum ErrorType {
  AUTHENTICATION = 'AUTHENTICATION',
  AUTHORIZATION = 'AUTHORIZATION',
  NETWORK = 'NETWORK',
  VALIDATION = 'VALIDATION',
  SERVER = 'SERVER',
  UNKNOWN = 'UNKNOWN',
}

export class ApiClientError extends Error {
  code?: number
  status?: number
  responseData?: unknown
  type?: ErrorType
  timestamp: string

  constructor(
    message: string,
    options?: {
      code?: number
      status?: number
      responseData?: unknown
      type?: ErrorType
    }
  ) {
    super(message)
    this.name = 'ApiClientError'
    this.code = options?.code
    this.status = options?.status
    this.responseData = options?.responseData
    this.timestamp = new Date().toISOString()
    this.type = options?.type ?? this.inferErrorType()
  }

  private inferErrorType(): ErrorType {
    if (this.status === 401) return ErrorType.AUTHENTICATION
    if (this.status === 403) return ErrorType.AUTHORIZATION
    if (this.status === 422) return ErrorType.VALIDATION
    if (this.status !== undefined && this.status >= 500) return ErrorType.SERVER
    if (this.code !== undefined) {
      if (this.code >= 50000) return ErrorType.SERVER
      if (this.code >= 40000 && this.code < 50000) return ErrorType.VALIDATION
    }
    return ErrorType.UNKNOWN
  }

  isBusinessError(): boolean {
    if (this.code === undefined) return false
    return this.code >= 40000 && this.code < 50000
  }

  isSystemError(): boolean {
    if (this.code === undefined) {
      return this.status !== undefined && this.status >= 500
    }
    return this.code >= 50000
  }
}
```

### 4.2 API客户端实现

```typescript
interface ApiResponse<T> {
  code: number
  message: string
  data?: T
  timestamp?: string
}

// 检查是否为API响应格式
const isApiResponse = <T>(payload: unknown): payload is ApiResponse<T> => {
  if (!payload || typeof payload !== 'object') return false
  const maybe = payload as Record<string, unknown>
  return typeof maybe.code === 'number' && typeof maybe.message === 'string'
}

// 从响应中提取业务数据
const extractResponseData = <T>(payload: unknown, silent?: boolean): T => {
  if (isApiResponse<T>(payload)) {
    if (payload.code === 0) {
      return payload.data as T
    }
    // 业务错误：HTTP 200 但 code !== 0
    const errorMessage = payload.message || '请求失败'
    if (!silent) {
      // 显示错误提示（使用 toast 或其他提示组件）
      toast.error(errorMessage)
    }
    throw new ApiClientError(errorMessage, {
      code: payload.code,
      responseData: payload.data,
    })
  }
  return payload as T
}

// API客户端
class ApiClient {
  async get<T>(url: string, options?: RequestInit): Promise<{ data: T }> {
    const response = await fetch(url, { ...options, method: 'GET' })
    const json = await response.json()
    return { data: extractResponseData<T>(json) }
  }

  async post<T>(url: string, body?: unknown, options?: RequestInit): Promise<{ data: T }> {
    const response = await fetch(url, {
      ...options,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      body: JSON.stringify(body),
    })
    const json = await response.json()
    return { data: extractResponseData<T>(json) }
  }

  async put<T>(url: string, body?: unknown, options?: RequestInit): Promise<{ data: T }> {
    const response = await fetch(url, {
      ...options,
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      body: JSON.stringify(body),
    })
    const json = await response.json()
    return { data: extractResponseData<T>(json) }
  }

  async delete<T>(url: string, options?: RequestInit): Promise<{ data: T }> {
    const response = await fetch(url, { ...options, method: 'DELETE' })
    const json = await response.json()
    return { data: extractResponseData<T>(json) }
  }
}

export const apiClient = new ApiClient()
```

### 4.3 Service层使用示例

```typescript
class EntityService {
  private baseUrl = '/entities'

  async getEntities(): Promise<Entity[]> {
    const response = await apiClient.get<Entity[]>(this.baseUrl)
    return response.data ?? []
  }

  async getEntity(id: string): Promise<Entity> {
    const response = await apiClient.get<Entity>(`${this.baseUrl}/${id}`)
    return response.data
  }

  async createEntity(entity: Partial<Entity>): Promise<Entity> {
    const response = await apiClient.post<Entity>(this.baseUrl, entity)
    return response.data
  }

  async updateEntity(id: string, entity: Partial<Entity>): Promise<Entity> {
    const response = await apiClient.put<Entity>(`${this.baseUrl}/${id}`, entity)
    return response.data
  }

  async deleteEntity(id: string): Promise<void> {
    await apiClient.delete<void>(`${this.baseUrl}/${id}`)
  }
}

export const entityService = new EntityService()
```

### 4.4 组件中使用示例

```typescript
import { useState } from 'react'
import { entityService } from '@/services/entityService'
import { ApiClientError } from '@/services/apiClient'
import toast from 'react-hot-toast'

function EntityList() {
  const [entities, setEntities] = useState<Entity[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchEntities = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await entityService.getEntities()
      setEntities(data)
    } catch (err) {
      if (err instanceof ApiClientError) {
        // 业务错误已经自动显示 toast，这里只设置表单错误
        setError(err.message)
      } else {
        // 系统错误或其他错误
        toast.error('获取列表失败')
        setError('获取列表失败')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async (entity: Partial<Entity>) => {
    try {
      await entityService.createEntity(entity)
      toast.success('创建成功')
      fetchEntities() // 刷新列表
    } catch (err) {
      // 业务错误已经自动显示 toast，这里可以设置表单错误
      if (err instanceof ApiClientError && err.isBusinessError()) {
        setError(err.message)
      }
    }
  }

  return (
    <div>
      {error && <div className="error">{error}</div>}
      {loading ? (
        <div>加载中...</div>
      ) : (
        <ul>
          {entities.map(entity => (
            <li key={entity.id}>{entity.name}</li>
          ))}
        </ul>
      )}
    </div>
  )
}
```

### 4.5 统一错误处理函数

```typescript
import toast from 'react-hot-toast'

export function handleApiError(
  error: unknown,
  fallbackMessage: string = '操作失败'
): string {
  let errorMessage = fallbackMessage

  if (error instanceof ApiClientError) {
    errorMessage = error.message
    
    // 业务错误：已经自动显示 toast，不重复显示
    if (error.isBusinessError()) {
      return errorMessage
    }
    
    // 系统错误：显示 toast 并上报
    if (error.isSystemError()) {
      console.error('系统错误:', errorMessage, error)
      toast.error(errorMessage)
      // 上报错误到监控系统
      reportError(error)
      return errorMessage
    }
  } else if (error instanceof Error) {
    errorMessage = error.message
  }

  // 其他错误：显示 toast
  console.error('请求错误:', errorMessage, error)
  toast.error(errorMessage)
  return errorMessage
}
```

---

## 五、最佳实践

### 5.1 后端最佳实践

1. **统一使用异常类**：不要直接抛出 `HTTPException`，使用 `BusinessException` 或 `SystemException`
2. **业务异常直接抛出**：Controller 中捕获 `BusinessException` 直接抛出，由全局处理器处理
3. **系统异常记录日志**：系统异常必须记录详细日志（包含 `exc_info=True`）
4. **使用 ApiResponse 包装响应**：所有成功响应使用 `ApiResponse.success()`，错误响应由异常处理器自动生成

```python
# ✅ 正确示例
@router.post("")
async def create_entity(entity_in: EntityCreate):
    try:
        entity = service.create(entity_in)
        return ApiResponse.success(EntityResponse.model_validate(entity))
    except BusinessException:
        raise  # 直接抛出
    except Exception as e:
        raise SystemException("创建失败")

# ❌ 错误示例
@router.post("")
async def create_entity(entity_in: EntityCreate):
    entity = service.create(entity_in)  # 没有异常处理
    return {"id": entity.id}  # 没有使用 ApiResponse
```

### 5.2 前端最佳实践

1. **使用统一的 API 客户端**：所有 API 调用通过 `apiClient`，自动处理响应格式
2. **业务错误不重复处理**：业务错误已自动显示 toast，组件中只需设置表单错误
3. **系统错误自动上报**：系统错误自动上报到监控系统，无需手动处理
4. **使用类型安全**：充分利用 TypeScript 类型系统，避免运行时错误

```typescript
// ✅ 正确示例
try {
  await entityService.createEntity(data)
  toast.success('创建成功')
} catch (err) {
  // 业务错误已自动显示 toast，这里只设置表单错误
  if (err instanceof ApiClientError && err.isBusinessError()) {
    setFormError(err.message)
  }
}

// ❌ 错误示例
try {
  await entityService.createEntity(data)
  toast.success('创建成功')
} catch (err) {
  toast.error('创建失败')  // 业务错误会重复显示 toast
}
```

---

## 六、错误处理流程

### 6.1 后端错误处理流程

```
请求 → Controller → Service → 数据库
                ↓
        发生异常
                ↓
    ┌───────────┴───────────┐
    │                       │
BusinessException    SystemException
    │                       │
    └───────────┬───────────┘
                ↓
        全局异常处理器
                ↓
        统一响应格式
                ↓
           返回前端
```

### 6.2 前端错误处理流程

```
组件调用 → Service → API客户端 → 后端API
                    ↓
              收到响应
                    ↓
         ┌──────────┴──────────┐
         │                     │
    code === 0          code !== 0
         │                     │
   提取 data         抛出 ApiClientError
         │                     │
   返回数据          ┌─────────┴─────────┐
                    │                   │
            业务错误(40000-49999)  系统错误(50000+)
                    │                   │
            自动显示 toast      显示 toast + 上报
                    │                   │
            返回错误信息        返回错误信息
```

---

## 七、总结

遵循本规范可以：

- ✅ 统一前后端API交互格式
- ✅ 清晰区分业务错误和系统错误
- ✅ 减少重复的错误处理代码
- ✅ 提升用户体验（自动错误提示）
- ✅ 便于问题追踪（统一错误码和日志）
- ✅ 提高代码可维护性

**所有新代码必须遵循此规范，旧代码应逐步迁移。**

