# UI优化指南

## 概述

本文档提供了全站UI优化的完整指南，基于任务管理页面的成功优化经验。通过遵循本指南，可以确保全站UI风格统一、视觉一致。

## 快速开始

### 1. 查看设计系统规范

在开始优化任何页面之前，请先阅读：
- [UI设计系统规范](../.cursor/rules/ui/ui-design-system.mdc) - 完整的样式规范
- [提示词模板](./ui-optimization-prompt-template.md) - 标准优化提示词

### 2. 使用标准提示词

复制标准提示词模板，替换页面路径，发送给AI助手：

```
请根据全站UI设计系统规范（@.cursor/rules/ui/ui-design-system.mdc），优化 @web/src/app/[页面路径] 页面UI...
```

## 核心规范要点

### 颜色系统

| 用途 | 颜色值 | Tailwind类名 |
|------|--------|-------------|
| 主色调 | #FFA500 | `bg-brand-primary` / `am-btn-primary` |
| 主色悬停 | #FF8C00 | `hover:bg-brand-primaryHover` / `am-btn-primary` |
| 主色浅色 | #FFF5E6 | `bg-brand-soft` |
| 背景色 | #FFFFFF | `bg-white` |
| 筛选区域 | #F9FAFB | `bg-gray-50` |

### 字体规范

**无衬线字体栈（推荐做法）**：
- 已在 `web/src/app/globals.css` 的 `body` 全局设置字体，页面/组件**默认继承**，无需再写 `style={{ fontFamily: ... }}`。

**等宽字体**（代码、ID等）：
- 使用全局类：`am-mono`

### 组件样式速查

#### 主要按钮
```tsx
<Button className="am-btn-primary">
  按钮文字
</Button>
```

#### 次要按钮
```tsx
<Button className="am-btn-outline">
  按钮文字
</Button>
```

#### 输入框
```tsx
<Input 
  className="am-field"
/>
```

#### 卡片
```tsx
<Card className="am-card">
  {/* 内容 */}
</Card>
```

#### 搜索筛选区域
```tsx
<div className="am-filter-bar">
  {/* 筛选内容 */}
</div>
```

#### 页面容器（建议统一）
```tsx
<div className="am-page">
  <div className="am-container">{/* 页面内容 */}</div>
</div>
```

## 优化检查清单

优化完成后，请对照以下清单检查：

### 基础样式
- [ ] 页面背景为白色 `bg-white`
- [ ] 所有文本使用无衬线字体
- [ ] 主色调使用 `#FFA500`
- [ ] 按钮样式符合规范

### 表单元素
- [ ] 输入框焦点边框为橙色（使用 `am-field` 或 `focus:border-brand-primary`）
- [ ] 输入框焦点环为橙色（使用 `am-field` 或 `focus:ring-brand-primary/20`）
- [ ] 下拉框焦点样式正确
- [ ] 文本域焦点样式正确

### 布局与间距
- [ ] 容器使用 `container mx-auto px-4 py-6`
- [ ] 卡片间距合理（移动端 `space-y-3`，桌面端 `gap-4`）
- [ ] 元素间距符合规范（`gap-2` / `gap-4` / `gap-6`）

### 响应式设计
- [ ] 移动端和桌面端布局正确
- [ ] 使用 `md:` 断点进行响应式切换
- [ ] 移动端使用卡片布局，桌面端使用表格布局（如适用）

### 交互效果
- [ ] 按钮悬停效果正确
- [ ] 卡片悬停阴影效果 `hover:shadow-md`
- [ ] 加载状态样式统一
- [ ] 空状态样式统一

## 常见问题与解决方案

### Q1: AI忘记了字体规范怎么办？

**解决方案**：在提示词中明确要求：
```
请确保所有文本都应用了无衬线字体，参考 @.cursor/rules/ui/ui-design-system.mdc 中的字体规范部分。
```

### Q2: 按钮颜色不一致？

**解决方案**：明确指出按钮类型：
```
请检查所有按钮是否符合规范：
- 主要操作按钮应使用：am-btn-primary（或 bg-brand-primary hover:bg-brand-primaryHover）
- 次要操作按钮应使用：am-btn-outline
```

### Q3: 输入框焦点样式缺失？

**解决方案**：明确要求焦点样式：
```
请确保所有输入框、下拉框、文本域都应用了焦点样式：
am-field（或 focus:border-brand-primary focus:ring-brand-primary/20）
```

### Q4: 间距不规范？

**解决方案**：引用规范中的间距部分：
```
请参考 @.cursor/rules/ui/ui-design-system.mdc 中的"间距与布局"部分，确保间距符合规范。
```

## 优化流程

### 步骤1：准备
1. 确定要优化的页面
2. 查看当前页面存在的问题
3. 准备标准提示词（参考 [提示词模板](./ui-optimization-prompt-template.md)）

### 步骤2：执行
1. 使用标准提示词模板
2. 引用规范文件 `@.cursor/rules/ui/ui-design-system.mdc`
3. 让AI执行优化

### 步骤3：检查
1. 对照检查清单逐项检查
2. 测试响应式布局（移动端/桌面端）
3. 验证交互效果（悬停、焦点等）

### 步骤4：调整
1. 如有不符合规范的地方，使用提醒机制
2. 继续优化直到完全符合规范
3. 记录遇到的问题和解决方案

## 页面优化优先级建议

建议按以下顺序优化页面：

1. **高频使用页面**（如聊天、任务管理）
2. **核心功能页面**（如用户管理、设置）
3. **次要功能页面**（如统计、报表）

## 维护与更新

### 规范更新
如果发现新的样式需求或需要调整规范：
1. 更新 `.cursor/rules/ui/ui-design-system.mdc`
2. 更新本文档
3. 通知团队规范变更

### 问题反馈
如果发现规范不清晰或有问题：
1. 记录问题
2. 提出改进建议
3. 更新规范文档

## 参考资源

- [UI设计系统规范](../.cursor/rules/ui/ui-design-system.mdc) - 完整规范文档
- [提示词模板](./ui-optimization-prompt-template.md) - 标准优化提示词
- [任务管理页面](../web/src/app/tasks/page.tsx) - 参考实现示例

## 总结

通过遵循本指南和设计系统规范，可以确保：
- ✅ 全站UI风格统一
- ✅ 视觉体验一致
- ✅ 开发效率提升
- ✅ 维护成本降低

记住：**始终引用规范文件，确保AI能读取最新规范！**

