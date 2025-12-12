'use client'

import React, { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'
import { Copy, Plus, Settings, Trash2, RotateCcw, Edit, RefreshCw, Check } from 'lucide-react'
import { 
  Dialog, 
  DialogContent, 
  DialogDescription, 
  DialogFooter, 
  DialogHeader, 
  DialogTitle, 
  DialogTrigger 
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from '@/components/ui/table'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useMCPConfigs } from '@/hooks/useMCPConfigs'
import { MCPGroup, MCPTool } from '@/service/mcpConfigService'
import { EnhancedPagination } from '@/components/ui/pagination'

export function MCPConfigPanel() {
  const {
    groups,
    tools,
    serverStatus,
    isLoading,
    isSubmitting,
    error,
    createGroup,
    updateGroup,
    deleteGroup,
    getGroupApiKey,
    regenerateApiKey,
    getGroupServerUrl,
    updateTool,
    refreshTools,
    clearError
  } = useMCPConfigs()

  const [isGroupDialogOpen, setIsGroupDialogOpen] = useState(false)
  const [editingGroup, setEditingGroup] = useState<MCPGroup | null>(null)
  const [copySuccess, setCopySuccess] = useState<string | null>(null)
  const [urlCopySuccess, setUrlCopySuccess] = useState<string | null>(null)

  // 工具编辑状态
  const [isToolEditDialogOpen, setIsToolEditDialogOpen] = useState(false)
  const [isToolConfigDialogOpen, setIsToolConfigDialogOpen] = useState(false)
  const [editingTool, setEditingTool] = useState<MCPTool | null>(null)

  // 表单状态
  const [groupForm, setGroupForm] = useState({
    name: '',
    description: ''
  })

  // 工具编辑表单状态
  const [toolEditForm, setToolEditForm] = useState({
    description: '',
    group_id: '',
    timeout_seconds: 30
  })

  // 工具配置表单状态
  const [toolConfigForm, setToolConfigForm] = useState({
    config_data: '{}'
  })

  // 分组查询和分页状态
  const [groupSearchName, setGroupSearchName] = useState('')
  const [groupCurrentPage, setGroupCurrentPage] = useState(1)
  const [groupItemsPerPage, setGroupItemsPerPage] = useState(5)
  const [allGroups, setAllGroups] = useState<MCPGroup[]>([])

  // 工具查询和分页状态
  const [toolSearchName, setToolSearchName] = useState('')
  const [toolSearchGroup, setToolSearchGroup] = useState('all')
  const [toolCurrentPage, setToolCurrentPage] = useState(1)
  const [toolItemsPerPage, setToolItemsPerPage] = useState(5)
  const [allTools, setAllTools] = useState<MCPTool[]>([])

  // 更新数据状态
  React.useEffect(() => {
    // 确保 groups 是数组
    const groupsArray = Array.isArray(groups) ? groups : []
    setAllGroups(groupsArray)
    // 重置到第一页
    setGroupCurrentPage(1)
  }, [groups])

  React.useEffect(() => {
    const toolsArray = Array.isArray(tools) ? tools : []
    setAllTools(toolsArray)
    // 重置到第一页
    setToolCurrentPage(1)
  }, [tools])

  // 分组过滤逻辑（前端过滤）
  const filteredGroups = React.useMemo(() => {
    let filtered = [...allGroups]
    
    if (groupSearchName) {
      const searchLower = groupSearchName.toLowerCase()
      filtered = filtered.filter(group => 
        group.name.toLowerCase().includes(searchLower) ||
        (group.description && group.description.toLowerCase().includes(searchLower))
      )
    }
    
    return filtered
  }, [allGroups, groupSearchName])

  // 工具过滤逻辑（前端过滤）
  const filteredTools = React.useMemo(() => {
    let filtered = [...allTools]
    
    if (toolSearchName) {
      const searchLower = toolSearchName.toLowerCase()
      filtered = filtered.filter(tool => 
        tool.tool_name.toLowerCase().includes(searchLower) ||
        (tool.description && tool.description.toLowerCase().includes(searchLower))
      )
    }
    
    if (toolSearchGroup && toolSearchGroup !== 'all') {
      filtered = filtered.filter(tool => 
        tool.group_name === toolSearchGroup
      )
    }
    
    return filtered
  }, [allTools, toolSearchName, toolSearchGroup])

  // 分组分页逻辑
  const groupIndexOfLastItem = groupCurrentPage * groupItemsPerPage
  const groupIndexOfFirstItem = groupIndexOfLastItem - groupItemsPerPage
  const currentGroups = filteredGroups.slice(groupIndexOfFirstItem, groupIndexOfLastItem)
  const groupTotalPages = Math.ceil(filteredGroups.length / groupItemsPerPage)

  // 工具分页逻辑
  const toolIndexOfLastItem = toolCurrentPage * toolItemsPerPage
  const toolIndexOfFirstItem = toolIndexOfLastItem - toolItemsPerPage
  const currentTools = filteredTools.slice(toolIndexOfFirstItem, toolIndexOfLastItem)
  const toolTotalPages = Math.ceil(filteredTools.length / toolItemsPerPage)

  // 分组查询功能
  const filterGroups = () => {
    setGroupCurrentPage(1)
  }

  // 重置分组查询
  const resetGroupFilters = () => {
    setGroupSearchName('')
    setGroupCurrentPage(1)
  }

  // 工具查询功能
  const filterTools = () => {
    setToolCurrentPage(1)
  }

  // 重置工具查询
  const resetToolFilters = () => {
    setToolSearchName('')
    setToolSearchGroup('all')
    setToolCurrentPage(1)
  }

  // 显示Loading状态
  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="text-center">
          <div className="mb-4 h-8 w-8 animate-spin rounded-full border-b-2 border-t-2 border-orange-500"></div>
          <p className="text-gray-600">加载MCP配置...</p>
        </div>
      </div>
    )
  }

  // 复制API密钥到剪贴板
  const handleCopyApiKey = async (groupId: string) => {
    try {
      const apiKey = await getGroupApiKey(groupId)
      if (apiKey) {
        await navigator.clipboard.writeText(apiKey)
        setCopySuccess(groupId)
        setTimeout(() => setCopySuccess(null), 2000) // 2秒后清除成功提示
      }
    } catch (error) {
      console.error('复制API密钥失败:', error)
      alert('复制失败，请重试')
    }
  }

  // 复制MCP Server URL到剪贴板
  const handleCopyServerUrl = async (groupId: string) => {
    try {
      const urlData = await getGroupServerUrl(groupId)
      if (urlData) {
        await navigator.clipboard.writeText(urlData.server_url)
        setUrlCopySuccess(groupId)
        setTimeout(() => setUrlCopySuccess(null), 2000) // 2秒后清除成功提示
      }
    } catch (error) {
      console.error('复制MCP Server URL失败:', error)
      alert('复制失败，请重试')
    }
  }

  // 创建/更新分组
  const handleSaveGroup = async () => {
    let success = false
    if (editingGroup) {
      success = await updateGroup(editingGroup.id, groupForm)
    } else {
      success = await createGroup(groupForm)
    }
    
    if (success) {
      setIsGroupDialogOpen(false)
      setEditingGroup(null)
      setGroupForm({ name: '', description: '' })
    }
  }

  // 编辑工具基本信息
  const handleEditTool = (tool: MCPTool) => {
    setEditingTool(tool)
    setToolEditForm({
      description: tool.description || '',
      group_id: tool.group_id,
      timeout_seconds: tool.timeout_seconds
    })
    setIsToolEditDialogOpen(true)
  }

  // 保存工具编辑
  const handleSaveToolEdit = async () => {
    if (!editingTool) return

    const success = await updateTool(editingTool.id, {
      description: toolEditForm.description,
      group_id: toolEditForm.group_id,
      timeout_seconds: toolEditForm.timeout_seconds
    })

    if (success) {
      setIsToolEditDialogOpen(false)
      setEditingTool(null)
      setToolEditForm({ description: '', group_id: '', timeout_seconds: 30 })
    }
  }

  // 配置工具高级参数
  const handleConfigTool = (tool: MCPTool) => {
    setEditingTool(tool)
    setToolConfigForm({
      config_data: JSON.stringify(tool.config_data, null, 2)
    })
    setIsToolConfigDialogOpen(true)
  }

  // 保存工具配置
  const handleSaveToolConfig = async () => {
    if (!editingTool) return

    try {
      // 验证JSON格式
      const configData = JSON.parse(toolConfigForm.config_data)
      
      const success = await updateTool(editingTool.id, {
        config_data: configData
      })

      if (success) {
        setIsToolConfigDialogOpen(false)
        setEditingTool(null)
        setToolConfigForm({ config_data: '{}' })
      }
    } catch (error) {
      alert('配置数据格式错误，请检查JSON格式是否正确')
    }
  }

  // 删除分组
  const handleDeleteGroup = async (groupId: string) => {
    if (!confirm('确定要删除此MCP分组吗？删除后无法恢复。')) {
      return
    }
    await deleteGroup(groupId)
  }

  // 重新生成API密钥
  const handleRegenerateApiKey = async (groupId: string) => {
    if (!confirm('确定要重新生成API密钥吗？旧密钥将立即失效。')) {
      return
    }
    await regenerateApiKey(groupId)
  }

  // 切换分组启用状态
  const handleToggleGroup = async (groupId: string, enabled: boolean) => {
    try {
      await updateGroup(groupId, { enabled })
    } catch (error) {
      console.error('更新分组状态失败:', error)
    }
  }

  // 切换工具启用状态
  const handleToggleTool = async (toolId: string, enabled: boolean) => {
    try {
      await updateTool(toolId, { enabled })
    } catch (error) {
      console.error('更新工具状态失败:', error)
    }
  }

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow">
      {/* 错误提示 */}
      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertDescription className="flex items-center justify-between">
            {error}
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={clearError}
              className="h-auto p-1 text-destructive-foreground hover:text-destructive-foreground/80"
            >
              ×
            </Button>
          </AlertDescription>
        </Alert>
      )}

      <Tabs defaultValue="groups" className="space-y-4">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="groups">工具分组管理</TabsTrigger>
          <TabsTrigger value="tools">工具配置管理</TabsTrigger>
        </TabsList>

        {/* 工具分组管理 */}
        <TabsContent value="groups" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-lg font-medium text-gray-800">工具分组管理</CardTitle>
                  <CardDescription className="text-gray-600">
                    管理MCP工具分组，每个分组拥有独立的API密钥和Server URL用于权限控制和外部系统接入
                  </CardDescription>
                </div>
                <Dialog open={isGroupDialogOpen} onOpenChange={setIsGroupDialogOpen}>
                  <DialogTrigger asChild>
                    <Button 
                      onClick={() => {
                        setEditingGroup(null)
                        setGroupForm({ name: '', description: '' })
                      }}
                      className="bg-orange-500 hover:bg-orange-600"
                    >
                      <Plus className="w-4 h-4 mr-2" />
                      添加分组
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="sm:max-w-[600px]">
                    <DialogHeader>
                      <DialogTitle className="text-lg font-medium text-gray-800">
                        {editingGroup ? '编辑MCP分组' : '创建MCP分组'}
                      </DialogTitle>
                      <DialogDescription className="text-gray-600">
                        {editingGroup ? '修改现有分组信息' : '创建新的MCP工具分组，系统将自动生成API密钥'}
                      </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4 py-4">
                      <div className="space-y-2">
                        <Label htmlFor="name" className="text-sm font-medium text-gray-700">
                          分组名称 <span className="text-red-500">*</span>
                        </Label>
                        <Input
                          id="name"
                          value={groupForm.name}
                          onChange={(e) => setGroupForm(prev => ({ ...prev, name: e.target.value }))}
                          placeholder="如：用户服务工具组"
                          className="w-full"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="description" className="text-sm font-medium text-gray-700">
                          分组描述
                        </Label>
                        <Textarea
                          id="description"
                          value={groupForm.description}
                          onChange={(e) => setGroupForm(prev => ({ ...prev, description: e.target.value }))}
                          placeholder="描述此分组包含的工具用途和使用场景..."
                          rows={3}
                          className="w-full"
                        />
                      </div>
                    </div>
                    <DialogFooter>
                      <Button 
                        variant="outline" 
                        onClick={() => setIsGroupDialogOpen(false)}
                        disabled={isSubmitting}
                      >
                        取消
                      </Button>
                      <Button 
                        onClick={handleSaveGroup} 
                        disabled={isSubmitting || !groupForm.name.trim()}
                        className="bg-orange-500 hover:bg-orange-600"
                      >
                        {isSubmitting ? '处理中...' : (editingGroup ? '更新' : '创建')}
                      </Button>
                    </DialogFooter>
                  </DialogContent>
                </Dialog>
              </div>
            </CardHeader>
            <CardContent>
              {/* 搜索区域 - 参考资源管理模块样式 */}
              <div className="mb-6 rounded-lg border border-gray-200 bg-white p-4 shadow">
                <div className="flex items-center gap-4">
                  <div className="flex-1">
                    <Label htmlFor="groupSearch" className="mb-2 block text-sm font-medium">关键词搜索</Label>
                    <Input
                      id="groupSearch"
                      value={groupSearchName}
                      onChange={(e) => setGroupSearchName(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          filterGroups()
                        }
                      }}
                      placeholder="搜索分组名称或描述..."
                      className="w-full max-w-md"
                    />
                  </div>
                  <div className="flex items-end gap-2 pb-1">
                    <Button variant="outline" onClick={resetGroupFilters}>
                      重置
                    </Button>
                    <Button className="bg-orange-500 hover:bg-orange-600" onClick={filterGroups}>
                      查询
                    </Button>
                  </div>
                </div>
              </div>

              {/* 表格区域 - 参考资源管理模块样式 */}
              <div className="overflow-hidden rounded-lg border border-gray-200 shadow">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                        序号
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                        分组名称
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                        分组描述
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                        API密钥
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                        MCP Server URL
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                        工具数量
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                        状态
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                        创建时间
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                        操作
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200 bg-white">
                    {isLoading ? (
                      <tr>
                        <td colSpan={9} className="px-6 py-12 text-center">
                          <div className="flex justify-center">
                            <div className="h-8 w-8 animate-spin rounded-full border-2 border-gray-300 border-t-orange-500"></div>
                          </div>
                        </td>
                      </tr>
                    ) : filteredGroups.length === 0 ? (
                      <tr>
                        <td colSpan={9} className="px-6 py-4 text-center text-sm text-gray-500">
                          {allGroups.length === 0 ? '暂无MCP分组，点击上方"添加分组"按钮创建第一个工具分组' : '未找到匹配的分组，请调整查询条件或重置查询'}
                        </td>
                      </tr>
                    ) : (
                      currentGroups.map((group, index) => (
                        <tr key={group.id} className="hover:bg-gray-50">
                          <td className="px-6 py-4 text-sm font-medium text-gray-900">
                            {groupIndexOfFirstItem + index + 1}
                          </td>
                          <td className="px-6 py-4 text-sm">
                            <div className="font-medium text-gray-900">{group.name}</div>
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-500">
                            {group.description || '-'}
                          </td>
                          <td className="px-6 py-4 text-sm">
                            <div className="flex items-center space-x-2">
                              <code className="text-xs bg-gray-50 border px-2 py-1 rounded font-mono">
                                {group.api_key_preview}
                              </code>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleCopyApiKey(group.id)}
                                className="h-8 w-8 p-0"
                                title={copySuccess === group.id ? "已复制" : "复制API密钥"}
                              >
                                {copySuccess === group.id ? (
                                  <Check className="w-4 h-4 text-green-600" />
                                ) : (
                                  <Copy className="w-4 h-4" />
                                )}
                              </Button>
                            </div>
                          </td>
                          <td className="px-6 py-4 text-sm">
                            <div className="flex items-center space-x-2">
                              {group.enabled ? (
                                <>
                                  <code className="text-xs bg-blue-50 border px-2 py-1 rounded font-mono max-w-48 truncate">
                                    /mcp/server/{group.server_code || '••••••••••••'}/mcp
                                  </code>
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => handleCopyServerUrl(group.id)}
                                    className="h-8 w-8 p-0"
                                    title={urlCopySuccess === group.id ? "已复制" : "复制Server URL"}
                                  >
                                    {urlCopySuccess === group.id ? (
                                      <Check className="w-4 h-4 text-green-600" />
                                    ) : (
                                      <Copy className="w-4 h-4" />
                                    )}
                                  </Button>
                                </>
                              ) : (
                                <span className="text-xs text-gray-400">未启用</span>
                              )}
                            </div>
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-500">
                            {group.tools_count || 0}个
                          </td>
                          <td className="px-6 py-4 text-sm">
                            <Switch
                              checked={group.enabled}
                              onCheckedChange={(checked) => handleToggleGroup(group.id, checked)}
                            />
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-500">
                            {new Date(group.created_at).toLocaleDateString('zh-CN')}
                          </td>
                          <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                            <div className="flex items-center gap-2">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => {
                                  setEditingGroup(group)
                                  setGroupForm({ name: group.name, description: group.description || '' })
                                  setIsGroupDialogOpen(true)
                                }}
                                className="text-blue-600 hover:text-blue-800"
                              >
                                <Edit className="w-4 h-4 mr-1" />
                                编辑
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleRegenerateApiKey(group.id)}
                                className="text-green-600 hover:text-green-800"
                                title="重新生成API密钥"
                              >
                                <RotateCcw className="w-4 h-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleDeleteGroup(group.id)}
                                className="text-red-600 hover:text-red-800"
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            </div>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
              
              {/* 分页组件 - 参考资源管理模块 */}
              {filteredGroups.length > 0 && (
                <div className="mt-6">
                  <EnhancedPagination
                    currentPage={groupCurrentPage}
                    totalPages={groupTotalPages}
                    totalItems={filteredGroups.length}
                    itemsPerPage={groupItemsPerPage}
                    itemsPerPageOptions={[5, 10, 20, 50, 100]}
                    onPageChange={setGroupCurrentPage}
                    onItemsPerPageChange={(newLimit) => {
                      setGroupItemsPerPage(newLimit)
                      setGroupCurrentPage(1)
                    }}
                    showPageInput={true}
                  />
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* 工具配置管理 */}
        <TabsContent value="tools" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-lg font-medium text-gray-800">工具配置管理</CardTitle>
                  <CardDescription className="text-gray-600">
                    管理各个MCP工具的配置参数和启用状态
                  </CardDescription>
                </div>
                <Button 
                  onClick={refreshTools}
                  disabled={isSubmitting}
                  className="bg-orange-500 hover:bg-orange-600"
                >
                  <RefreshCw className={`w-4 h-4 mr-2 ${isSubmitting ? 'animate-spin' : ''}`} />
                  刷新工具列表
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {/* 搜索区域 - 参考资源管理模块样式 */}
              <div className="mb-6 rounded-lg border border-gray-200 bg-white p-4 shadow">
                <div className="flex items-center gap-4">
                  <div className="flex-1">
                    <Label htmlFor="toolSearch" className="mb-2 block text-sm font-medium">关键词搜索</Label>
                    <Input
                      id="toolSearch"
                      value={toolSearchName}
                      onChange={(e) => setToolSearchName(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          filterTools()
                        }
                      }}
                      placeholder="搜索工具名称或描述..."
                      className="w-full max-w-md"
                    />
                  </div>
                  <div className="flex items-end gap-2 pb-1">
                    <Select value={toolSearchGroup} onValueChange={setToolSearchGroup}>
                      <SelectTrigger className="w-40">
                        <SelectValue placeholder="所属分组" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">全部分组</SelectItem>
                        {Array.isArray(allGroups) && allGroups.length > 0 && allGroups.map((group) => (
                          <SelectItem key={group.id} value={group.name}>
                            {group.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <Button variant="outline" onClick={resetToolFilters}>
                      重置
                    </Button>
                    <Button className="bg-orange-500 hover:bg-orange-600" onClick={filterTools}>
                      查询
                    </Button>
                  </div>
                </div>
              </div>

              {/* 表格区域 - 参考资源管理模块样式 */}
              <div className="overflow-hidden rounded-lg border border-gray-200 shadow">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                        序号
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                        工具名称
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                        所属分组
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                        版本
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                        描述
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                        超时时间
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                        状态
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                        操作
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200 bg-white">
                    {isLoading ? (
                      <tr>
                        <td colSpan={8} className="px-6 py-12 text-center">
                          <div className="flex justify-center">
                            <div className="h-8 w-8 animate-spin rounded-full border-2 border-gray-300 border-t-orange-500"></div>
                          </div>
                        </td>
                      </tr>
                    ) : filteredTools.length === 0 ? (
                      <tr>
                        <td colSpan={8} className="px-6 py-4 text-center text-sm text-gray-500">
                          {allTools.length === 0 ? '暂无MCP工具，点击上方"刷新工具列表"按钮从服务器同步工具信息' : '未找到匹配的工具，请调整查询条件或重置查询'}
                        </td>
                      </tr>
                    ) : (
                      currentTools.map((tool, index) => (
                        <tr key={tool.id} className="hover:bg-gray-50">
                          <td className="px-6 py-4 text-sm font-medium text-gray-900">
                            {toolIndexOfFirstItem + index + 1}
                          </td>
                          <td className="px-6 py-4 text-sm">
                            <div className="font-medium text-gray-900">{tool.tool_name}</div>
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-500">
                            <Badge variant="outline" className="text-xs">
                              {tool.group_name || '未分组'}
                            </Badge>
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-500">
                            {tool.version}
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-500">
                            {tool.description || '-'}
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-500">
                            {tool.timeout_seconds}秒
                          </td>
                          <td className="px-6 py-4 text-sm">
                            <Switch
                              checked={tool.enabled}
                              onCheckedChange={(checked) => handleToggleTool(tool.id, checked)}
                              disabled={isSubmitting}
                            />
                          </td>
                          <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                            <div className="flex items-center gap-2">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleEditTool(tool)}
                                className="text-blue-600 hover:text-blue-800"
                              >
                                <Edit className="w-4 h-4 mr-1" />
                                编辑
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleConfigTool(tool)}
                                className="text-gray-600 hover:text-gray-800"
                                title="高级配置"
                              >
                                <Settings className="w-4 h-4" />
                              </Button>
                            </div>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
              
              {/* 分页组件 - 参考资源管理模块 */}
              {filteredTools.length > 0 && (
                <div className="mt-6">
                  <EnhancedPagination
                    currentPage={toolCurrentPage}
                    totalPages={toolTotalPages}
                    totalItems={filteredTools.length}
                    itemsPerPage={toolItemsPerPage}
                    itemsPerPageOptions={[5, 10, 20, 50, 100]}
                    onPageChange={setToolCurrentPage}
                    onItemsPerPageChange={(newLimit) => {
                      setToolItemsPerPage(newLimit)
                      setToolCurrentPage(1)
                    }}
                    showPageInput={true}
                  />
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* 工具编辑对话框 */}
      <Dialog open={isToolEditDialogOpen} onOpenChange={setIsToolEditDialogOpen}>
        <DialogContent className="sm:max-w-[600px]">
          <DialogHeader>
            <DialogTitle className="text-lg font-medium text-gray-800">
              编辑工具信息
            </DialogTitle>
            <DialogDescription className="text-gray-600">
              修改工具的基本配置信息，包括描述、分组归属和超时设置
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label className="text-sm font-medium text-gray-700">工具名称</Label>
              <Input
                value={editingTool?.tool_name || ''}
                disabled
                className="bg-gray-50"
              />
              <p className="text-xs text-gray-500">工具名称由系统管理，不可修改</p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="tool_description" className="text-sm font-medium text-gray-700">
                工具描述
              </Label>
              <Textarea
                id="tool_description"
                value={toolEditForm.description}
                onChange={(e) => setToolEditForm(prev => ({ ...prev, description: e.target.value }))}
                placeholder="描述此工具的功能和用途..."
                rows={3}
                className="w-full"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="tool_group" className="text-sm font-medium text-gray-700">
                所属分组 <span className="text-red-500">*</span>
              </Label>
              <Select
                value={toolEditForm.group_id}
                onValueChange={(value) => setToolEditForm(prev => ({ ...prev, group_id: value }))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="选择工具分组" />
                </SelectTrigger>
                <SelectContent>
                  {Array.isArray(groups) && groups.length > 0 ? (
                    groups.map((group) => (
                      <SelectItem key={group.id} value={group.id}>
                        {group.name}
                      </SelectItem>
                    ))
                  ) : (
                    <SelectItem value="no-groups" disabled>暂无分组</SelectItem>
                  )}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="tool_timeout" className="text-sm font-medium text-gray-700">
                超时时间（秒）
              </Label>
              <Input
                id="tool_timeout"
                type="number"
                min="1"
                max="300"
                value={toolEditForm.timeout_seconds}
                onChange={(e) => setToolEditForm(prev => ({ 
                  ...prev, 
                  timeout_seconds: parseInt(e.target.value) || 30 
                }))}
                className="w-full"
              />
              <p className="text-xs text-gray-500">工具执行的最大超时时间，建议设置为10-60秒</p>
            </div>
          </div>
          <DialogFooter>
            <Button 
              variant="outline" 
              onClick={() => setIsToolEditDialogOpen(false)}
              disabled={isSubmitting}
            >
              取消
            </Button>
            <Button 
              onClick={handleSaveToolEdit} 
              disabled={isSubmitting || !toolEditForm.group_id}
              className="bg-orange-500 hover:bg-orange-600"
            >
              {isSubmitting ? '保存中...' : '保存更改'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 工具高级配置对话框 */}
      <Dialog open={isToolConfigDialogOpen} onOpenChange={setIsToolConfigDialogOpen}>
        <DialogContent className="sm:max-w-[700px] max-h-[80vh] flex flex-col">
          <DialogHeader>
            <DialogTitle className="text-lg font-medium text-gray-800">
              高级配置参数
            </DialogTitle>
            <DialogDescription className="text-gray-600">
              配置工具的高级参数，请使用有效的JSON格式
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4 flex-1">
            <div className="space-y-2">
              <Label className="text-sm font-medium text-gray-700">工具名称</Label>
              <Input
                value={editingTool?.tool_name || ''}
                disabled
                className="bg-gray-50"
              />
            </div>
            <div className="space-y-2 flex-1">
              <Label htmlFor="tool_config_data" className="text-sm font-medium text-gray-700">
                配置参数 (JSON格式)
              </Label>
              <Textarea
                id="tool_config_data"
                value={toolConfigForm.config_data}
                onChange={(e) => setToolConfigForm(prev => ({ ...prev, config_data: e.target.value }))}
                placeholder='{"key": "value", "timeout": 30}'
                rows={12}
                className="w-full font-mono text-sm"
                style={{ minHeight: '300px' }}
              />
              <div className="text-xs text-gray-500 space-y-1">
                <p>• 请使用有效的JSON格式配置参数</p>
                <p>• 配置示例：{`{"max_retries": 3, "cache_enabled": true, "api_endpoint": "https://api.example.com"}`}</p>
                <p>• 空配置请使用：{`{}`}</p>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button 
              variant="outline" 
              onClick={() => setIsToolConfigDialogOpen(false)}
              disabled={isSubmitting}
            >
              取消
            </Button>
            <Button 
              onClick={handleSaveToolConfig} 
              disabled={isSubmitting}
              className="bg-orange-500 hover:bg-orange-600"
            >
              {isSubmitting ? '保存中...' : '保存配置'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default MCPConfigPanel 