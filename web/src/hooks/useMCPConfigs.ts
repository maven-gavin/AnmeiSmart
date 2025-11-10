import { useState, useEffect, useCallback } from 'react'
import { 
  mcpConfigService, 
  MCPGroup, 
  MCPTool, 
  MCPGroupCreate, 
  MCPGroupUpdate, 
  MCPToolUpdate, 
  MCPServerStatus 
} from '@/service/mcpConfigService'

export function useMCPConfigs() {
  const [groups, setGroups] = useState<MCPGroup[]>([])
  const [tools, setTools] = useState<MCPTool[]>([])
  const [serverStatus, setServerStatus] = useState<MCPServerStatus | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // ========== 分组管理 ==========

  const loadGroups = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const data = await mcpConfigService.getGroups()
      setGroups(data)
    } catch (error: any) {
      setError(error.message || '获取分组列表失败')
      console.error('加载MCP分组失败:', error)
    } finally {
      setIsLoading(false)
    }
  }, [])

  const createGroup = useCallback(async (groupData: MCPGroupCreate): Promise<boolean> => {
    setIsSubmitting(true)
    setError(null)
    try {
      await mcpConfigService.createGroup(groupData)
      await loadGroups() // 重新加载分组列表
      return true
    } catch (error: any) {
      setError(error.message || '创建分组失败')
      console.error('创建MCP分组失败:', error)
      return false
    } finally {
      setIsSubmitting(false)
    }
  }, [loadGroups])

  const updateGroup = useCallback(async (groupId: string, groupData: MCPGroupUpdate): Promise<boolean> => {
    setIsSubmitting(true)
    setError(null)
    try {
      await mcpConfigService.updateGroup(groupId, groupData)
      await loadGroups() // 重新加载分组列表
      return true
    } catch (error: any) {
      setError(error.message || '更新分组失败')
      console.error('更新MCP分组失败:', error)
      return false
    } finally {
      setIsSubmitting(false)
    }
  }, [loadGroups])

  const deleteGroup = useCallback(async (groupId: string): Promise<boolean> => {
    setIsSubmitting(true)
    setError(null)
    try {
      await mcpConfigService.deleteGroup(groupId)
      await loadGroups() // 重新加载分组列表
      return true
    } catch (error: any) {
      setError(error.message || '删除分组失败')
      console.error('删除MCP分组失败:', error)
      return false
    } finally {
      setIsSubmitting(false)
    }
  }, [loadGroups])

  const getGroupApiKey = useCallback(async (groupId: string): Promise<string | null> => {
    setError(null)
    try {
      const data = await mcpConfigService.getGroupApiKey(groupId)
      return data.api_key
    } catch (error: any) {
      setError(error.message || '获取API密钥失败')
      console.error('获取分组API密钥失败:', error)
      return null
    }
  }, [])

  const regenerateApiKey = useCallback(async (groupId: string): Promise<string | null> => {
    setIsSubmitting(true)
    setError(null)
    try {
      const data = await mcpConfigService.regenerateApiKey(groupId)
      await loadGroups() // 重新加载分组列表以更新API密钥
      return data.api_key
    } catch (error: any) {
      setError(error.message || '重新生成API密钥失败')
      console.error('重新生成API密钥失败:', error)
      return null
    } finally {
      setIsSubmitting(false)
    }
  }, [loadGroups])

  const getGroupServerUrl = useCallback(async (groupId: string): Promise<{ server_url: string; server_code: string } | null> => {
    setError(null)
    try {
      const data = await mcpConfigService.getGroupServerUrl(groupId)
      return data
    } catch (error: any) {
      setError(error.message || '获取MCP Server URL失败')
      console.error('获取MCP Server URL失败:', error)
      return null
    }
  }, [])

  // ========== 工具管理 ==========

  const loadTools = useCallback(async (groupId?: string) => {
    setIsLoading(true)
    setError(null)
    try {
      const data = await mcpConfigService.getTools(groupId)
      setTools(data)
    } catch (error: any) {
      setError(error.message || '获取工具列表失败')
      console.error('加载MCP工具失败:', error)
    } finally {
      setIsLoading(false)
    }
  }, [])

  const updateTool = useCallback(async (toolId: string, toolData: MCPToolUpdate): Promise<boolean> => {
    setIsSubmitting(true)
    setError(null)
    try {
      await mcpConfigService.updateTool(toolId, toolData)
      await loadTools() // 重新加载工具列表
      return true
    } catch (error: any) {
      setError(error.message || '更新工具失败')
      console.error('更新MCP工具失败:', error)
      return false
    } finally {
      setIsSubmitting(false)
    }
  }, [loadTools])

  const refreshTools = useCallback(async (): Promise<boolean> => {
    setIsSubmitting(true)
    setError(null)
    try {
      await mcpConfigService.refreshTools()
      await loadTools() // 重新加载工具列表
      return true
    } catch (error: any) {
      const friendlyMessage = error.message?.includes('网络连接失败') 
        ? 'MCP服务器连接失败，请检查服务器是否正常运行' 
        : error.message || '刷新工具列表时遇到问题，请稍后重试'
      
      setError(friendlyMessage)
      console.error('刷新MCP工具列表失败:', error)
      return false
    } finally {
      setIsSubmitting(false)
    }
  }, [loadTools])

  // ========== 服务器状态 ==========

  const loadServerStatus = useCallback(async () => {
    setError(null)
    try {
      const data = await mcpConfigService.getMCPServerStatus()
      setServerStatus(data)
    } catch (error: any) {
      setError(error.message || '获取服务器状态失败')
      console.error('获取MCP服务器状态失败:', error)
    }
  }, [])

  // ========== 初始化加载 ==========

  useEffect(() => {
    loadGroups()
    loadTools()
    loadServerStatus()
  }, [loadGroups, loadTools, loadServerStatus])

  return {
    // 数据状态
    groups,
    tools,
    serverStatus,
    isLoading,
    isSubmitting,
    error,
    
    // 分组操作
    loadGroups,
    createGroup,
    updateGroup,
    deleteGroup,
    getGroupApiKey,
    regenerateApiKey,
    getGroupServerUrl,
    
    // 工具操作
    loadTools,
    updateTool,
    refreshTools,
    
    // 服务器状态
    loadServerStatus,
    
    // 错误处理
    clearError: () => setError(null)
  }
} 