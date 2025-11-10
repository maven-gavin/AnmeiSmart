# 前端错误处理开发规范

## 概述

本文档定义了项目中统一的错误处理开发规范，所有业务代码必须遵循此规范。

## 核心原则

1. **统一错误类型**：使用 `ApiClientError` 作为唯一的错误类型
2. **自动错误处理**：业务错误自动显示 toast，系统错误自动上报
3. **简化代码**：优先使用 Hook 简化错误处理逻辑
4. **类型安全**：充分利用 TypeScript 类型检查

## 错误分类

| 错误类型 | 错误码范围 | Toast提示 | 控制台日志 | 错误上报 | 示例 |
|---------|-----------|---------|----------|---------|------|
| 业务错误 | 40000-49999 | ✅ 自动显示 | ❌ 不打印 | ❌ 不上报 | 角色名称已存在 |
| 系统错误 | 50000+ | ✅ 显示 | ✅ 打印 | ✅ 上报 | 服务器内部错误 |
| 网络错误 | - | ✅ 显示 | ✅ 打印 | ✅ 上报 | 网络连接失败 |
| 认证错误 | 401 | ✅ 显示 | ✅ 打印 | ✅ 上报 | Token过期 |

## 导入规范

### ✅ 正确导入

```typescript
// 导入错误类型和处理函数
import { ApiClientError, ErrorType, handleApiError } from '@/service/apiClient'

// 导入 Hook（推荐）
import { useApiError, useApiAction } from '@/hooks/useApiError'
```

### ❌ 错误导入（已废弃）

```typescript
// ❌ 不要使用
import { AppError, errorHandler } from '@/service/errors'
```

## 使用方式

### 方式1：使用 `handleApiError`（基础方式）

```typescript
import { handleApiError } from '@/service/apiClient'
import toast from 'react-hot-toast'

try {
  await apiClient.post('/roles', data)
  toast.success('创建成功')
} catch (err) {
  // 业务错误已自动显示 toast，这里只设置表单错误
  const message = handleApiError(err, '创建失败')
  setFormError(message)
}
```

### 方式2：使用 `useApiError` Hook（推荐）

```typescript
import { useApiError } from '@/hooks/useApiError'
import toast from 'react-hot-toast'

function MyComponent() {
  const { handleError, errorMessage } = useApiError()
  
  const handleSubmit = async () => {
    try {
      await apiClient.post('/roles', data)
      toast.success('创建成功')
    } catch (err) {
      handleError(err, '创建失败')
    }
  }
  
  return (
    <div>
      {errorMessage && <p className="text-red-500">{errorMessage}</p>}
      {/* ... */}
    </div>
  )
}
```

### 方式3：使用 `useApiAction` Hook（最简洁）

```typescript
import { useApiAction } from '@/hooks/useApiError'

function MyComponent() {
  const { execute, loading, error } = useApiAction()
  
  const handleCreate = () => {
    execute(
      () => permissionService.createRole(data),
      undefined,
      {
        successMessage: '创建成功',
        onSuccess: () => {
          // 重置表单
          resetForm()
          // 刷新列表
          fetchRoles()
        }
      }
    )
  }
  
  return (
    <button onClick={handleCreate} disabled={loading}>
      {loading ? '创建中...' : '创建角色'}
    </button>
  )
}
```

## 创建自定义错误

### ✅ 正确方式

```typescript
import { ApiClientError, ErrorType } from '@/service/apiClient'

// 创建业务错误
throw new ApiClientError('角色名称已存在', {
  code: 40001,
  status: 200,
  type: ErrorType.VALIDATION,
})

// 创建系统错误
throw new ApiClientError('服务器内部错误', {
  code: 50000,
  status: 500,
  type: ErrorType.SERVER,
})

// 创建认证错误
throw new ApiClientError('用户未登录', {
  status: 401,
  type: ErrorType.AUTHENTICATION,
})
```

### ❌ 错误方式

```typescript
// ❌ 不要使用旧的 AppError
throw new AppError(ErrorType.AUTHENTICATION, 401, '用户未登录')

// ❌ 不要手动显示 toast（业务错误会自动显示）
toast.error('角色名称已存在')

// ❌ 不要手动打印日志（系统错误会自动打印）
console.error('系统错误', error)
```

## 错误处理选项

`handleApiError` 和 Hook 支持以下选项：

```typescript
handleApiError(error, '操作失败', {
  // 是否在控制台打印错误（默认：仅系统错误打印）
  logError: false,
  
  // 是否显示 toast（默认：业务错误不显示，系统错误显示）
  showToast: true,
  
  // 是否上报错误（默认：仅系统错误上报）
  reportError: false,
  
  // 错误上报上下文
  reportContext: {
    userId: 'user123',
    path: '/roles',
    method: 'POST',
  },
  
  // 自定义错误消息提取
  getMessage: (err) => {
    if (err instanceof ApiClientError) {
      return err.message
    }
    return '自定义错误消息'
  }
})
```

## 错误类型判断

```typescript
import { ApiClientError, ErrorType } from '@/service/apiClient'

if (error instanceof ApiClientError) {
  // 判断是否是业务错误
  if (error.isBusinessError()) {
    // 业务错误处理
  }
  
  // 判断是否是系统错误
  if (error.isSystemError()) {
    // 系统错误处理
  }
  
  // 获取错误类型
  if (error.type === ErrorType.AUTHENTICATION) {
    // 认证错误处理
  }
}
```

## 最佳实践

### ✅ 推荐做法

1. **优先使用 Hook**：`useApiAction` 或 `useApiError`
2. **业务错误不处理**：业务错误已自动显示 toast，只需设置表单错误
3. **系统错误自动上报**：系统错误会自动上报，无需手动处理
4. **统一错误消息**：使用 `handleApiError` 统一提取错误消息

### ❌ 避免做法

1. **不要手动显示 toast**：业务错误会自动显示
2. **不要手动打印日志**：系统错误会自动打印
3. **不要使用旧的错误类型**：统一使用 `ApiClientError`
4. **不要重复处理错误**：避免在多个地方处理同一个错误

## 迁移检查清单

在编写新代码或重构旧代码时，确保：

- [ ] 使用 `ApiClientError` 而不是 `AppError`
- [ ] 使用 `handleApiError` 或 Hook 处理错误
- [ ] 业务错误不手动显示 toast
- [ ] 系统错误不手动打印日志
- [ ] 错误上报上下文自动包含用户信息（使用 Hook 时）

## 示例代码

### 完整的组件示例

```typescript
'use client'

import { useState } from 'react'
import { useApiAction } from '@/hooks/useApiError'
import { permissionService } from '@/service/permissionService'

export function CreateRoleForm() {
  const [roleName, setRoleName] = useState('')
  const { execute, loading, error } = useApiAction()
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    execute(
      () => permissionService.createRole({ name: roleName }),
      undefined,
      {
        successMessage: '角色创建成功',
        onSuccess: () => {
          setRoleName('')
          // 刷新列表等操作
        }
      }
    )
  }
  
  return (
    <form onSubmit={handleSubmit}>
      <input
        value={roleName}
        onChange={(e) => setRoleName(e.target.value)}
        placeholder="角色名称"
      />
      {error && <p className="text-red-500">{error}</p>}
      <button type="submit" disabled={loading}>
        {loading ? '创建中...' : '创建角色'}
      </button>
    </form>
  )
}
```

## 总结

遵循此规范可以：
- ✅ 统一错误处理逻辑
- ✅ 减少重复代码
- ✅ 提升用户体验
- ✅ 便于问题追踪
- ✅ 提高代码可维护性

**所有新代码必须遵循此规范，旧代码应逐步迁移。**

