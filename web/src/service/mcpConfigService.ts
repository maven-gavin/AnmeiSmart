import { apiClient } from './apiClient'

// =============== 类型定义 ===============

export interface MCPGroup {
  id: string
  name: string
  description?: string
  api_key_preview: string  // 修改：后端返回的是脱敏后的预览
  server_code?: string  // MCP服务器代码
  user_tier_access: string[]
  allowed_roles: string[]
  enabled: boolean
  tools_count?: number
  created_by: string
  created_at: string
  updated_at: string
}

export interface MCPGroupCreate {
  name: string
  description?: string
  user_tier_access?: string[]
  allowed_roles?: string[]
  enabled?: boolean
}

export interface MCPGroupUpdate {
  name?: string
  description?: string
  user_tier_access?: string[]
  allowed_roles?: string[]
  enabled?: boolean
}

export interface MCPTool {
  id: string
  tool_name: string  // 修改：与后端Schema保持一致
  group_id: string
  group_name?: string
  version: string
  description?: string
  enabled: boolean
  timeout_seconds: number
  config_data: Record<string, any>
  created_at: string
  updated_at: string
}

export interface MCPToolUpdate {
  group_id?: string
  enabled?: boolean
  timeout_seconds?: number
  description?: string
  config_data?: Record<string, any>
}

export interface MCPServerStatus {
  status: string
  server: {
    name: string
    version: string
    description: string
  }
  tools_count: number
  last_check: string
}

// =============== MCP配置服务类 ===============

class MCPConfigService {
  
  // ========== MCP分组管理 ==========
  
  /**
   * 获取MCP分组列表
   */
  async getGroups(): Promise<MCPGroup[]> {
    const response = await apiClient.get<{ success: boolean; data: MCPGroup[]; message: string }>('/mcp/admin/groups')
    // 确保返回的是数组
    if (response.data && Array.isArray(response.data.data)) {
      return response.data.data
    }
    // 如果响应格式不同，尝试直接返回 data
    if (Array.isArray(response.data)) {
      return response.data
    }
    // 默认返回空数组
    console.warn('getGroups: 响应格式异常', response.data)
    return []
  }

  /**
   * 创建MCP分组
   */
  async createGroup(groupData: MCPGroupCreate): Promise<MCPGroup> {
    const response = await apiClient.post<MCPGroup>('/mcp/admin/groups', { body: groupData })
    return response.data
  }

  /**
   * 更新MCP分组
   */
  async updateGroup(groupId: string, groupData: MCPGroupUpdate): Promise<MCPGroup> {
    const response = await apiClient.put<MCPGroup>(`/mcp/admin/groups/${groupId}`, { body: groupData })
    return response.data
  }

  /**
   * 删除MCP分组
   */
  async deleteGroup(groupId: string): Promise<void> {
    await apiClient.delete(`/mcp/admin/groups/${groupId}`)
  }

  /**
   * 获取分组API密钥
   */
  async getGroupApiKey(groupId: string): Promise<{ api_key: string }> {
    const response = await apiClient.get<{ api_key: string }>(`/mcp/admin/groups/${groupId}/api-key`)
    return response.data
  }

  /**
   * 重新生成分组API密钥
   */
  async regenerateApiKey(groupId: string): Promise<{ api_key: string }> {
    const response = await apiClient.post<{ api_key: string }>(`/mcp/admin/groups/${groupId}/regenerate-key`)
    return response.data
  }

  /**
   * 获取分组的完整MCP Server URL
   */
  async getGroupServerUrl(groupId: string): Promise<{ server_url: string; server_code: string }> {
    const response = await apiClient.get<{ server_url: string; server_code: string }>(`/mcp/admin/groups/${groupId}/server-url`)
    return response.data
  }

  // ========== MCP工具管理 ==========

  /**
   * 获取MCP工具列表
   */
  async getTools(groupId?: string): Promise<MCPTool[]> {
    const url = groupId ? `/mcp/admin/tools?group_id=${groupId}` : '/mcp/admin/tools'
    const response = await apiClient.get<{ success: boolean; data: MCPTool[]; message: string } | MCPTool[]>(url)
    // 确保返回的是数组
    if (response.data && typeof response.data === 'object' && 'data' in response.data && Array.isArray(response.data.data)) {
      return response.data.data
    }
    // 如果响应格式不同，尝试直接返回 data
    if (Array.isArray(response.data)) {
      return response.data
    }
    // 默认返回空数组
    console.warn('getTools: 响应格式异常', response.data)
    return []
  }

  /**
   * 更新MCP工具配置
   */
  async updateTool(toolId: string, toolData: MCPToolUpdate): Promise<MCPTool> {
    const response = await apiClient.put<MCPTool>(`/mcp/admin/tools/${toolId}`, { body: toolData })
    return response.data
  }

  /**
   * 刷新MCP工具列表
   */
  async refreshTools(): Promise<void> {
    await apiClient.post('/mcp/admin/tools/refresh')
  }

  // ========== MCP服务器状态 ==========

  /**
   * 获取MCP服务器状态
   */
  async getMCPServerStatus(): Promise<MCPServerStatus> {
    const response = await apiClient.get<MCPServerStatus>('/mcp/admin/server/status')
    return response.data
  }

  /**
   * 获取MCP调用日志
   */
  async getMCPCallLogs(groupId?: string, limit: number = 50): Promise<any[]> {
    const params = new URLSearchParams()
    if (groupId) params.append('group_id', groupId)
    params.append('limit', limit.toString())
    
    const url = `/mcp/admin/call-logs?${params.toString()}`
    const response = await apiClient.get<any[]>(url)
    return response.data
  }

  // ========== Agent配置生成 ==========

  /**
   * 生成Agent MCP配置
   */
  async generateAgentConfig(): Promise<Record<string, any>> {
    const response = await apiClient.get<Record<string, any>>('/mcp/admin/agent-config')
    return response.data
  }
}

// 导出服务实例
export const mcpConfigService = new MCPConfigService()

// 导出默认服务
export default mcpConfigService 