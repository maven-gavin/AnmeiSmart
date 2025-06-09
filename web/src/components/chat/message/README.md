# 聊天消息组件架构

## 架构设计

重构后的聊天消息组件采用组合模式，提供了更好的扩展性和代码复用：

### 基础组件

- **ChatMessage** - 基础消息组件，负责通用功能：
  - 消息状态管理（pending, failed, sent）
  - 操作按钮（重点标记、重试、撤销、删除）
  - 发送者信息显示
  - 系统消息处理
  - 消息容器布局

### 消息内容组件

所有消息内容组件都实现 `MessageContentProps` 接口：

```typescript
export interface MessageContentProps {
  message: Message;
  searchTerm?: string;
  compact?: boolean;
}
```

#### 专用消息组件

1. **TextMessage** - 文本消息

   - 高亮搜索词
   - 支持多行文本显示
2. **ImageMessage** - 图片消息

   - 图片预览和放大
   - 图片下载功能
   - 错误处理和重载
3. **VoiceMessage** - 语音消息

   - 自定义音频播放器
   - 进度条控制
   - 播放状态管理
4. **VideoMessage** - 视频消息

   - 视频播放控制
   - 全屏功能
   - 下载功能
5. **FileMessage** - 文件消息

   - 文件类型图标
   - 预览功能（支持的格式）
   - 下载功能
   - 兼容多种调用方式

## 使用方式

### 1. 基础使用（自动分发）

```tsx
<ChatMessage 
  message={message} 
  searchTerm="搜索词"
  showSender={true}
  compact={false}
/>
```

### 2. 直接使用特定组件

```tsx
// 文本消息
<TextMessage 
  message={textMessage} 
  searchTerm="keyword" 
  compact={false} 
/>

// 文件消息 - 使用消息数据
<FileMessage 
  message={fileMessage} 
  compact={false} 
/>

// 文件消息 - 直接传递文件信息
<FileMessage 
  message={fileMessage} 
  fileInfo={customFileInfo}
  compact={false} 
/>
```

## 扩展性

### 添加新的消息类型

1. 创建新的消息组件，实现 `MessageContentProps` 接口
2. 在 `ChatMessage.tsx` 的 `renderMessageContent()` 方法中添加新类型的判断逻辑

### 修改现有组件

每个消息类型组件都是独立的，可以单独修改而不影响其他组件。

## 优势

1. **单一职责**：每个组件只负责特定类型的消息渲染
2. **高复用性**：基础组件提供通用功能，避免重复代码
3. **易扩展**：添加新消息类型简单，不影响现有代码
4. **易维护**：组件职责清晰，便于调试和维护
5. **向后兼容**：保持原有API的兼容性
