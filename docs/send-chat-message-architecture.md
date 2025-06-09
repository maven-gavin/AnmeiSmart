# 🏗️ 消息发送架构设计

### 📋 核心组件职责

#### 1. **MessageInput.tsx** - 消息输入协调器

```typescript
职责：
✅ 统一管理所有类型的消息输入
✅ 创建消息对象（createTextMessage、createImageMessage、createVoiceMessage、createFileMessage）
✅ 协调各个子组件的交互
✅ 通过 onSendMessage 接口向上传递消息

特点：
- 单一入口：所有消息发送都通过 onSendMessage 接口
- 类型统一：统一的消息创建逻辑
- 状态管理：管理发送状态和错误处理
```

#### 2. **MediaPreview.tsx** - 媒体预览处理器

```typescript
职责：
✅ 专注于媒体文件的预览展示
✅ 处理文件上传到存储服务
✅ 通过回调向父组件传递上传后的URL
✅ 不直接参与消息创建和发送

设计原则：
- 关注点分离：只管预览和上传，不管消息逻辑
- 回调机制：onSendImage、onSendAudio 回调
- 错误边界：独立的错误处理和用户提示
```

#### 3. **useMediaUpload.ts** - 媒体状态管理

```typescript
职责：
✅ 管理图片和语音的预览状态
✅ 处理文件选择和本地预览
✅ 提供状态清理方法

特点：
- 纯状态管理：不涉及业务逻辑
- 可复用：可在多个组件中使用
- 简洁API：清晰的状态和操作方法
```

#### 4. **ChatMessage.tsx** - 消息显示器

```typescript
职责：
✅ 根据消息类型渲染不同的显示效果
✅ 处理消息状态（pending、sent、failed）
✅ 提供消息操作（重试、删除、撤销、标记重点）
✅ 自动处理pending消息的发送

特点：
- 多态显示：支持文本、图片、语音、文件等类型
- 状态驱动：根据消息状态展示不同UI
- 自治处理：自动发送pending消息
```

### 🔄 数据流设计

#### **发送流程**

```
1. 用户输入 → 2. 组件处理 → 3. 消息创建 → 4. 统一发送 → 5. 状态更新 → 6. 显示反馈
```

#### **具体流程示例**

**📝 文本消息：**

```
用户输入文字 → MessageInput → createTextMessage() → onSendMessage() → 父组件保存 → ChatMessage显示
```

**🖼️ 图片消息：**

```
用户选择图片 → useMediaUpload管理状态 → MediaPreview预览 → 
上传到存储 → 回调传递URL → createImageMessage() → onSendMessage() → 
父组件保存 → ChatMessage显示
```

**🎵 语音消息：**

```
用户录音 → useRecording管理录音 → MediaPreview预览 → 
上传到存储 → 回调传递URL → createVoiceMessage() → onSendMessage() → 
父组件保存 → ChatMessage显示
```

### 🎨 设计原则

#### **1. 单一职责原则 (SRP)**

- 每个组件只负责一个明确的功能
- MediaPreview只管预览，不管发送
- MessageInput只管协调，不管具体上传

#### **2. 开闭原则 (OCP)**

- 易于扩展新的消息类型
- 可以添加新的媒体处理方式
- 不影响现有代码结构

#### **3. 依赖倒置 (DIP)**

- 通过接口和回调解耦
- 父组件控制发送逻辑
- 子组件专注于具体实现

#### **4. 一致性原则**

- 统一的消息对象结构
- 一致的错误处理方式
- 统一的UI主题（橙色）

### 📦 文件结构

```
web/src/
├── components/chat/
│   ├── MessageInput.tsx      # 消息输入协调器
│   ├── MediaPreview.tsx      # 媒体预览处理器
│   ├── ChatMessage.tsx       # 消息显示器
│   ├── FileMessage.tsx       # 文件消息显示
│   └── RecordingControls.tsx # 录音控制
├── hooks/
│   ├── useMediaUpload.ts     # 媒体上传状态管理
│   └── useRecording.ts       # 录音状态管理
├── service/
│   ├── fileService.ts        # 文件服务
│   └── chatService.ts        # 聊天服务
├── utils/
│   └── messageUtils.ts       # 消息工具函数
└── types/
    └── chat.ts               # 类型定义
```

### 🎯 架构优势

1. **✅ 高内聚低耦合**：组件职责清晰，依赖关系简单
2. **✅ 易于测试**：每个组件都可以独立测试
3. **✅ 易于扩展**：新增消息类型只需添加对应的创建函数
4. **✅ 用户体验一致**：统一的错误处理和状态提示
5. **✅ 代码复用**：工具函数和状态管理可复用
6. **✅ 类型安全**：完整的 TypeScript 类型支持

这个架构确保了消息发送功能的**可维护性**、**可扩展性**和**用户体验**的完美平衡！🚀
