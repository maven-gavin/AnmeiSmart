# 前端错误处理开发规范

## 概述

本文档定义前端统一的错误处理规范。后端 API 契约见 [API_ERROR_HANDLING_STANDARD.md](./API_ERROR_HANDLING_STANDARD.md)。

## 核心原则

1. **统一错误类型**：使用 `ApiClientError` 作为唯一错误类型
2. **自动错误处理**：业务错误自动 toast，系统错误自动上报
3. **类型安全**：充分利用 TypeScript 类型检查

## 错误分类

| 错误类型 | 错误码范围 | Toast | 控制台 | 上报 | 示例 |
|---------|-----------|-------|--------|------|------|
| 业务错误 | 40000-49999 | ✅ | ❌ | ❌ | 角色名称已存在 |
| 系统错误 | 50000+ | ✅ | ✅ | ✅ | 服务器内部错误 |
| 网络错误 | - | ✅ | ✅ | ✅ | 网络连接失败 |
| 认证错误 | 401 | ✅ | ✅ | ✅ | Token 过期 |

## 导入

```typescript
import { ApiClientError, ErrorType, handleApiError } from '@/service/apiClient'
```

## 使用方式

```typescript
import { handleApiError } from '@/service/apiClient'
import toast from 'react-hot-toast'

try {
  await apiClient.post('/roles', data)
  toast.success('创建成功')
} catch (err) {
  const message = handleApiError(err, '创建失败')
  setFormError(message)
}
```

## 创建自定义错误

```typescript
import { ApiClientError, ErrorType } from '@/service/apiClient'

throw new ApiClientError('角色名称已存在', {
  code: 40001,
  status: 200,
  type: ErrorType.VALIDATION,
})
```

## 最佳实践

1. 业务错误不手动 toast（`apiClient` 已处理）
2. 系统错误不手动 `console.error`（会自动上报）
3. 统一用 `handleApiError` 提取表单/页面错误文案
4. 不要使用已废弃的 `AppError` / `@/service/errors`

## 检查清单

- [ ] 使用 `ApiClientError`
- [ ] 使用 `handleApiError` 处理 catch
- [ ] 业务错误不重复 toast
- [ ] 系统错误不重复打日志
