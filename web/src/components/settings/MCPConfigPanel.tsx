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
  const [groupItemsPerPage] = useState(5)
  const [filteredGroups, setFilteredGroups] = useState<MCPGroup[]>([])
  const [allGroups, setAllGroups] = useState<MCPGroup[]>([])

  // 工具查询和分页状态
  const [toolSearchName, setToolSearchName] = useState('')
  const [toolSearchGroup, setToolSearchGroup] = useState('all')
  const [toolCurrentPage, setToolCurrentPage] = useState(1)
  const [toolItemsPerPage] = useState(5)
  const [filteredTools, setFilteredTools] = useState<MCPTool[]>([])
  const [allTools, setAllTools] = useState<MCPTool[]>([])

  // 更新数据状态
  React.useEffect(() => {
    setAllGroups(groups)
    setFilteredGroups(groups)
  }, [groups])

  React.useEffect(() => {
    setAllTools(tools)
    setFilteredTools(tools)
  }, [tools])

  // 分组查询功能
  const filterGroups = () => {
    setGroupCurrentPage(1)
    let filtered = [...allGroups]
    
    if (groupSearchName) {
      filtered = filtered.filter(group => 
        group.name.toLowerCase().includes(groupSearchName.toLowerCase())
      )
    }
    
    setFilteredGroups(filtered)
  }

  // 重置分组查询
  const resetGroupFilters = () => {
    setGroupSearchName('')
    setFilteredGroups(allGroups)
    setGroupCurrentPage(1)
  }

  // 工具查询功能
  const filterTools = () => {
    setToolCurrentPage(1)
    let filtered = [...allTools]
    
    if (toolSearchName) {
      filtered = filtered.filter(tool => 
        tool.tool_name.toLowerCase().includes(toolSearchName.toLowerCase())
      )
    }
    
    if (toolSearchGroup && toolSearchGroup !== 'all') {
      filtered = filtered.filter(tool => 
        tool.group_name === toolSearchGroup
      )
    }
    
    setFilteredTools(filtered)
  }

  // 重置工具查询
  const resetToolFilters = () => {
    setToolSearchName('')
    setToolSearchGroup('all')
    setFilteredTools(allTools)
    setToolCurrentPage(1)
  }

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
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-gray-800">MCP配置管理</h2>
        <p className="mt-1 text-sm text-gray-600">
          管理Model Context Protocol工具分组和权限配置
        </p>
      </div>

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

      {/* 说明提示 */}
      <Alert className="mb-6">
        <AlertDescription>
          MCP（Model Context Protocol）是一个开放标准协议，为AI平台提供标准化的工具调用接口。通过分组管理可以精确控制不同用户的工具访问权限。每个启用的分组会自动生成一个唯一的Server URL用于外部系统调用。
        </AlertDescription>
      </Alert>

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
              {/* 分组查询区域 */}
              {allGroups.length > 0 && (
                <div className="mb-6 rounded-lg border border-gray-200 bg-gray-50 p-4">
                  <h3 className="mb-4 text-sm font-medium text-gray-800">分组查询</h3>
                  <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                    <div>
                      <Label htmlFor="groupName" className="mb-2 block text-sm font-medium">分组名称</Label>
                      <Input
                        id="groupName"
                        value={groupSearchName}
                        onChange={(e) => setGroupSearchName(e.target.value)}
                        placeholder="搜索分组名称"
                        className="w-full"
                      />
                    </div>
                  </div>
                  <div className="mt-4 flex justify-end space-x-2">
                    <Button variant="outline" onClick={resetGroupFilters}>
                      重置
                    </Button>
                    <Button className="bg-orange-500 hover:bg-orange-600" onClick={filterGroups}>
                      查询
                    </Button>
                  </div>
                </div>
              )}

              {filteredGroups.length === 0 && allGroups.length === 0 ? (
                <div className="text-center py-8">
                  <div className="text-gray-400 mb-2">
                    <Settings className="w-12 h-12 mx-auto" />
                  </div>
                  <p className="text-gray-600">暂无MCP分组</p>
                  <p className="text-sm text-gray-500">点击上方"添加分组"按钮创建第一个工具分组</p>
                </div>
              ) : filteredGroups.length === 0 ? (
                <div className="text-center py-8">
                  <div className="text-gray-400 mb-2">
                    <Settings className="w-12 h-12 mx-auto" />
                  </div>
                  <p className="text-gray-600">未找到匹配的分组</p>
                  <p className="text-sm text-gray-500">请调整查询条件或重置查询</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="w-16">序号</TableHead>
                        <TableHead>分组名称</TableHead>
                        <TableHead>分组描述</TableHead>
                        <TableHead>API密钥</TableHead>
                        <TableHead>MCP Server URL</TableHead>
                        <TableHead className="w-24">工具数量</TableHead>
                        <TableHead className="w-20">状态</TableHead>
                        <TableHead className="w-28">创建时间</TableHead>
                        <TableHead className="w-32">操作</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {currentGroups.map((group, index) => (
                        <TableRow key={group.id}>
                          <TableCell className="font-medium">{groupIndexOfFirstItem + index + 1}</TableCell>
                          <TableCell className="font-medium text-gray-800">{group.name}</TableCell>
                          <TableCell className="text-gray-600 max-w-xs truncate">{group.description || '-'}</TableCell>
                          <TableCell>
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
                          </TableCell>
                          <TableCell>
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
                                    title={urlCopySuccess === group.id ? "已复制完整URL" : "复制完整MCP Server URL"}
                                  >
                                    {urlCopySuccess === group.id ? (
                                      <Check className="w-4 h-4 text-green-600" />
                                    ) : (
                                      <Copy className="w-4 h-4" />
                                    )}
                                  </Button>
                                </>
                              ) : (
                                <span className="text-sm text-gray-400">分组已禁用</span>
                              )}
                            </div>
                          </TableCell>
                          <TableCell>
                            <Badge variant="secondary" className="text-xs">
                              {group.tools_count || 0} 个
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <Switch
                              checked={group.enabled}
                              onCheckedChange={(checked) => handleToggleGroup(group.id, checked)}
                              disabled={isSubmitting}
                            />
                          </TableCell>
                          <TableCell className="text-sm text-gray-600">
                            {new Date(group.created_at).toLocaleDateString()}
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center space-x-1">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => {
                                  setEditingGroup(group)
                                  setGroupForm({ name: group.name, description: group.description || '' })
                                  setIsGroupDialogOpen(true)
                                }}
                                disabled={isSubmitting}
                                className="h-8 w-8 p-0"
                              >
                                <Edit className="w-4 h-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleRegenerateApiKey(group.id)}
                                disabled={isSubmitting}
                                className="h-8 w-8 p-0"
                              >
                                <RotateCcw className="w-4 h-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleDeleteGroup(group.id)}
                                disabled={isSubmitting}
                                className="h-8 w-8 p-0 text-red-600 hover:text-red-700 hover:bg-red-50"
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}
              
              {/* 分组分页组件 */}
              {filteredGroups.length > 0 && groupTotalPages > 1 && (
                <div className="mt-6 flex justify-center">
                  <div className="flex space-x-2">
                    <Button
                      onClick={() => setGroupCurrentPage(groupCurrentPage - 1)}
                      disabled={groupCurrentPage === 1}
                      variant="outline"
                      size="sm"
                      className="px-3"
                    >
                      上一页
                    </Button>
                    
                    {Array.from({ length: groupTotalPages }, (_, i) => (
                      <Button
                        key={i}
                        onClick={() => setGroupCurrentPage(i + 1)}
                        variant={groupCurrentPage === i + 1 ? "default" : "outline"}
                        size="sm"
                        className={`px-3 ${groupCurrentPage === i + 1 ? 'bg-orange-500 hover:bg-orange-600' : ''}`}
                      >
                        {i + 1}
                      </Button>
                    ))}
                    
                    <Button
                      onClick={() => setGroupCurrentPage(groupCurrentPage + 1)}
                      disabled={groupCurrentPage === groupTotalPages}
                      variant="outline"
                      size="sm"
                      className="px-3"
                    >
                      下一页
                    </Button>
                  </div>
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
              {/* 工具查询区域 */}
              {allTools.length > 0 && (
                <div className="mb-6 rounded-lg border border-gray-200 bg-gray-50 p-4">
                  <h3 className="mb-4 text-sm font-medium text-gray-800">工具查询</h3>
                  <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                    <div>
                      <Label htmlFor="toolName" className="mb-2 block text-sm font-medium">工具名称</Label>
                      <Input
                        id="toolName"
                        value={toolSearchName}
                        onChange={(e) => setToolSearchName(e.target.value)}
                        placeholder="搜索工具名称"
                        className="w-full"
                      />
                    </div>
                    <div>
                      <Label htmlFor="toolGroup" className="mb-2 block text-sm font-medium">所属分组</Label>
                      <Select value={toolSearchGroup} onValueChange={setToolSearchGroup}>
                        <SelectTrigger className="w-full">
                          <SelectValue placeholder="选择分组" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="all">全部分组</SelectItem>
                          {allGroups.map((group) => (
                            <SelectItem key={group.id} value={group.name}>
                              {group.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <div className="mt-4 flex justify-end space-x-2">
                    <Button variant="outline" onClick={resetToolFilters}>
                      重置
                    </Button>
                    <Button className="bg-orange-500 hover:bg-orange-600" onClick={filterTools}>
                      查询
                    </Button>
                  </div>
                </div>
              )}

              {filteredTools.length === 0 && allTools.length === 0 ? (
                <div className="text-center py-8">
                  <div className="text-gray-400 mb-2">
                    <Settings className="w-12 h-12 mx-auto" />
                  </div>
                  <p className="text-gray-600">暂无MCP工具</p>
                  <p className="text-sm text-gray-500">点击上方"刷新工具列表"按钮从服务器同步工具信息</p>
                </div>
              ) : filteredTools.length === 0 ? (
                <div className="text-center py-8">
                  <div className="text-gray-400 mb-2">
                    <Settings className="w-12 h-12 mx-auto" />
                  </div>
                  <p className="text-gray-600">未找到匹配的工具</p>
                  <p className="text-sm text-gray-500">请调整查询条件或重置查询</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="w-16">序号</TableHead>
                        <TableHead>工具名称</TableHead>
                        <TableHead>所属分组</TableHead>
                        <TableHead className="w-20">版本</TableHead>
                        <TableHead>描述</TableHead>
                        <TableHead className="w-24">超时时间</TableHead>
                        <TableHead className="w-20">状态</TableHead>
                        <TableHead className="w-24">操作</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {currentTools.map((tool, index) => (
                        <TableRow key={tool.id}>
                          <TableCell className="font-medium">{toolIndexOfFirstItem + index + 1}</TableCell>
                          <TableCell className="font-medium text-gray-800">{tool.tool_name}</TableCell>
                          <TableCell>
                            <Badge variant="outline" className="text-xs">
                              {tool.group_name || '未分组'}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-sm text-gray-600">{tool.version}</TableCell>
                          <TableCell className="text-gray-600 max-w-xs truncate">{tool.description || '-'}</TableCell>
                          <TableCell className="text-sm text-gray-600">{tool.timeout_seconds}秒</TableCell>
                          <TableCell>
                            <Switch
                              checked={tool.enabled}
                              onCheckedChange={(checked) => handleToggleTool(tool.id, checked)}
                              disabled={isSubmitting}
                            />
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center space-x-1">
                              <Button 
                                variant="ghost" 
                                size="sm"
                                onClick={() => handleEditTool(tool)}
                                disabled={isSubmitting}
                                className="h-8 w-8 p-0"
                                title="编辑工具基本信息"
                              >
                                <Edit className="w-4 h-4" />
                              </Button>
                              <Button 
                                variant="ghost" 
                                size="sm"
                                onClick={() => handleConfigTool(tool)}
                                disabled={isSubmitting}
                                className="h-8 w-8 p-0"
                                title="高级配置参数"
                              >
                                <Settings className="w-4 h-4" />
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}
              
              {/* 工具分页组件 */}
              {filteredTools.length > 0 && toolTotalPages > 1 && (
                <div className="mt-6 flex justify-center">
                  <div className="flex space-x-2">
                    <Button
                      onClick={() => setToolCurrentPage(toolCurrentPage - 1)}
                      disabled={toolCurrentPage === 1}
                      variant="outline"
                      size="sm"
                      className="px-3"
                    >
                      上一页
                    </Button>
                    
                    {Array.from({ length: toolTotalPages }, (_, i) => (
                      <Button
                        key={i}
                        onClick={() => setToolCurrentPage(i + 1)}
                        variant={toolCurrentPage === i + 1 ? "default" : "outline"}
                        size="sm"
                        className={`px-3 ${toolCurrentPage === i + 1 ? 'bg-orange-500 hover:bg-orange-600' : ''}`}
                      >
                        {i + 1}
                      </Button>
                    ))}
                    
                    <Button
                      onClick={() => setToolCurrentPage(toolCurrentPage + 1)}
                      disabled={toolCurrentPage === toolTotalPages}
                      variant="outline"
                      size="sm"
                      className="px-3"
                    >
                      下一页
                    </Button>
                  </div>
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
                  {groups.map((group) => (
                    <SelectItem key={group.id} value={group.id}>
                      {group.name}
                    </SelectItem>
                  ))}
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