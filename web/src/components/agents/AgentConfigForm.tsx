'use client';

import type { ReactNode } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Checkbox } from '@/components/ui/checkbox';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { DialogFooter } from '@/components/ui/dialog';
import {
  LLM_PROVIDER_PRESETS,
  type AgentCapabilitiesForm,
  type LlmProviderId,
} from '@/lib/llmProviderPresets';

interface FormSectionProps {
  title: string;
  description?: string;
  children: ReactNode;
}

function FormSection({ title, description, children }: FormSectionProps) {
  return (
    <section className="rounded-lg border border-gray-200 bg-gray-50/60 p-5">
      <div className="mb-4">
        <h3 className="text-sm font-semibold text-gray-900">{title}</h3>
        {description && <p className="mt-1 text-xs text-gray-500">{description}</p>}
      </div>
      {children}
    </section>
  );
}

export interface AgentConfigFormValues {
  environment: string;
  appId: string;
  appName: string;
  agentType: string;
  apiKey: string;
  baseUrl: string;
  description: string;
  timeoutSeconds: number;
  maxRetries: number;
  enabled: boolean;
  llmProvider: LlmProviderId;
  capabilities: AgentCapabilitiesForm;
}

export interface AgentConfigFormProps {
  mode: 'create' | 'edit';
  idPrefix: string;
  formLoading: boolean;
  formError: string | null;
  values: AgentConfigFormValues;
  onEnvironmentChange: (v: string) => void;
  onAppIdChange: (v: string) => void;
  onAppNameChange: (v: string) => void;
  onAgentTypeChange: (v: string) => void;
  onApiKeyChange: (v: string) => void;
  onBaseUrlChange: (v: string) => void;
  onDescriptionChange: (v: string) => void;
  onTimeoutSecondsChange: (v: number) => void;
  onMaxRetriesChange: (v: number) => void;
  onEnabledChange: (v: boolean) => void;
  onProviderChange: (id: LlmProviderId) => void;
  onCapabilitiesChange: (caps: AgentCapabilitiesForm) => void;
  onSubmit: (e: React.FormEvent) => void;
  onCancel: () => void;
}

export function AgentConfigForm({
  mode,
  idPrefix,
  formLoading,
  formError,
  values,
  onEnvironmentChange,
  onAppIdChange,
  onAppNameChange,
  onAgentTypeChange,
  onApiKeyChange,
  onBaseUrlChange,
  onDescriptionChange,
  onTimeoutSecondsChange,
  onMaxRetriesChange,
  onEnabledChange,
  onProviderChange,
  onCapabilitiesChange,
  onSubmit,
  onCancel,
}: AgentConfigFormProps) {
  const {
    environment,
    appId,
    appName,
    agentType,
    apiKey,
    baseUrl,
    description,
    timeoutSeconds,
    maxRetries,
    enabled,
    llmProvider,
    capabilities,
  } = values;

  const preset = LLM_PROVIDER_PRESETS.find((p) => p.id === llmProvider);

  const patchCaps = (partial: Partial<AgentCapabilitiesForm>) => {
    onCapabilitiesChange({ ...capabilities, ...partial });
  };

  return (
    <form onSubmit={onSubmit} className="flex min-h-0 flex-1 flex-col">
      <div className="min-h-0 flex-1 space-y-5 overflow-y-auto pr-1">
        {formError && (
          <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
            {formError}
          </div>
        )}

        <FormSection title="基本信息" description="标识 Agent 的应用与环境">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
            <div>
              <Label htmlFor={`${idPrefix}-environment`} className="mb-2 block text-sm font-medium text-gray-700">
                环境 *
              </Label>
              <Select value={environment} onValueChange={onEnvironmentChange} disabled={formLoading}>
                <SelectTrigger id={`${idPrefix}-environment`} className="am-field w-full">
                  <SelectValue placeholder="选择环境" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="dev">开发环境</SelectItem>
                  <SelectItem value="test">测试环境</SelectItem>
                  <SelectItem value="prod">生产环境</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor={`${idPrefix}-appId`} className="mb-2 block text-sm font-medium text-gray-700">
                应用 ID *
              </Label>
              <Input
                id={`${idPrefix}-appId`}
                className="am-field am-mono"
                value={appId}
                onChange={(e) => onAppIdChange(e.target.value)}
                disabled={formLoading}
                placeholder="例如 AGENT_CHAT"
              />
            </div>

            <div>
              <Label htmlFor={`${idPrefix}-appName`} className="mb-2 block text-sm font-medium text-gray-700">
                应用名称 *
              </Label>
              <Input
                id={`${idPrefix}-appName`}
                className="am-field"
                value={appName}
                onChange={(e) => onAppNameChange(e.target.value)}
                disabled={formLoading}
                placeholder="例如 通用聊天"
              />
            </div>

            <div>
              <Label htmlFor={`${idPrefix}-agentType`} className="mb-2 block text-sm font-medium text-gray-700">
                应用类型
              </Label>
              <Select value={agentType} onValueChange={onAgentTypeChange} disabled={formLoading}>
                <SelectTrigger id={`${idPrefix}-agentType`} className="am-field w-full">
                  <SelectValue placeholder="选择类型" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="chat">对话型</SelectItem>
                  <SelectItem value="agent">智能体</SelectItem>
                  <SelectItem value="workflow">工作流</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-end md:col-span-2 lg:col-span-2">
              <div className="flex w-full items-center justify-between rounded-lg border border-gray-200 bg-white px-4 py-3">
                <div>
                  <Label htmlFor={`${idPrefix}-enabled`} className="text-sm font-medium text-gray-700">
                    启用配置
                  </Label>
                  <p className="text-xs text-gray-500">关闭后 Agent 不可用，且无法删除</p>
                </div>
                <Switch
                  id={`${idPrefix}-enabled`}
                  checked={enabled}
                  onCheckedChange={onEnabledChange}
                  disabled={formLoading}
                />
              </div>
            </div>
          </div>

          <div className="mt-4">
            <Label htmlFor={`${idPrefix}-description`} className="mb-2 block text-sm font-medium text-gray-700">
              描述
            </Label>
            <Textarea
              id={`${idPrefix}-description`}
              className="am-field"
              value={description}
              onChange={(e) => onDescriptionChange(e.target.value)}
              disabled={formLoading}
              rows={2}
              placeholder="可选：说明该 Agent 的用途"
            />
          </div>
        </FormSection>

        <FormSection title="LLM 连接" description="模型提供商、端点与 API 密钥">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div>
              <Label htmlFor={`${idPrefix}-provider`} className="mb-2 block text-sm font-medium text-gray-700">
                模型提供商
              </Label>
              <Select
                value={llmProvider}
                onValueChange={(v) => onProviderChange(v as LlmProviderId)}
                disabled={formLoading}
              >
                <SelectTrigger id={`${idPrefix}-provider`} className="am-field w-full">
                  <SelectValue placeholder="选择提供商" />
                </SelectTrigger>
                <SelectContent>
                  {LLM_PROVIDER_PRESETS.map((p) => (
                    <SelectItem key={p.id} value={p.id}>
                      {p.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {preset?.hint && <p className="mt-1.5 text-xs text-brand-deep">{preset.hint}</p>}
            </div>

            <div>
              <Label htmlFor={`${idPrefix}-model`} className="mb-2 block text-sm font-medium text-gray-700">
                模型名称
              </Label>
              <Input
                id={`${idPrefix}-model`}
                className="am-field am-mono"
                value={capabilities.model}
                onChange={(e) => patchCaps({ model: e.target.value })}
                disabled={formLoading}
                placeholder="例如 deepseek-chat"
              />
            </div>

            <div className="md:col-span-2">
              <Label htmlFor={`${idPrefix}-baseUrl`} className="mb-2 block text-sm font-medium text-gray-700">
                API Base URL
              </Label>
              <Input
                id={`${idPrefix}-baseUrl`}
                className="am-field am-mono"
                value={baseUrl}
                onChange={(e) => onBaseUrlChange(e.target.value)}
                disabled={formLoading}
                placeholder="https://api.deepseek.com/v1"
              />
            </div>

            <div className="md:col-span-2">
              <Label htmlFor={`${idPrefix}-apiKey`} className="mb-2 block text-sm font-medium text-gray-700">
                API 密钥 {mode === 'create' ? '*' : ''}
              </Label>
              <Input
                id={`${idPrefix}-apiKey`}
                className="am-field am-mono"
                type="password"
                value={apiKey}
                onChange={(e) => onApiKeyChange(e.target.value)}
                disabled={formLoading}
                placeholder={mode === 'edit' ? '留空表示不修改' : '输入 LLM API Key'}
                autoComplete="off"
              />
            </div>

            <div>
              <Label htmlFor={`${idPrefix}-timeoutSeconds`} className="mb-2 block text-sm font-medium text-gray-700">
                超时时间（秒）
              </Label>
              <Input
                id={`${idPrefix}-timeoutSeconds`}
                className="am-field"
                type="number"
                value={timeoutSeconds}
                onChange={(e) => onTimeoutSecondsChange(parseInt(e.target.value, 10) || 30)}
                disabled={formLoading}
                min={1}
                max={300}
              />
            </div>

            <div>
              <Label htmlFor={`${idPrefix}-maxRetries`} className="mb-2 block text-sm font-medium text-gray-700">
                最大重试次数
              </Label>
              <Input
                id={`${idPrefix}-maxRetries`}
                className="am-field"
                type="number"
                value={maxRetries}
                onChange={(e) => onMaxRetriesChange(parseInt(e.target.value, 10) || 3)}
                disabled={formLoading}
                min={0}
                max={10}
              />
            </div>
          </div>
        </FormSection>

        <FormSection title="模型与能力" description="提示词、温度及可选工具能力">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div>
              <Label htmlFor={`${idPrefix}-temperature`} className="mb-2 block text-sm font-medium text-gray-700">
                温度 (0–2)
              </Label>
              <Input
                id={`${idPrefix}-temperature`}
                className="am-field"
                type="number"
                step="0.1"
                min="0"
                max="2"
                value={capabilities.temperature}
                onChange={(e) => patchCaps({ temperature: parseFloat(e.target.value) || 0.7 })}
                disabled={formLoading}
              />
            </div>

            <div className="flex flex-wrap items-center gap-6 pt-7">
              <div className="flex items-center gap-2">
                <Checkbox
                  id={`${idPrefix}-enableTools`}
                  checked={capabilities.enable_tools}
                  onCheckedChange={(checked) => patchCaps({ enable_tools: checked === true })}
                  disabled={formLoading}
                />
                <Label htmlFor={`${idPrefix}-enableTools`} className="text-sm text-gray-700">
                  启用 MCP 工具
                </Label>
              </div>
              <div className="flex items-center gap-2">
                <Checkbox
                  id={`${idPrefix}-enableRag`}
                  checked={capabilities.enable_rag}
                  onCheckedChange={(checked) => patchCaps({ enable_rag: checked === true })}
                  disabled={formLoading}
                />
                <Label htmlFor={`${idPrefix}-enableRag`} className="text-sm text-gray-700">
                  启用 RAG 知识库
                </Label>
              </div>
            </div>
          </div>

          <div className="mt-4">
            <Label htmlFor={`${idPrefix}-systemPrompt`} className="mb-2 block text-sm font-medium text-gray-700">
              系统提示词
            </Label>
            <Textarea
              id={`${idPrefix}-systemPrompt`}
              className="am-field"
              value={capabilities.system_prompt}
              onChange={(e) => patchCaps({ system_prompt: e.target.value })}
              disabled={formLoading}
              rows={4}
              placeholder="定义 Agent 的角色与行为…"
            />
          </div>

          {capabilities.enable_tools && (
            <div className="mt-4">
              <Label htmlFor={`${idPrefix}-mcpGroups`} className="mb-2 block text-sm font-medium text-gray-700">
                MCP 工具组（逗号分隔）
              </Label>
              <Input
                id={`${idPrefix}-mcpGroups`}
                className="am-field"
                value={capabilities.mcp_tool_groups.join(', ')}
                onChange={(e) =>
                  patchCaps({
                    mcp_tool_groups: e.target.value
                      .split(',')
                      .map((s) => s.trim())
                      .filter(Boolean),
                  })
                }
                disabled={formLoading}
                placeholder="例如 default, datahub"
              />
            </div>
          )}
        </FormSection>
      </div>

      <DialogFooter className="mt-5 shrink-0 border-t border-gray-200 bg-white pt-4 sm:justify-end">
        <Button type="button" variant="outline" className="am-btn-reset" onClick={onCancel} disabled={formLoading}>
          取消
        </Button>
        <Button type="submit" disabled={formLoading} className="am-btn-primary">
          {formLoading ? (mode === 'create' ? '创建中…' : '保存中…') : mode === 'create' ? '创建配置' : '保存更改'}
        </Button>
      </DialogFooter>
    </form>
  );
}
