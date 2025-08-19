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

export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  message?: string
  error?: string
  error_code?: string
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
  async getGroups(): Promise<ApiResponse<MCPGroup[]>> {
    try {
      const response = await apiClient.get('/mcp/admin/groups')
      return (response.data as any) || { success: false, message: '获取分组列表失败' }
    } catch (error: any) {
      console.error('获取MCP分组列表失败:', error)
      return {
        success: false,
        error: error.response?.data?.detail || error.message || '获取分组列表失败'
      }
    }
  }

  /**
   * 创建MCP分组
   */
  async createGroup(groupData: MCPGroupCreate): Promise<ApiResponse<MCPGroup>> {
    try {
      const response = await apiClient.post('/mcp/admin/groups', groupData)
      return (response.data as any) || { success: false, message: '创建分组失败' }
    } catch (error: any) {
      console.error('创建MCP分组失败:', error)
      return {
        success: false,
        error: error.response?.data?.detail || error.message || '创建分组失败'
      }
    }
  }

  /**
   * 更新MCP分组
   */
  async updateGroup(groupId: string, groupData: MCPGroupUpdate): Promise<ApiResponse<MCPGroup>> {
    try {
      const response = await apiClient.put(`/mcp/admin/groups/${groupId}`, groupData)
      return (response.data as any) || { success: false, message: '更新分组失败' }
    } catch (error: any) {
      console.error('更新MCP分组失败:', error)
      return {
        success: false,
        error: error.response?.data?.detail || error.message || '更新分组失败'
      }
    }
  }

  /**
   * 删除MCP分组
   */
  async deleteGroup(groupId: string): Promise<ApiResponse> {
    try {
      const response = await apiClient.delete(`/mcp/admin/groups/${groupId}`)
      return (response.data as any) || { success: false, message: '删除分组失败' }
    } catch (error: any) {
      console.error('删除MCP分组失败:', error)
      return {
        success: false,
        error: error.response?.data?.detail || error.message || '删除分组失败'
      }
    }
  }

  /**
   * 获取分组API密钥
   */
  async getGroupApiKey(groupId: string): Promise<ApiResponse<{ api_key: string }>> {
    try {
      const response = await apiClient.get(`/mcp/admin/groups/${groupId}/api-key`)
      return (response.data as any) || { success: false, message: '获取API密钥失败' }
    } catch (error: any) {
      console.error('获取分组API密钥失败:', error)
      return {
        success: false,
        error: error.response?.data?.detail || error.message || '获取API密钥失败'
      }
    }
  }

  /**
   * 重新生成分组API密钥
   */
  async regenerateApiKey(groupId: string): Promise<ApiResponse<{ api_key: string }>> {
    try {
      const response = await apiClient.post(`/mcp/admin/groups/${groupId}/regenerate-key`)
      return (response.data as any) || { success: false, message: '重新生成API密钥失败' }
    } catch (error: any) {
      console.error('重新生成API密钥失败:', error)
      return {
        success: false,
        error: error.response?.data?.detail || error.message || '重新生成API密钥失败'
      }
    }
  }

  /**
   * 获取分组的完整MCP Server URL
   */
  async getGroupServerUrl(groupId: string): Promise<ApiResponse<{ server_url: string; server_code: string }>> {
    try {
      const url = `/mcp/admin/groups/${groupId}/server-url`
      const response = await apiClient.get(url)
      return (response.data as any) || { success: false, message: '获取MCP Server URL失败' }
    } catch (error: any) {
      console.error('获取MCP Server URL失败:', error)
      return {
        success: false,
        error: error.response?.data?.detail || error.message || '获取MCP Server URL失败'
      }
    }
  }

  // ========== MCP工具管理 ==========

  /**
   * 获取MCP工具列表
   */
  async getTools(groupId?: string): Promise<ApiResponse<MCPTool[]>> {
    try {
      const url = groupId ? `/mcp/admin/tools?group_id=${groupId}` : '/mcp/admin/tools'
      const response = await apiClient.get(url)
      return (response.data as any) || { success: false, message: '获取工具列表失败' }
    } catch (error: any) {
      console.error('获取MCP工具列表失败:', error)
      return {
        success: false,
        error: error.response?.data?.detail || error.message || '获取工具列表失败'
      }
    }
  }

  /**
   * 更新MCP工具配置
   */
  async updateTool(toolId: string, toolData: MCPToolUpdate): Promise<ApiResponse<MCPTool>> {
    try {
      const response = await apiClient.put(`/mcp/admin/tools/${toolId}`, toolData)
      return (response.data as any) || { success: false, message: '更新工具失败' }
    } catch (error: any) {
      console.error('更新MCP工具失败:', error)
      return {
        success: false,
        error: error.response?.data?.detail || error.message || '更新工具失败'
      }
    }
  }

  /**
   * 刷新MCP工具列表
   */
  async refreshTools(): Promise<ApiResponse> {
    try {
      const response = await apiClient.post('/mcp/admin/tools/refresh')
      return (response.data as any) || { success: false, message: '刷新工具列表失败' }
    } catch (error: any) {
      console.error('刷新MCP工具列表失败:', error)
      return {
        success: false,
        error: error.response?.data?.detail || error.message || '刷新工具列表失败'
      }
    }
  }

  // ========== MCP服务器状态 ==========

  /**
   * 获取MCP服务器状态
   */
  async getMCPServerStatus(): Promise<ApiResponse<MCPServerStatus>> {
    try {
      const response = await apiClient.get('/mcp/admin/server/status')
      return (response.data as any) || { success: false, message: '获取服务器状态失败' }
    } catch (error: any) {
      console.error('获取MCP服务器状态失败:', error)
      return {
        success: false,
        error: error.response?.data?.detail || error.message || '获取服务器状态失败'
      }
    }
  }

  /**
   * 获取MCP调用日志
   */
  async getMCPCallLogs(groupId?: string, limit: number = 50): Promise<ApiResponse<any[]>> {
    try {
      const params = new URLSearchParams()
      if (groupId) params.append('group_id', groupId)
      params.append('limit', limit.toString())
      
      const url = `/mcp/admin/call-logs?${params.toString()}`
      const response = await apiClient.get(url)
      return (response.data as any) || { success: false, message: '获取调用日志失败' }
    } catch (error: any) {
      console.error('获取MCP调用日志失败:', error)
      return {
        success: false,
        error: error.response?.data?.detail || error.message || '获取调用日志失败'
      }
    }
  }

  // ========== Agent配置生成 ==========

  /**
   * 生成Agent MCP配置
   */
  async generateAgentConfig(): Promise<ApiResponse<Record<string, any>>> {
    try {
      const response = await apiClient.get('/mcp/admin/agent-config')
      return (response.data as any) || { success: false, message: '生成Agent配置失败' }
    } catch (error: any) {
      console.error('生成Agent配置失败:', error)
      return {
        success: false,
        error: error.response?.data?.detail || error.message || '生成Agent配置失败'
      }
    }
  }
}

// 导出服务实例
export const mcpConfigService = new MCPConfigService()

// 导出默认服务
export default mcpConfigService 