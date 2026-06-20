# 错误处理规范

前后端 API 交互的统一错误处理约定。实现细节见代码，本文仅保留契约与用法要点。

## API 契约

所有响应使用 `{ code, message, data?, timestamp? }` 格式，`code === 0` 表示成功。

| 错误码范围 | 类型 | HTTP 状态码（典型） |
|-----------|------|-------------------|
| `0` | 成功 | 200 |
| `40000–49999` | 业务错误（可预期） | 200 / 404 等 |
| `50000+` | 系统错误（意外） | 500 |

完整错误码见 `api/app/core/api/errors.py`。

## 后端

**模块**：`app.core.api`（`ApiResponse`、`ErrorCode`、`BusinessException`、`SystemException`）

**Controller 模式**：

```python
from app.core.api import ApiResponse, BusinessException, SystemException, ErrorCode

@router.post("", response_model=ApiResponse[EntityResponse])
async def create_entity(...):
    try:
        entity = service.create(...)
        return ApiResponse.success(EntityResponse.model_validate(entity), message="创建成功")
    except BusinessException:
        raise
    except Exception as e:
        logger.error("创建失败", exc_info=True)
        raise SystemException("创建失败", code=ErrorCode.SYSTEM_ERROR)
```

**Service 层**：业务校验失败直接 `raise BusinessException(...)`，不抛 `HTTPException`。

**全局处理器**：已在应用启动时注册（`register_exception_handlers`），Controller 无需手动构造错误响应。

参考：`api/app/core/api/`、`api/app/identity_access/controllers/roles.py`

## 前端

**模块**：`@/service/apiClient`（`apiClient`、`ApiClientError`、`ErrorType`、`handleApiError`）

| 错误类型 | 错误码 | Toast | 上报 |
|---------|--------|-------|------|
| 业务错误 | 40000–49999 | 自动 | 否 |
| 系统错误 | 50000+ | 自动 | 是 |
| 认证/网络 | 401 等 | 自动 | 是 |

```typescript
import { apiClient, handleApiError } from '@/service/apiClient'

try {
  await apiClient.post('/roles', data)
  toast.success('创建成功')
} catch (err) {
  setFormError(handleApiError(err, '创建失败'))
}
```

- 业务错误：`apiClient` 已 toast，组件内只设置表单/页面错误文案
- 不要用已废弃的 `AppError` / `@/service/errors`

参考：`web/src/service/apiClient.ts`、`web/src/service/permissionService.ts`
