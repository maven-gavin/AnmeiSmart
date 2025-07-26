'use client'

import React, { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'
import { Eye, EyeOff, Plus, Settings, Trash2, RotateCcw, Edit } from 'lucide-react'
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
// import { toast } from '@/components/ui/use-toast'
import { useMCPConfigs } from '@/hooks/useMCPConfigs'
import { MCPGroup, MCPTool } from '@/service/mcpConfigService'

export default function MCPConfigPanel() {
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
  const [isToolDialogOpen, setIsToolDialogOpen] = useState(false)
  const [editingGroup, setEditingGroup] = useState<MCPGroup | null>(null)
  const [editingTool, setEditingTool] = useState<MCPTool | null>(null)

  // 表单状态
  const [groupForm, setGroupForm] = useState({
    name: '',
    description: ''
  })

  const [toolForm, setToolForm] = useState({
    tool_name: '',
    group_id: '',
    version: '1.0.0',
    description: '',
    enabled: true,
    timeout_seconds: 30,
    config_data: '{}'
  })

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
    // 错误处理由useMCPConfigs hook统一处理
  }

  // 删除分组
  const handleDeleteGroup = async (groupId: string) => {
    if (!confirm('确定要删除此MCP分组吗？删除后无法恢复。')) {
      return
    }

    const success = await deleteGroup(groupId)
    // 错误处理由useMCPConfigs hook统一处理
  }

  // 重新生成API密钥
  const handleRegenerateApiKey = async (groupId: string) => {
    if (!confirm('确定要重新生成API密钥吗？旧密钥将立即失效。')) {
      return
    }

    const newApiKey = await regenerateApiKey(groupId)
    // 错误处理由useMCPConfigs hook统一处理
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
    <div className="space-y-6">
      {/* 错误提示 */}
      {error && (
        <Alert variant="destructive">
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
      <Alert>
        <AlertDescription>
          MCP（Model Context Protocol）配置管理：通过分组方式管理AI工具，为Dify等AI平台提供标准化的工具调用接口。
        </AlertDescription>
      </Alert>

      <Tabs defaultValue="groups" className="space-y-4">
        <TabsList>
          <TabsTrigger value="groups">工具分组管理</TabsTrigger>
          <TabsTrigger value="tools">工具配置管理</TabsTrigger>
        </TabsList>

        {/* 工具分组管理 */}
        <TabsContent value="groups" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>MCP工具分组管理</CardTitle>
                  <CardDescription>
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
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>
                        {editingGroup ? '编辑MCP分组' : '创建MCP分组'}
                      </DialogTitle>
                      <DialogDescription>
                        创建新的MCP工具分组，系统将自动生成API密钥
                      </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4">
                      <div>
                        <Label htmlFor="name">分组名称</Label>
                        <Input
                          id="name"
                          value={groupForm.name}
                          onChange={(e) => setGroupForm(prev => ({ ...prev, name: e.target.value }))}
                          placeholder="如：用户服务工具组"
                        />
                      </div>
                      <div>
                        <Label htmlFor="description">分组描述</Label>
                        <Textarea
                          id="description"
                          value={groupForm.description}
                          onChange={(e) => setGroupForm(prev => ({ ...prev, description: e.target.value }))}
                          placeholder="描述此分组包含的工具用途..."
                          rows={3}
                        />
                      </div>
                    </div>
                    <DialogFooter>
                      <Button variant="outline" onClick={() => setIsGroupDialogOpen(false)}>
                        取消
                      </Button>
                      <Button onClick={handleSaveGroup} className="bg-orange-500 hover:bg-orange-600">
                        {editingGroup ? '更新' : '创建'}
                      </Button>
                    </DialogFooter>
                  </DialogContent>
                </Dialog>
              </div>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>序号</TableHead>
                    <TableHead>分组名称</TableHead>
                    <TableHead>分组描述</TableHead>
                    <TableHead>API密钥</TableHead>
                    <TableHead>工具数量</TableHead>
                    <TableHead>启用状态</TableHead>
                    <TableHead>创建时间</TableHead>
                    <TableHead>操作</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {groups.map((group, index) => (
                    <TableRow key={group.id}>
                      <TableCell>{index + 1}</TableCell>
                      <TableCell className="font-medium">{group.name}</TableCell>
                      <TableCell>{group.description}</TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-2">
                          <code className="text-sm bg-gray-100 px-2 py-1 rounded">
                            {showApiKeys[group.id] 
                              ? group.api_key 
                              : 'mcp_key_' + '•'.repeat(20)
                            }
                          </code>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => toggleApiKeyVisibility(group.id)}
                          >
                            {showApiKeys[group.id] ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                          </Button>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="secondary">
                          {group.tools_count || 0} 个
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Switch
                          checked={group.enabled}
                          onCheckedChange={(checked) => handleToggleGroup(group.id, checked)}
                        />
                      </TableCell>
                      <TableCell>{new Date(group.created_at).toLocaleDateString()}</TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              setEditingGroup(group)
                              setGroupForm({ name: group.name, description: group.description })
                              setIsGroupDialogOpen(true)
                            }}
                          >
                            <Edit className="w-4 h-4" />
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleRegenerateApiKey(group.id)}
                          >
                            <RotateCcw className="w-4 h-4" />
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleDeleteGroup(group.id)}
                            className="text-red-600 hover:text-red-700"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 工具配置管理 */}
        <TabsContent value="tools" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>MCP工具配置管理</CardTitle>
                  <CardDescription>
                    管理各个MCP工具的配置参数和启用状态
                  </CardDescription>
                </div>
                                  <Button 
                    onClick={refreshTools}
                    disabled={isSubmitting}
                    className="bg-orange-500 hover:bg-orange-600"
                  >
                    <Settings className="w-4 h-4 mr-2" />
                    刷新工具列表
                  </Button>
              </div>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>序号</TableHead>
                    <TableHead>工具名称</TableHead>
                    <TableHead>所属分组</TableHead>
                    <TableHead>版本</TableHead>
                    <TableHead>描述</TableHead>
                    <TableHead>超时时间(秒)</TableHead>
                    <TableHead>启用状态</TableHead>
                    <TableHead>操作</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {tools.map((tool, index) => (
                    <TableRow key={tool.id}>
                      <TableCell>{index + 1}</TableCell>
                      <TableCell className="font-medium">{tool.tool_name}</TableCell>
                      <TableCell>
                        <Badge variant="outline">{tool.group_name}</Badge>
                      </TableCell>
                      <TableCell>{tool.version}</TableCell>
                      <TableCell>{tool.description}</TableCell>
                      <TableCell>{tool.timeout_seconds}</TableCell>
                      <TableCell>
                        <Switch
                          checked={tool.enabled}
                          onCheckedChange={(checked) => handleToggleTool(tool.id, checked)}
                        />
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-2">
                          <Button variant="outline" size="sm">
                            <Edit className="w-4 h-4" />
                          </Button>
                          <Button variant="outline" size="sm">
                            <Settings className="w-4 h-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
} 