# Agent 文件上传功能实现文档

## 📋 概述

成功实现了Agent系统的文件上传功能，使用户可以在Agent对话前通过表单上传文件到Dify服务器，并将文件作为输入参数传递给Agent。

## 🎯 实现目标

1. ✅ 创建 Agent 文件上传服务
2. ✅ 扩展对话服务支持 inputs 参数
3. ✅ 修改 useAgentChat Hook 支持表单数据
4. ✅ 集成文件上传到用户输入表单
5. ✅ 更新类型定义

## 📁 文件变更列表

### 1. 新增文件

#### `web/src/service/agentFileService.ts`
- **功能**: Agent 文件上传服务
- **主要方法**:
  - `uploadAgentFile(agentConfigId, file)`: 上传单个文件到Dify
  - `uploadAgentFiles(agentConfigId, files)`: 批量上传多个文件到Dify
- **返回值**: Dify的文件ID（upload_file_id）

### 2. 修改文件

#### `web/src/service/agentChatService.ts`
- **变更**: `sendAgentMessage` 函数新增 `inputs` 参数
- **用途**: 支持将表单数据（包括文件ID）传递给Dify

#### `web/src/hooks/useAgentChat.ts`
- **变更**: `sendMessage` 函数新增 `inputs` 参数
- **用途**: 从UI层接收表单数据并传递给服务层

#### `web/src/components/agents/UserInputForm.tsx`
- **变更**:
  1. 新增 `agentConfigId` 属性（必需）
  2. 新增 `uploading` 状态管理
  3. `handleSubmit` 改为异步函数
  4. 实现文件上传逻辑：
     - 单文件字段: 上传并替换为Dify文件ID
     - 多文件字段: 批量上传并替换为Dify文件ID数组
  5. 提交按钮显示上传进度

#### `web/src/components/agents/EmptyState.tsx`
- **变更**: 调用 `UserInputForm` 时传入 `agentConfigId` 属性

#### `web/src/types/agent-chat.ts`
- **变更**: 新增 `FileUploadResult` 接口定义

## 🔄 完整工作流程

```
用户填写表单并选择文件
         ↓
点击"开始聊天"按钮
         ↓
UserInputForm.handleSubmit()
  ├─ 验证表单数据
  ├─ 检测文件字段
  ├─ 调用 uploadAgentFile(s) 上传到Dify
  └─ 获取 Dify 文件ID
         ↓
调用 onSubmit(finalValues)
  - finalValues 包含文件ID而非File对象
         ↓
EmptyState.handleFormSubmit(formData)
         ↓
调用 onSendMessage(message, formData)
         ↓
useAgentChat.sendMessage(text, inputs)
         ↓
agentChatService.sendAgentMessage(
  agentConfigId,
  conversationId,
  message,
  callbacks,
  inputs  // ← 包含文件ID
)
         ↓
后端接收 inputs 并转发给Dify
         ↓
Dify 使用文件ID处理对话
```

## 💡 使用示例

### 1. 定义表单字段（Dify配置）

```json
{
  "user_input_form": [
    {
      "variable": "document",
      "label": "上传文档",
      "type": "file",
      "required": true,
      "description": "支持 PDF、Word、TXT 文件"
    },
    {
      "variable": "images",
      "label": "相关图片",
      "type": "file-list",
      "required": false,
      "description": "最多上传5张图片"
    }
  ]
}
```

### 2. 用户操作流程

1. 用户在表单中选择文件
2. 文件显示在预览区域
3. 点击"开始聊天"按钮
4. 按钮显示"上传中..."并禁用
5. 文件上传到Dify服务器
6. 获取Dify文件ID
7. 开始对话，文件ID通过 `inputs` 参数传递

### 3. 数据传递格式

```typescript
// 前端表单值（提交前）
{
  document: File,           // File对象
  images: [File, File]      // File数组
}

// 上传后的最终值（传给Dify）
{
  document: "upload_file_123",              // Dify文件ID
  images: ["upload_file_456", "upload_file_789"]  // Dify文件ID数组
}
```

## 🔑 关键特性

### 1. 文件类型支持
- **单文件** (`type: 'file'`): 上传一个文件
- **多文件** (`type: 'file-list'`): 上传多个文件

### 2. 上传体验
- ✅ 上传进度提示（按钮显示"上传中..."）
- ✅ 按钮禁用防止重复提交
- ✅ 错误提示（上传失败时显示toast）
- ✅ 文件预览和删除功能

### 3. 错误处理
```typescript
try {
  // 上传文件
  const uploadResult = await uploadAgentFile(agentConfigId, file);
} catch (error) {
  toast.error('文件上传失败，请重试');
  // 不继续提交表单
}
```

### 4. 并行上传
多文件上传使用 `Promise.all()` 实现并行上传，提高效率：

```typescript
const uploadResults = await uploadAgentFiles(agentConfigId, files);
// 所有文件同时上传
```

## 🎨 UI 改进

### 按钮状态
```tsx
<Button
  onClick={handleSubmit}
  disabled={uploading}
  className="bg-orange-500 hover:bg-orange-600"
>
  {uploading ? (
    <>
      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
      上传中...
    </>
  ) : (
    '开始聊天'
  )}
</Button>
```

## 🔧 后端对接

### API 端点
- **文件上传**: `POST /api/v1/agent/{agent_config_id}/upload`
- **对话接口**: `POST /api/v1/agent/{agent_config_id}/chat`

### 请求格式

#### 文件上传
```http
POST /api/v1/agent/{agent_config_id}/upload
Content-Type: multipart/form-data

file: <binary>
```

#### 对话请求（带inputs）
```json
{
  "message": "开始对话",
  "conversation_id": "conv_123",
  "inputs": {
    "document": "upload_file_123",
    "images": ["upload_file_456", "upload_file_789"]
  },
  "response_mode": "streaming"
}
```

## ✅ 测试要点

### 功能测试
1. ✅ 单文件上传并提交表单
2. ✅ 多文件上传并提交表单
3. ✅ 文件上传失败时的错误处理
4. ✅ 上传中按钮禁用状态
5. ✅ 文件预览和删除功能
6. ✅ 表单验证（必填文件字段）

### 集成测试
1. ✅ 完整流程：选择文件 → 上传 → 对话
2. ✅ inputs参数正确传递到后端
3. ✅ Dify能正确接收和处理文件

## 📝 注意事项

### 1. Agent配置ID
- `UserInputForm` 现在需要 `agentConfigId` 属性
- 所有使用该组件的地方都需要传入该属性

### 2. 文件大小限制
- 默认最大文件大小: 10MB
- 可在 `UserInputForm.tsx` 中调整 `maxSize` 变量

### 3. 文件类型验证
- 由 Dify 服务器端处理
- 前端可通过 `accept` 属性限制选择

### 4. 错误处理
- 上传失败会显示toast提示
- 上传失败不会提交表单
- 用户可以重新尝试上传

## 🚀 未来优化方向

### 优先级1（建议）
- [ ] 添加上传进度条显示
- [ ] 支持文件大小和类型的前端验证
- [ ] 添加文件上传取消功能

### 优先级2（可选）
- [ ] 支持拖拽上传
- [ ] 支持文件缩略图预览（图片）
- [ ] 批量文件选择优化

### 优先级3（优化）
- [ ] 上传失败后的重试机制
- [ ] 文件上传队列管理
- [ ] 上传统计和日志

## 📚 相关文档

- [Agent对话API指南](./agent-chat-api-guide.md)
- [文件上传功能](./file-upload-readme.md)

## 🎉 总结

成功实现了Agent系统的完整文件上传功能，包括：

1. **前端服务层**: 创建了专用的文件上传服务
2. **状态管理**: 扩展了 useAgentChat Hook
3. **UI集成**: 在用户输入表单中集成文件上传
4. **类型安全**: 完善的TypeScript类型定义
5. **用户体验**: 上传进度提示和错误处理

所有代码遵循项目规范，保持整洁一致，没有linter错误。

