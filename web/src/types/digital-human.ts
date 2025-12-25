/**
 * 数字人相关类型定义
 */

export interface DigitalHuman {
  id: string;
  name: string;
  avatar?: string;
  description?: string;
  type: 'personal' | 'business' | 'specialized' | 'system';
  status: 'active' | 'inactive' | 'maintenance';
  is_system_created: boolean;
  personality?: {
    tone?: string;
    style?: string;
    specialization?: string;
  };
  greeting_message?: string;
  welcome_message?: string;
  user_id: string | null;
  conversation_count: number;
  message_count: number;
  last_active_at?: string;
  created_at: string;
  updated_at: string;
  
  // 关联信息
  user?: {
    id: string;
    username: string;
    email: string;
    phone?: string;
  };
  agent_configs?: DigitalHumanAgentConfig[];
  agent_count?: number;
}

export interface DigitalHumanAgentConfig {
  id: string;
  priority: number;
  is_active: boolean;
  scenarios?: string[];
  context_prompt?: string;
  agent_config: AgentConfig;
}

export interface AgentConfig {
  id: string;
  app_name: string;
  app_id: string;
  environment: string;
  description?: string;
  enabled: boolean;
  agent_type?: string;
  capabilities?: {
    features?: string[];
    specializations?: string[];
    languages?: string[];
  };
}

export interface CreateDigitalHumanRequest {
  name: string;
  avatar?: string;
  description?: string;
  type: 'personal' | 'business' | 'specialized' | 'system';
  status?: 'active' | 'inactive' | 'maintenance';
  personality?: {
    tone?: string;
    style?: string;
    specialization?: string;
  };
  greeting_message?: string;
  welcome_message?: string;
}

export interface UpdateDigitalHumanRequest extends Partial<CreateDigitalHumanRequest> {}

export interface AddAgentConfigRequest {
  agent_config_id: string;
  priority: number;
  scenarios?: string[];
  context_prompt?: string;
  is_active: boolean;
}

export interface UpdateAgentConfigRequest extends Partial<AddAgentConfigRequest> {}

// 管理员端类型
export interface AdminDigitalHuman extends DigitalHuman {
  // 管理员可以看到更多信息
}

export interface UpdateDigitalHumanStatusRequest {
  status: 'active' | 'inactive' | 'maintenance';
}

// 数字人统计信息
export interface DigitalHumanStats {
  total: number;
  active: number;
  inactive: number;
  maintenance: number;
  system: number;
  user: number;
}

// 数字人筛选条件
export interface DigitalHumanFilters {
  status?: string;
  type?: string;
  userId?: string;
  isSystemCreated?: boolean;
  search?: string;
  dateRange?: {
    start?: string;
    end?: string;
  };
}
