/** LLM 提供商预设（OpenAI 兼容 API） */

export type LlmProviderId = 'openai' | 'deepseek' | 'custom';

export interface LlmProviderPreset {
  id: LlmProviderId;
  label: string;
  baseUrl: string;
  defaultModel: string;
  hint?: string;
}

export const LLM_PROVIDER_PRESETS: LlmProviderPreset[] = [
  {
    id: 'openai',
    label: 'OpenAI',
    baseUrl: 'https://api.openai.com/v1',
    defaultModel: 'gpt-4o-mini',
  },
  {
    id: 'deepseek',
    label: 'DeepSeek',
    baseUrl: 'https://api.deepseek.com/v1',
    defaultModel: 'deepseek-chat',
    hint: '在 platform.deepseek.com 创建 API Key',
  },
  {
    id: 'custom',
    label: '自定义兼容端点',
    baseUrl: '',
    defaultModel: '',
  },
];

export function getProviderPreset(id: LlmProviderId): LlmProviderPreset {
  return LLM_PROVIDER_PRESETS.find((p) => p.id === id) ?? LLM_PROVIDER_PRESETS[2];
}

export interface AgentCapabilitiesForm {
  model: string;
  system_prompt: string;
  temperature: number;
  enable_tools: boolean;
  enable_rag: boolean;
  mcp_tool_groups: string[];
  suggested_questions_after_answer: boolean;
}

export const DEFAULT_CAPABILITIES: AgentCapabilitiesForm = {
  model: 'gpt-4o-mini',
  system_prompt: '',
  temperature: 0.7,
  enable_tools: true,
  enable_rag: false,
  mcp_tool_groups: [],
  suggested_questions_after_answer: false,
};

export function capabilitiesFromRecord(raw?: Record<string, unknown> | null): AgentCapabilitiesForm {
  if (!raw) return { ...DEFAULT_CAPABILITIES };
  return {
    model: (raw.model as string) || DEFAULT_CAPABILITIES.model,
    system_prompt: (raw.system_prompt as string) || '',
    temperature: typeof raw.temperature === 'number' ? raw.temperature : DEFAULT_CAPABILITIES.temperature,
    enable_tools: raw.enable_tools !== false,
    enable_rag: Boolean(raw.enable_rag),
    mcp_tool_groups: Array.isArray(raw.mcp_tool_groups) ? (raw.mcp_tool_groups as string[]) : [],
    suggested_questions_after_answer: Boolean(raw.suggested_questions_after_answer),
  };
}

export function capabilitiesToRecord(
  form: AgentCapabilitiesForm,
  existing?: Record<string, unknown> | null,
): Record<string, unknown> {
  const record: Record<string, unknown> = {
    model: form.model,
    system_prompt: form.system_prompt,
    temperature: form.temperature,
    enable_tools: form.enable_tools,
    enable_rag: form.enable_rag,
    mcp_tool_groups: form.mcp_tool_groups,
    suggested_questions_after_answer: form.suggested_questions_after_answer,
  };
  if (existing?.knowledge_base_id) {
    record.knowledge_base_id = existing.knowledge_base_id;
  }
  return record;
}
