# AgentChatPanel 三栏布局重构文档

## 概述

本次重构将 `AgentChatPanel` 从单一对话界面升级为类似 Dify 的三栏布局，支持智能体列表、对话历史管理和实时聊天功能。

## 架构设计

### 三栏布局结构

```
┌─────────────────────────────────────────────────────────────┐
│                      AgentChatPanel                          │
├──────────────┬────────────────┬──────────────────────────────┤
│              │                │                              │
│  AgentSidebar│ Conversation   │     Chat Area                │
│              │ History Panel  │                              │
│  (智能体列表) │  (对话历史)    │   - Header                   │
│              │                │   - Messages                 │
│              │                │   - Input                    │
│              │                │                              │
└──────────────┴────────────────┴──────────────────────────────┘
```

## 新增组件

### 1. AgentSidebar.tsx

**功能**：显示所有可用智能体列表

**Props**：
```typescript
interface AgentSidebarProps {
  agents: AgentConfig[];           // 智能体配置列表
  selectedAgent: AgentConfig | null; // 当前选中的智能体
  onSelectAgent: (agent: AgentConfig) => void; // 选择智能体回调
  isLoading?: boolean;              // 加载状态
}
```

**特性**：
- 显示智能体图标和名称
- 高亮当前选中的智能体
- 支持滚动浏览长列表
- 空状态提示

### 2. ConversationHistoryPanel.tsx

**功能**：显示选中智能体的对话历史

**Props**：
```typescript
interface ConversationHistoryPanelProps {
  agentName: string;                // 智能体名称
  conversations: AgentConversation[]; // 对话列表
  selectedConversationId: string | null; // 当前选中的对话ID
  onSelectConversation: (conversationId: string) => void; // 选择对话回调
  onCreateNewChat: () => void;      // 创建新对话回调
  isLoading?: boolean;              // 加载状态
}
```

**对话数据类型**：
```typescript
export interface AgentConversation {
  id: string;            // 对话ID
  title: string;         // 对话标题
  agentId: string;       // 所属智能体ID
  lastMessageAt: Date;   // 最后消息时间
  messageCount: number;  // 消息数量
}
```

**特性**：
- "Start New chat" 按钮创建新对话
- 显示对话标题、时间和消息数
- 高亮当前对话
- 相对时间显示（使用 date-fns）
- 空状态提示

### 3. 重构后的 AgentChatPanel.tsx

**功能**：主容器组件，协调三栏布局

**Props**：
```typescript
interface AgentChatPanelProps {
  agents: AgentConfig[];      // 所有智能体列表
  isLoadingAgents?: boolean;  // 智能体加载状态
}
```

**核心逻辑**：
1. **智能体选择**：用户从左侧列表选择智能体
2. **对话历史加载**：选中智能体后自动加载其对话历史
3. **对话切换**：
   - 点击历史对话：加载该对话的消息
   - 点击"Start New chat"：清空消息，开始新对话
4. **消息发送**：发送消息后自动创建/更新对话记录

## 工具组件和函数

### ScrollArea Component

位置：`web/src/components/ui/scroll-area.tsx`

基于 `@radix-ui/react-scroll-area` 实现的自定义滚动区域组件。

### cn 工具函数

位置：`web/src/lib/utils.ts`

```typescript
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

用于合并和去重 Tailwind CSS 类名。

## 使用 Hook

### useAgentChat

现有的 Hook 已支持对话管理功能：

```typescript
const {
  messages,              // 当前对话的消息列表
  conversations,         // 智能体的所有对话
  currentConversationId, // 当前对话ID
  isResponding,          // 是否正在响应
  isLoading,             // 是否加载中
  sendMessage,           // 发送消息
  switchConversation,    // 切换对话
  stopResponding,        // 停止响应
} = useAgentChat({ 
  agentConfig: selectedAgent,
  onError: (error) => console.error(error)
});
```

## 使用示例

### 在页面中使用

```tsx
import { AgentChatPanel } from '@/components/agents';

function AgentsPage() {
  const { configs: agentConfigs, isLoading } = useAgentConfigs();

  return (
    <AppLayout>
      <AgentChatPanel
        agents={agentConfigs}
        isLoadingAgents={isLoading}
      />
    </AppLayout>
  );
}
```

## 状态流转

```
1. 用户进入页面
   ↓
2. 显示智能体列表（左侧栏）
   ↓
3. 用户选择智能体
   ↓
4. 加载该智能体的对话历史（中间栏）
   ↓
5. 用户选择历史对话 OR 创建新对话
   ↓
6. 显示对话消息（右侧）
   ↓
7. 用户发送消息
   ↓
8. 实时显示 AI 响应（流式）
```

## 样式规范

### 颜色方案

- **主色调**：橙色系（`orange-100`, `orange-600`）
- **背景**：白色 + 灰色（`gray-50`, `gray-100`）
- **边框**：`gray-200`
- **文本**：`gray-700`, `gray-900`
- **选中状态**：蓝色系（`blue-50`, `blue-600`）

### 响应式设计

- 左侧智能体栏：固定宽度 `w-64`
- 中间对话历史栏：固定宽度 `w-80`
- 右侧聊天区：自适应 `flex-1`

### 图标

使用 `lucide-react` 图标库：
- `Package`: 工作区图标
- `Bot`: 智能体图标
- `MessageSquare`: 对话图标
- `Calendar`: 日期图标
- `Plus`: 添加图标
- `Receipt`: 报销/通用图标

## 遵循的规范

### React 规范
- ✅ 函数组件 + Hooks
- ✅ 使用 `memo` 优化性能
- ✅ TypeScript 类型定义
- ✅ 组件职责单一

### Next.js 规范
- ✅ 'use client' 标记客户端组件
- ✅ 命名导出优先
- ✅ PascalCase 组件命名

### Tailwind CSS 规范
- ✅ 响应式设计
- ✅ 状态变体（hover, focus）
- ✅ 一致的间距系统
- ✅ 使用 cn() 合并类名

### TypeScript 规范
- ✅ 接口定义 Props
- ✅ 明确的类型注解
- ✅ 导出类型定义
- ✅ 避免使用 any

## 后续优化建议

1. **持久化**：将对话历史保存到后端
2. **搜索功能**：在对话历史中搜索
3. **对话管理**：删除、重命名对话
4. **快捷键**：键盘快捷键导航
5. **拖拽排序**：对话历史拖拽排序
6. **分类标签**：为对话添加标签分类
7. **导出功能**：导出对话记录

## 文件清单

### 新增文件
- `web/src/components/agents/AgentSidebar.tsx`
- `web/src/components/agents/ConversationHistoryPanel.tsx`
- `web/src/lib/utils.ts`
- `web/src/components/ui/scroll-area.tsx`

### 修改文件
- `web/src/components/agents/AgentChatPanel.tsx` - 重构为三栏布局
- `web/src/components/agents/index.tsx` - 更新导出
- `web/src/app/agents/explore/page.tsx` - 更新 API 调用

## 测试要点

1. **智能体选择**
   - [ ] 点击智能体能正确切换
   - [ ] 选中状态正确高亮
   - [ ] 加载状态显示正常

2. **对话历史**
   - [ ] 对话列表正确加载
   - [ ] 创建新对话功能正常
   - [ ] 切换对话消息正确加载
   - [ ] 时间显示格式正确

3. **消息发送**
   - [ ] 消息能正常发送
   - [ ] 流式响应正常显示
   - [ ] 停止按钮功能正常
   - [ ] 错误处理正确

4. **UI/UX**
   - [ ] 滚动区域工作正常
   - [ ] 空状态提示友好
   - [ ] 响应式布局适配
   - [ ] 加载状态清晰

## 总结

本次重构成功实现了类似 Dify 的三栏布局界面，大幅提升了用户体验：

✅ **更好的导航**：左侧智能体列表便于快速切换  
✅ **历史管理**：中间对话历史方便查看和管理  
✅ **专注聊天**：右侧聊天区提供沉浸式对话体验  
✅ **代码质量**：遵循项目规范，类型安全，可维护性强  

---

*文档创建时间：2025-10-02*  
*相关 PR/Issue：待补充*

