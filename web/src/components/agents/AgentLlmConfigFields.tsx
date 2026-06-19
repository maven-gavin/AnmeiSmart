'use client';

import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Checkbox } from '@/components/ui/checkbox';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import {
  LLM_PROVIDER_PRESETS,
  type AgentCapabilitiesForm,
  type LlmProviderId,
} from '@/lib/llmProviderPresets';

interface AgentLlmConfigFieldsProps {
  idPrefix: string;
  formLoading: boolean;
  llmProvider: LlmProviderId;
  onProviderChange: (id: LlmProviderId) => void;
  baseUrl: string;
  onBaseUrlChange: (v: string) => void;
  capabilities: AgentCapabilitiesForm;
  onCapabilitiesChange: (caps: AgentCapabilitiesForm) => void;
}

export function AgentLlmConfigFields({
  idPrefix,
  formLoading,
  llmProvider,
  onProviderChange,
  baseUrl,
  onBaseUrlChange,
  capabilities,
  onCapabilitiesChange,
}: AgentLlmConfigFieldsProps) {
  const preset = LLM_PROVIDER_PRESETS.find((p) => p.id === llmProvider);

  const patchCaps = (partial: Partial<AgentCapabilitiesForm>) => {
    onCapabilitiesChange({ ...capabilities, ...partial });
  };

  return (
    <div className="space-y-4 rounded-lg border border-gray-200 bg-gray-50 p-4">
      <h3 className="text-sm font-medium text-gray-800">LLM 模型配置</h3>

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
          {preset?.hint && <p className="mt-1 text-xs text-gray-500">{preset.hint}</p>}
        </div>

        <div>
          <Label htmlFor={`${idPrefix}-model`} className="mb-2 block text-sm font-medium text-gray-700">
            模型名称
          </Label>
          <Input
            id={`${idPrefix}-model`}
            className="am-field"
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
            className="am-field"
            type="text"
            value={baseUrl}
            onChange={(e) => onBaseUrlChange(e.target.value)}
            disabled={formLoading}
            placeholder="https://api.deepseek.com/v1"
          />
        </div>

        <div>
          <Label htmlFor={`${idPrefix}-temperature`} className="mb-2 block text-sm font-medium text-gray-700">
            温度 (0–1)
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
      </div>

      <div>
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

      <div className="flex flex-wrap gap-6">
        <div className="flex items-center space-x-2">
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
        <div className="flex items-center space-x-2">
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

      {capabilities.enable_tools && (
        <div>
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
    </div>
  );
}
