'use client'

import React, { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'
import { Eye, EyeOff, Plus, Settings, Trash2, RotateCcw, Edit, RefreshCw } from 'lucide-react'
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
    updateTool,
    refreshTools,
    clearError
  } = useMCPConfigs()

  const [showApiKeys, setShowApiKeys] = useState<Record<string, boolean>>({})
  const [isGroupDialogOpen, setIsGroupDialogOpen] = useState(false)
  const [editingGroup, setEditingGroup] = useState<MCPGroup | null>(null)

  // 表单状态
  const [groupForm, setGroupForm] = useState({
    name: '',
    description: ''
  })

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

  // 显示/隐藏API密钥
  const toggleApiKeyVisibility = (groupId: string) => {
    setShowApiKeys(prev => ({
      ...prev,
      [groupId]: !prev[groupId]
    }))
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
          MCP（Model Context Protocol）是一个开放标准协议，为AI平台提供标准化的工具调用接口。通过分组管理可以精确控制不同用户的工具访问权限。
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
                    管理MCP工具分组，每个分组拥有独立的API密钥用于权限控制
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
              {groups.length === 0 ? (
                <div className="text-center py-8">
                  <div className="text-gray-400 mb-2">
                    <Settings className="w-12 h-12 mx-auto" />
                  </div>
                  <p className="text-gray-600">暂无MCP分组</p>
                  <p className="text-sm text-gray-500">点击上方"添加分组"按钮创建第一个工具分组</p>
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
                        <TableHead className="w-24">工具数量</TableHead>
                        <TableHead className="w-20">状态</TableHead>
                        <TableHead className="w-28">创建时间</TableHead>
                        <TableHead className="w-32">操作</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {groups.map((group, index) => (
                        <TableRow key={group.id}>
                          <TableCell className="font-medium">{index + 1}</TableCell>
                          <TableCell className="font-medium text-gray-800">{group.name}</TableCell>
                          <TableCell className="text-gray-600 max-w-xs truncate">{group.description || '-'}</TableCell>
                          <TableCell>
                            <div className="flex items-center space-x-2">
                              <code className="text-xs bg-gray-50 border px-2 py-1 rounded font-mono">
                                {showApiKeys[group.id] 
                                  ? group.api_key_preview 
                                  : 'mcp_key_' + '•'.repeat(20)
                                }
                              </code>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => toggleApiKeyVisibility(group.id)}
                                className="h-8 w-8 p-0"
                              >
                                {showApiKeys[group.id] ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                              </Button>
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
              {tools.length === 0 ? (
                <div className="text-center py-8">
                  <div className="text-gray-400 mb-2">
                    <Settings className="w-12 h-12 mx-auto" />
                  </div>
                  <p className="text-gray-600">暂无MCP工具</p>
                  <p className="text-sm text-gray-500">点击上方"刷新工具列表"按钮从服务器同步工具信息</p>
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
                      {tools.map((tool, index) => (
                        <TableRow key={tool.id}>
                          <TableCell className="font-medium">{index + 1}</TableCell>
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
                                disabled={isSubmitting}
                                className="h-8 w-8 p-0"
                              >
                                <Edit className="w-4 h-4" />
                              </Button>
                              <Button 
                                variant="ghost" 
                                size="sm"
                                disabled={isSubmitting}
                                className="h-8 w-8 p-0"
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
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

// 默认导出
export default MCPConfigPanel 