# 服务层重构总结

## 重构目标
- 代码整洁，消除冗余
- 错误集中处理
- 模块化设计
- 遵循 Next.js 和 React 最佳实践

## 重构内容

### 1. 新增模块

#### `errors.ts` - 统一错误处理
- 定义标准化错误类型 (`ErrorType`)
- 实现统一错误类 (`AppError`)
- 提供错误处理工具函数 (`errorHandler`)
- 集中错误消息管理

#### `jwt.ts` - JWT 工具模块
- JWT 令牌解析和验证
- 令牌过期检查
- 令牌格式验证
- 独立的工具函数，避免循环依赖

#### `tokenManager.ts` - 令牌管理器
- 统一令牌存储和获取
- 自动令牌刷新机制
- 安全的本地存储操作
- 防止并发刷新

### 2. 重构现有模块

#### `authService.ts` - 身份验证服务
**改进前问题：**
- 功能过于庞大，包含太多职责
- 重复的 API 请求逻辑
- 错误处理分散
- 存在潜在的循环依赖

**改进后：**
- 专注于身份验证逻辑
- 使用令牌管理器处理令牌相关操作
- 统一错误处理
- 清晰的单一职责原则
- 增加角色权限检查方法

#### `apiClient.ts` - API 客户端
**改进前问题：**
- 重复的令牌处理逻辑
- 错误处理分散在多个地方
- 类型定义不够清晰
- 冗余的响应处理逻辑

**改进后：**
- 模块化设计，分离关注点
- 统一的请求拦截器
- 集中的错误处理
- 自动令牌刷新和重试机制
- 清晰的类型定义
- 支持文件上传和超时控制

## 架构改进

### 依赖关系优化
```
错误处理层 (errors.ts)
    ↑
JWT工具层 (jwt.ts)
    ↑  
令牌管理层 (tokenManager.ts)
    ↑
服务层 (authService.ts, apiClient.ts)
```

### 核心改进点

1. **单一职责原则**：每个模块专注于特定功能
2. **依赖注入**：通过模块化设计减少耦合
3. **错误集中处理**：统一的错误类型和处理机制
4. **类型安全**：使用 TypeScript 严格类型检查
5. **可测试性**：清晰的模块边界便于单元测试

### 性能优化

1. **令牌管理**：
   - 防止并发刷新
   - 缓存有效令牌
   - 自动过期检查

2. **请求优化**：
   - 智能重试机制
   - 超时控制
   - 错误恢复

3. **内存管理**：
   - 安全的存储操作
   - 及时清理资源

## 使用示例

### API 客户端使用
```typescript
// GET 请求
const response = await apiClient.get<UserData>('/users/me');

// POST 请求
const result = await apiClient.post<CreateResult>('/users', userData);

// 文件上传
const uploadResult = await apiClient.upload<UploadResult>('/files', formData);
```

### 身份验证服务使用
```typescript
// 登录
const { user, token } = await authService.login(credentials);

// 角色检查
if (authService.hasRole('admin')) {
  // 管理员操作
}

// 角色切换
await authService.switchRole('doctor');
```

## 错误处理

### 统一错误类型
- `AUTHENTICATION`: 认证错误
- `AUTHORIZATION`: 授权错误
- `NETWORK`: 网络错误
- `VALIDATION`: 验证错误
- `SERVER`: 服务器错误
- `UNKNOWN`: 未知错误

### 错误处理示例
```typescript
try {
  const data = await apiClient.get('/api/data');
} catch (error) {
  if (error instanceof AppError) {
    switch (error.type) {
      case ErrorType.AUTHENTICATION:
        // 处理认证错误
        break;
      case ErrorType.NETWORK:
        // 处理网络错误
        break;
    }
  }
}
```

## 后续优化建议

1. **缓存机制**：实现智能缓存策略
2. **离线支持**：添加离线数据同步
3. **监控和日志**：集成错误监控和日志系统
4. **单元测试**：为新模块编写完整的单元测试 