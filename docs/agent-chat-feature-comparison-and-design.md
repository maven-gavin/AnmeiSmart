# Agent Chat 功能对比与未实现功能设计

## 📊 功能实现状态对比表

| 功能模块 | Dify | 本系统 | 实现状态 | 优先级 |
|---------|------|--------|---------|--------|
| **1. 对话前输入表单** | ✅ | ❌ | 未实现 | 🔴 高 |
| **2. 开场白与建议问题** | ✅ | ✅ | 已实现 | ✅ |
| **3. 语音输入 (STT)** | ✅ | ⚠️ | 部分实现 | 🟡 中 |
| **4. 文件上传** | ✅ | ⚠️ | 部分实现 | 🟡 中 |
| **5. 文字转语音 (TTS)** | ✅ | ❌ | 未实现 | 🟡 中 |
| **6. 引用/引证** | ✅ | ❌ | 未实现 | 🟢 低 |
| **7. 回答后建议问题** | ✅ | ✅ | 已实现 | ✅ |
| **8. 点赞/点踩反馈** | ✅ | ✅ | 已实现 | ✅ |
| **9. 标注回复** | ✅ | ❌ | 未实现 | 🟢 低 |
| **10. 敏感词规避** | ✅ | ❌ | 未实现 | 🟢 低 |
| **11. 更多类似** | ✅ | ❌ | 未实现 | 🟢 低 |
| **12. 对话管理** | ✅ | ✅ | 已实现 | ✅ |
| **13. 流式 Markdown** | ✅ | ✅ | 已实现 | ✅ |
| **14. 停止生成** | ✅ | ✅ | 已实现(增强) | ✅ |

---

## ✅ 已实现功能详情

### 1. 开场白与建议问题
**实现位置**: `web/src/components/agents/EmptyState.tsx`

**核心功能**:
- ✅ 从后端获取应用参数 (`getApplicationParameters`)
- ✅ 显示开场白 (`opening_statement`)
- ✅ 显示建议问题 (`suggested_questions`)
- ✅ 点击建议问题自动发送

**实现代码**:
```typescript
// 获取应用参数
const fetchParameters = async () => {
  const data = await getApplicationParameters(agentConfig.id);
  setParameters(data);
};

// 渲染建议问题
{parameters?.suggested_questions?.map((question, index) => (
  <button
    onClick={() => onSendMessage?.(question)}
    className="rounded-lg border px-4 py-2 hover:bg-orange-50"
  >
    {question}
  </button>
))}
```

---

### 2. 回答后建议问题
**实现位置**: `web/src/components/agents/SuggestedQuestions.tsx`

**核心功能**:
- ✅ 异步加载建议问题
- ✅ 仅在最后一个消息显示
- ✅ 点击自动发送

**API**: `GET /agent/{id}/messages/{messageId}/suggested`

---

### 3. 点赞/点踩反馈
**实现位置**: `web/src/components/agents/MessageFeedback.tsx`

**核心功能**:
- ✅ 点赞/点踩按钮
- ✅ 状态高亮显示
- ✅ 提交到后端
- ✅ 再次点击取消反馈

**API**: `POST /agent/{id}/feedback`

---

### 4. 对话管理
**实现位置**: `web/src/components/agents/ConversationHistoryPanel.tsx`

**核心功能**:
- ✅ 对话历史列表
- ✅ 新建对话
- ✅ 切换对话
- ✅ 重命名对话 (支持)
- ✅ 删除对话

---

### 5. 流式 Markdown 渲染
**实现位置**: `web/src/components/base/StreamMarkdown.tsx`

**核心功能**:
- ✅ 使用 `streamdown` 库
- ✅ 支持数学公式 (katex)
- ✅ 支持代码块、列表、表格等

---

### 6. 停止生成功能
**实现位置**: `web/src/hooks/useAgentChat.ts`

**核心功能** (增强版):
- ✅ 客户端中止 (`AbortController`)
- ✅ 服务端停止 (`POST /agent/{id}/stop`)
- ✅ 双重停止机制

---

### 7. 语音输入 (部分实现)
**实现位置**: `web/src/components/chat/MessageInput.tsx` (在普通聊天中)

**已实现**:
- ✅ 录音功能 (`useRecording` hook)
- ✅ 音频预览
- ✅ 发送语音消息

**未在 Agent Chat 中集成**: Agent Chat 的 `MessageInput` 未包含语音功能

---

### 8. 文件上传 (部分实现)
**实现位置**: `web/src/components/chat/MessageInput.tsx` (在普通聊天中)

**已实现**:
- ✅ 文件选择
- ✅ 文件预览
- ✅ 多文件上传

**未在 Agent Chat 中集成**: Agent Chat 的 `MessageInput` 未包含文件上传

---

## ❌ 未实现功能设计

### 🔴 高优先级

#### 1. 对话前输入表单 (Pre-conversation Inputs)

**产品需求**:
- 用户在开始对话前填写表单
- 支持多种输入类型
- 表单可折叠/展开
- 填写完成后点击"开始聊天"

**技术设计**:

##### 1.1 数据模型
```typescript
// web/src/types/agent-chat.ts
export interface UserInputFormField {
  variable: string;              // 变量名
  label: string;                 // 显示标签
  type: 'text-input' | 'paragraph' | 'number' | 'select' | 'file' | 'file-list';
  required: boolean;             // 是否必填
  max_length?: number;           // 最大长度
  default?: string | number;     // 默认值
  options?: string[];            // select 类型的选项
  hide?: boolean;                // 是否隐藏
  description?: string;          // 字段描述
}

export interface ApplicationParameters {
  opening_statement?: string;
  suggested_questions?: string[];
  user_input_form?: UserInputFormField[];  // 新增
  speech_to_text?: {
    enabled: boolean;
  };
  file_upload?: {
    enabled: boolean;
    allowed_file_types: string[];
    allowed_file_upload_methods: string[];
    number_limits: number;
  };
  text_to_speech?: {
    enabled: boolean;
    voice?: string;
    language?: string;
  };
  // ... 其他配置
}
```

##### 1.2 组件设计
```typescript
// web/src/components/agents/UserInputForm.tsx
'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select } from '@/components/ui/select';
import { ChevronDown, ChevronUp } from 'lucide-react';

interface UserInputFormProps {
  fields: UserInputFormField[];
  onSubmit: (values: Record<string, any>) => void;
  onCancel?: () => void;
}

export function UserInputForm({ fields, onSubmit, onCancel }: UserInputFormProps) {
  const [collapsed, setCollapsed] = useState(false);
  const [values, setValues] = useState<Record<string, any>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});

  // 过滤隐藏字段
  const visibleFields = fields.filter(f => !f.hide);

  // 验证表单
  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};
    
    visibleFields.forEach(field => {
      if (field.required && !values[field.variable]) {
        newErrors[field.variable] = `${field.label} 是必填项`;
      }
      
      if (field.type === 'text-input' && field.max_length) {
        const value = values[field.variable] || '';
        if (value.length > field.max_length) {
          newErrors[field.variable] = `不能超过 ${field.max_length} 个字符`;
        }
      }
    });

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = () => {
    if (validateForm()) {
      onSubmit(values);
    }
  };

  // 渲染字段
  const renderField = (field: UserInputFormField) => {
    switch (field.type) {
      case 'text-input':
        return (
          <Input
            value={values[field.variable] || field.default || ''}
            onChange={(e) => setValues({ ...values, [field.variable]: e.target.value })}
            placeholder={field.description}
            maxLength={field.max_length}
          />
        );
      
      case 'paragraph':
        return (
          <Textarea
            value={values[field.variable] || field.default || ''}
            onChange={(e) => setValues({ ...values, [field.variable]: e.target.value })}
            placeholder={field.description}
            rows={4}
          />
        );
      
      case 'number':
        return (
          <Input
            type="number"
            value={values[field.variable] || field.default || ''}
            onChange={(e) => setValues({ ...values, [field.variable]: Number(e.target.value) })}
            placeholder={field.description}
          />
        );
      
      case 'select':
        return (
          <Select
            value={values[field.variable] || field.default}
            onValueChange={(value) => setValues({ ...values, [field.variable]: value })}
          >
            {field.options?.map((option) => (
              <option key={option} value={option}>{option}</option>
            ))}
          </Select>
        );
      
      // file 和 file-list 类型暂时返回提示
      default:
        return <p className="text-sm text-gray-500">暂不支持此字段类型</p>;
    }
  };

  if (visibleFields.length === 0) return null;

  return (
    <div className="mx-auto max-w-2xl rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
      {/* 表单头部 */}
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">填写信息</h3>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setCollapsed(!collapsed)}
        >
          {collapsed ? <ChevronDown /> : <ChevronUp />}
        </Button>
      </div>

      {/* 表单内容 */}
      {!collapsed && (
        <>
          <div className="space-y-4">
            {visibleFields.map((field) => (
              <div key={field.variable}>
                <label className="mb-1 block text-sm font-medium text-gray-700">
                  {field.label}
                  {field.required && <span className="text-red-500">*</span>}
                </label>
                {renderField(field)}
                {errors[field.variable] && (
                  <p className="mt-1 text-sm text-red-600">{errors[field.variable]}</p>
                )}
              </div>
            ))}
          </div>

          {/* 操作按钮 */}
          <div className="mt-6 flex justify-end space-x-3">
            {onCancel && (
              <Button variant="outline" onClick={onCancel}>
                取消
              </Button>
            )}
            <Button onClick={handleSubmit}>
              开始聊天
            </Button>
          </div>
        </>
      )}

      {/* 已折叠状态 */}
      {collapsed && (
        <Button
          variant="outline"
          size="sm"
          onClick={() => setCollapsed(false)}
          className="w-full"
        >
          编辑信息
        </Button>
      )}
    </div>
  );
}
```

##### 1.3 集成到 EmptyState
```typescript
// web/src/components/agents/EmptyState.tsx 修改
export function EmptyState({ agentConfig, onSendMessage }: EmptyStateProps) {
  const [parameters, setParameters] = useState<ApplicationParameters | null>(null);
  const [showForm, setShowForm] = useState(true);
  const [formValues, setFormValues] = useState<Record<string, any> | null>(null);

  const handleFormSubmit = (values: Record<string, any>) => {
    setFormValues(values);
    setShowForm(false);
    
    // 将表单值存储，后续发送消息时携带
    // 可以通过 context 或状态管理传递
  };

  const hasInputForm = parameters?.user_input_form && parameters.user_input_form.length > 0;
  const allInputsHidden = parameters?.user_input_form?.every(f => f.hide === true);

  return (
    <div className="flex min-h-[60vh] items-center justify-center p-8">
      <div className="max-w-2xl w-full space-y-6">
        {/* 输入表单 */}
        {hasInputForm && !allInputsHidden && showForm && !formValues && (
          <UserInputForm
            fields={parameters.user_input_form}
            onSubmit={handleFormSubmit}
          />
        )}

        {/* 开场白（表单填写后或无表单时显示） */}
        {(!hasInputForm || !showForm || formValues) && (
          <>
            {/* 应用图标 */}
            <div className="flex justify-center">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-orange-100">
                <MessageCircle className="h-8 w-8 text-orange-600" />
              </div>
            </div>

            {/* 开场白 */}
            {parameters?.opening_statement && (
              <div className="rounded-lg bg-white border border-gray-200 p-6">
                <StreamMarkdown
                  content={parameters.opening_statement}
                  className="text-sm text-gray-900"
                />
              </div>
            )}

            {/* 建议问题 */}
            {parameters?.suggested_questions && parameters.suggested_questions.length > 0 && (
              <div>
                <p className="mb-3 text-sm font-medium text-gray-700">💡 您可能想问：</p>
                <div className="grid grid-cols-1 gap-2">
                  {parameters.suggested_questions.map((question, index) => (
                    <button
                      key={index}
                      onClick={() => onSendMessage?.(question)}
                      className="rounded-lg border border-orange-200 bg-orange-50 px-4 py-3 text-left text-sm text-orange-700 transition hover:bg-orange-100"
                    >
                      {question}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
```

##### 1.4 后端 API 支持
后端已实现 `GET /agent/{id}/parameters` 接口，返回包含 `user_input_form` 的配置。

---

### 🟡 中优先级

#### 2. Agent Chat 中的语音输入 (STT)

**设计思路**: 复用已有的 `useRecording` hook

##### 2.1 增强 MessageInput 组件
```typescript
// web/src/components/agents/MessageInput.tsx 增强版
import { Mic, StopCircle } from 'lucide-react';
import { useRecording } from '@/hooks/useRecording';

export function MessageInput({ 
  onSend, 
  disabled, 
  isResponding,
  onStop,
  placeholder = '输入消息...',
  enableVoice = false,  // 新增：是否启用语音
}: MessageInputProps) {
  const [input, setInput] = useState('');
  const [audioPreview, setAudioPreview] = useState<string | null>(null);
  
  const {
    isRecording,
    isPaused,
    startRecording,
    stopRecording,
    cancelRecording
  } = useRecording();

  const handleStopRecording = async () => {
    const audioUrl = await stopRecording();
    if (audioUrl) {
      setAudioPreview(audioUrl);
      // 可选：自动转换为文字
      // const text = await convertSpeechToText(audioUrl);
      // setInput(text);
    }
  };

  return (
    <div className="border-t border-gray-200 bg-white p-4">
      {/* 音频预览 */}
      {audioPreview && (
        <div className="mb-2 flex items-center space-x-2 rounded-lg bg-orange-50 p-3">
          <audio src={audioPreview} controls className="flex-1" />
          <button
            onClick={() => setAudioPreview(null)}
            className="text-gray-500 hover:text-gray-700"
          >
            ✕
          </button>
        </div>
      )}

      <div className="flex items-end space-x-4">
        <div className="flex-1">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled || isRecording}
            rows={1}
            className="w-full resize-none rounded-lg border border-gray-300 px-4 py-2"
          />
        </div>

        {/* 语音按钮 */}
        {enableVoice && !isResponding && (
          <Button
            onClick={isRecording ? handleStopRecording : startRecording}
            variant={isRecording ? 'destructive' : 'outline'}
            size="icon"
          >
            {isRecording ? <StopCircle /> : <Mic />}
          </Button>
        )}

        {/* 发送/停止按钮 */}
        {isResponding ? (
          <Button onClick={onStop} variant="outline">
            <StopCircle className="animate-pulse" />
          </Button>
        ) : (
          <Button onClick={handleSend} disabled={!input.trim() && !audioPreview}>
            <Send />
          </Button>
        )}
      </div>
    </div>
  );
}
```

##### 2.2 集成到 AgentChatPanel
```typescript
<MessageInput
  onSend={chatState.sendMessage}
  disabled={chatState.isResponding}
  isResponding={chatState.isResponding}
  onStop={chatState.stopResponding}
  enableVoice={parameters?.speech_to_text?.enabled}  // 从应用参数获取
  placeholder={`向 ${selectedAgent.appName} 提问...`}
/>
```

---

#### 3. Agent Chat 中的文件上传

**设计思路**: 复用已有的 `useMediaUpload` hook

##### 3.1 增强 MessageInput 组件
```typescript
import { Image, Paperclip } from 'lucide-react';
import { useMediaUpload } from '@/hooks/useMediaUpload';

export function MessageInput({
  // ... 其他 props
  enableFileUpload = false,  // 新增
  fileUploadConfig,          // 新增
}: MessageInputProps) {
  const {
    imagePreview,
    filePreview,
    handleImageUpload,
    handleFileUpload,
    cancelImagePreview,
    cancelFilePreview,
    fileInputRef,
    fileInputForFileRef
  } = useMediaUpload();

  return (
    <div className="border-t border-gray-200 bg-white p-4">
      {/* 文件预览 */}
      {(imagePreview || filePreview) && (
        <div className="mb-2 space-y-2">
          {imagePreview && (
            <div className="relative inline-block">
              <img src={imagePreview} className="h-20 rounded-lg" />
              <button
                onClick={cancelImagePreview}
                className="absolute -right-2 -top-2 rounded-full bg-red-500 p-1 text-white"
              >
                ✕
              </button>
            </div>
          )}
          
          {filePreview && (
            <div className="flex items-center space-x-2 rounded-lg bg-gray-50 p-3">
              <Paperclip className="h-5 w-5" />
              <span className="flex-1 text-sm">{filePreview.name}</span>
              <button onClick={cancelFilePreview}>✕</button>
            </div>
          )}
        </div>
      )}

      <div className="flex items-end space-x-4">
        <div className="flex-1">
          <textarea /* ... */ />
        </div>

        {/* 文件上传按钮 */}
        {enableFileUpload && !isResponding && (
          <div className="flex space-x-2">
            {/* 图片上传 */}
            {fileUploadConfig?.allowed_file_types?.includes('image') && (
              <>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleImageUpload}
                  className="hidden"
                />
                <Button
                  variant="outline"
                  size="icon"
                  onClick={() => fileInputRef.current?.click()}
                >
                  <Image />
                </Button>
              </>
            )}

            {/* 文件上传 */}
            <>
              <input
                ref={fileInputForFileRef}
                type="file"
                accept={fileUploadConfig?.allowed_file_types?.join(',')}
                onChange={handleFileUpload}
                className="hidden"
              />
              <Button
                variant="outline"
                size="icon"
                onClick={() => fileInputForFileRef.current?.click()}
              >
                <Paperclip />
              </Button>
            </>
          </div>
        )}

        {/* 发送按钮 */}
        <Button onClick={handleSend}>
          <Send />
        </Button>
      </div>
    </div>
  );
}
```

---

#### 4. 文字转语音 (TTS)

**设计思路**: 在 AI 消息上添加播放按钮

##### 4.1 创建 TTS 组件
```typescript
// web/src/components/agents/TextToSpeechButton.tsx
'use client';

import { useState, useRef } from 'react';
import { Volume2, VolumeX } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface TextToSpeechButtonProps {
  text: string;
  agentConfigId: string;
  messageId: string;
}

export function TextToSpeechButton({
  text,
  agentConfigId,
  messageId
}: TextToSpeechButtonProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const handlePlay = async () => {
    try {
      setIsLoading(true);
      
      // 调用后端 TTS API
      const response = await fetch(
        `/api/v1/agent/${agentConfigId}/text-to-audio`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text, streaming: false })
        }
      );

      const audioBlob = await response.blob();
      const audioUrl = URL.createObjectURL(audioBlob);

      // 播放音频
      if (audioRef.current) {
        audioRef.current.src = audioUrl;
        audioRef.current.play();
        setIsPlaying(true);
      }
    } catch (error) {
      console.error('TTS 失败:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleStop = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      setIsPlaying(false);
    }
  };

  return (
    <>
      <audio
        ref={audioRef}
        onEnded={() => setIsPlaying(false)}
        onError={() => setIsPlaying(false)}
      />
      
      <Button
        variant="ghost"
        size="sm"
        onClick={isPlaying ? handleStop : handlePlay}
        disabled={isLoading}
        title={isPlaying ? '停止播放' : '播放语音'}
      >
        {isPlaying ? <VolumeX className="h-4 w-4" /> : <Volume2 className="h-4 w-4" />}
      </Button>
    </>
  );
}
```

##### 4.2 集成到 AIMessage
```typescript
// web/src/components/agents/AIMessage.tsx
import { TextToSpeechButton } from './TextToSpeechButton';

export function AIMessage({ message, agentConfigId, ttsEnabled }: AIMessageProps) {
  return (
    <div className="flex items-start space-x-3">
      <div className="flex-1">
        <div className="relative">
          <div className="rounded-lg bg-white border border-gray-200 px-4 py-3">
            <StreamMarkdown content={message.content} />
          </div>

          {/* 操作按钮区域 */}
          {!message.isStreaming && !message.isError && (
            <div className="mt-2 flex items-center space-x-2">
              {/* 反馈按钮 */}
              <MessageFeedback /* ... */ />
              
              {/* TTS 按钮 */}
              {ttsEnabled && (
                <TextToSpeechButton
                  text={message.content}
                  agentConfigId={agentConfigId}
                  messageId={message.id}
                />
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
```

---

### 🟢 低优先级

#### 5. 引用/引证 (Citation)

**设计思路**: 显示知识库检索结果

```typescript
// web/src/components/agents/Citation.tsx
interface CitationProps {
  citations: {
    id: string;
    title: string;
    content: string;
    score?: number;
    source?: string;
  }[];
  showHitInfo?: boolean;
}

export function Citation({ citations, showHitInfo }: CitationProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="mt-2 rounded-lg border border-blue-200 bg-blue-50 p-3">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center justify-between text-sm font-medium text-blue-700"
      >
        <span>📚 引用来源 ({citations.length})</span>
        <ChevronDown className={expanded ? 'rotate-180' : ''} />
      </button>

      {expanded && (
        <div className="mt-3 space-y-2">
          {citations.map((citation, index) => (
            <div key={citation.id} className="rounded border bg-white p-3">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <p className="text-sm font-medium">{citation.title}</p>
                  <p className="mt-1 text-xs text-gray-600">{citation.content}</p>
                  {citation.source && (
                    <p className="mt-1 text-xs text-gray-500">来源: {citation.source}</p>
                  )}
                </div>
                {showHitInfo && citation.score && (
                  <span className="ml-2 rounded bg-blue-100 px-2 py-1 text-xs">
                    {(citation.score * 100).toFixed(0)}%
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

---

## 📈 实现优先级建议

### Phase 1: 核心体验增强 (2-3周)
1. **对话前输入表单** - 支持业务定制化
2. **语音输入集成** - 提升用户体验
3. **文件上传集成** - 支持多模态交互

### Phase 2: 高级功能 (2周)
4. **文字转语音** - 提升可访问性
5. **引用/引证** - 增强可信度

### Phase 3: 辅助功能 (可选)
6. **标注回复** - 支持数据标注
7. **敏感词规避** - 内容安全
8. **更多类似** - 智能推荐

---

## 🔧 技术实现要点

### 1. 状态管理
使用 React Context 或状态管理库传递应用参数配置：

```typescript
// web/src/contexts/AgentConfigContext.tsx
export const AgentConfigContext = createContext<ApplicationParameters | null>(null);

export function AgentConfigProvider({ children, agentConfigId }) {
  const [config, setConfig] = useState<ApplicationParameters | null>(null);

  useEffect(() => {
    getApplicationParameters(agentConfigId).then(setConfig);
  }, [agentConfigId]);

  return (
    <AgentConfigContext.Provider value={config}>
      {children}
    </AgentConfigContext.Provider>
  );
}
```

### 2. 条件渲染
根据应用参数动态显示功能：

```typescript
const config = useContext(AgentConfigContext);

{config?.speech_to_text?.enabled && <VoiceInput />}
{config?.file_upload?.enabled && <FileUpload />}
{config?.text_to_speech?.enabled && <TTSButton />}
```

### 3. 表单值传递
将对话前表单的值传递给后续消息：

```typescript
const [formValues, setFormValues] = useState<Record<string, any> | null>(null);

const sendMessage = (text: string) => {
  const messageWithContext = {
    query: text,
    inputs: formValues,  // 携带表单值
    response_mode: 'streaming'
  };
  
  // 发送到后端
  sendAgentMessage(agentConfigId, messageWithContext);
};
```

---

## 📊 对比总结

| 维度 | Dify | 本系统 |
|-----|------|--------|
| **核心对话** | ✅ 完整 | ✅ 完整 |
| **用户输入** | ✅ 表单 + 语音 + 文件 | ⚠️ 仅文本 (待增强) |
| **AI 输出** | ✅ TTS + 引用 | ⚠️ 仅文本 (待增强) |
| **交互增强** | ✅ 建议问题 + 反馈 | ✅ 建议问题 + 反馈 |
| **内容展示** | ✅ 流式 Markdown | ✅ 流式 Markdown |
| **停止生成** | ✅ 客户端 | ✅ 双重机制 (更强) |
| **对话管理** | ✅ 完整 | ✅ 完整 |

**本系统优势**:
- ✅ 双重停止机制（客户端 + 服务端）
- ✅ 更强的类型安全（TypeScript）
- ✅ 更现代的 UI 组件（shadcn/ui）

**待改进方向**:
- 🔴 补充对话前输入表单
- 🟡 集成语音输入/TTS
- 🟡 集成文件上传
- 🟢 引用/引证等高级功能

---

**完成日期**: 2025-10-03  
**文档版本**: v1.0  
**状态**: 设计完成，待开发实现

