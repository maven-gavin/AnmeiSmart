'use client'

import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { useRouter } from 'next/navigation'
import AppLayout from '@/components/layout/AppLayout'
import { useAuthContext } from '@/contexts/AuthContext'
import { usePermission } from '@/hooks/usePermission'
import { handleApiError } from '@/service/apiClient'
import { taskGovernanceService } from '@/service/taskGovernanceService'
import type {
  RouteTaskResponse,
  SensitiveCategory,
  TaskQueue,
  TaskQueueRotationStrategy,
  TaskRoutingRule,
  TaskRuleMatchType,
  TaskSensitiveRule,
} from '@/types/task-governance'

import toast from 'react-hot-toast'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Switch } from '@/components/ui/switch'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { RefreshCw, Plus, Trash2, Pencil, Play } from 'lucide-react'

type JsonTextState = { text: string; error?: string | null }

function safeParseJson(text: string): { ok: true; value: unknown } | { ok: false; error: string } {
  const trimmed = text.trim()
  if (!trimmed) return { ok: true, value: null }
  try {
    return { ok: true, value: JSON.parse(trimmed) }
  } catch (e) {
    return { ok: false, error: e instanceof Error ? e.message : 'JSON解析失败' }
  }
}

const DEFAULT_ROUTE_TEMPLATE_JSON = JSON.stringify(
  [
    {
      task_type: 'create_ticket',
      title: '交期核查工单',
      description: '核查交期与出货节点，并给销售可对客的反馈口径',
      priority: 'high',
      due_in_minutes: 120,
      queue_name: 'PMC队列',
    },
    { task_type: 'set_sla', title: '设置SLA：2小时内反馈', priority: 'high', due_in_minutes: 120 },
    { task_type: 'create_followup', title: '销售跟进：16:00前回复客户', priority: 'medium', due_in_minutes: 480 },
  ],
  null,
  2
)

export default function TaskGovernanceAdminPage() {
  const { user } = useAuthContext()
  const { isAdmin } = usePermission()
  const router = useRouter()

  // guard
  useEffect(() => {
    if (user && !isAdmin) {
      router.push('/unauthorized')
    }
  }, [user, isAdmin, router])

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [queues, setQueues] = useState<TaskQueue[]>([])
  const [routingRules, setRoutingRules] = useState<TaskRoutingRule[]>([])
  const [sensitiveRules, setSensitiveRules] = useState<TaskSensitiveRule[]>([])

  // dialogs
  const [queueDialogOpen, setQueueDialogOpen] = useState(false)
  const [editingQueue, setEditingQueue] = useState<TaskQueue | null>(null)
  const [queueForm, setQueueForm] = useState<{
    name: string
    scene_key: string
    description: string
    rotation_strategy: TaskQueueRotationStrategy
    config: JsonTextState
    is_active: boolean
  }>({
    name: '',
    scene_key: '',
    description: '',
    rotation_strategy: 'fixed',
    config: { text: '' },
    is_active: true,
  })

  const [ruleDialogOpen, setRuleDialogOpen] = useState(false)
  const [editingRule, setEditingRule] = useState<TaskRoutingRule | null>(null)
  const [ruleForm, setRuleForm] = useState<{
    scene_key: string
    keyword: string
    match_type: TaskRuleMatchType
    priority: number
    target: string
    task_templates: JsonTextState
    description: string
    enabled: boolean
  }>({
    scene_key: '',
    keyword: '',
    match_type: 'contains',
    priority: 100,
    target: '',
    task_templates: { text: DEFAULT_ROUTE_TEMPLATE_JSON },
    description: '',
    enabled: true,
  })

  const [sensitiveDialogOpen, setSensitiveDialogOpen] = useState(false)
  const [editingSensitive, setEditingSensitive] = useState<TaskSensitiveRule | null>(null)
  const [sensitiveForm, setSensitiveForm] = useState<{
    category: SensitiveCategory
    pattern: string
    match_type: TaskRuleMatchType
    priority: number
    suggestion_templates: JsonTextState
    description: string
    enabled: boolean
  }>({
    category: 'commitment',
    pattern: '',
    match_type: 'contains',
    priority: 100,
    suggestion_templates: { text: '' },
    description: '',
    enabled: true,
  })

  const [deleteTarget, setDeleteTarget] = useState<{ kind: 'queue' | 'routing' | 'sensitive'; id: string; title: string } | null>(null)
  const [deleteOpen, setDeleteOpen] = useState(false)
  const [deleteLoading, setDeleteLoading] = useState(false)

  // route tester
  const [routeSceneKey, setRouteSceneKey] = useState('sales_delivery')
  const [routeText, setRouteText] = useState('客户催交期：今天必须给明确交期')
  const [routeLoading, setRouteLoading] = useState(false)
  const [routeResult, setRouteResult] = useState<RouteTaskResponse | null>(null)

  const loadAll = async () => {
    try {
      setLoading(true)
      setError(null)
      const [q, rr, sr] = await Promise.all([
        taskGovernanceService.listQueues(),
        taskGovernanceService.listRoutingRules(),
        taskGovernanceService.listSensitiveRules(),
      ])
      setQueues(q)
      setRoutingRules(rr)
      setSensitiveRules(sr)
    } catch (err) {
      const msg = handleApiError(err, '加载治理配置失败')
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadAll()
  }, [])

  const openCreateQueue = () => {
    setEditingQueue(null)
    setQueueForm({
      name: '',
      scene_key: '',
      description: '',
      rotation_strategy: 'fixed',
      config: { text: '' },
      is_active: true,
    })
    setQueueDialogOpen(true)
  }

  const openEditQueue = (q: TaskQueue) => {
    setEditingQueue(q)
    setQueueForm({
      name: q.name,
      scene_key: q.scene_key,
      description: q.description ?? '',
      rotation_strategy: q.rotation_strategy,
      config: { text: q.config ? JSON.stringify(q.config, null, 2) : '' },
      is_active: q.is_active,
    })
    setQueueDialogOpen(true)
  }

  const submitQueue = async (e: FormEvent) => {
    e.preventDefault()
    const name = queueForm.name.trim()
    const scene_key = queueForm.scene_key.trim()
    if (!name) return setError('队列名称不能为空')
    if (!scene_key) return setError('场景Key不能为空')

    const parsed = safeParseJson(queueForm.config.text)
    if (!parsed.ok) {
      setQueueForm((prev) => ({ ...prev, config: { text: prev.config.text, error: parsed.error } }))
      return
    }

    try {
      if (editingQueue) {
        await taskGovernanceService.updateQueue(editingQueue.id, {
          name,
          scene_key,
          description: queueForm.description.trim() || undefined,
          rotation_strategy: queueForm.rotation_strategy,
          config: (parsed.value as any) ?? undefined,
          is_active: queueForm.is_active,
        })
        toast.success('更新队列成功')
      } else {
        await taskGovernanceService.createQueue({
          name,
          scene_key,
          description: queueForm.description.trim() || undefined,
          rotation_strategy: queueForm.rotation_strategy,
          config: (parsed.value as any) ?? undefined,
          is_active: queueForm.is_active,
        } as any)
        toast.success('创建队列成功')
      }
      setQueueDialogOpen(false)
      await loadAll()
    } catch {
      // handleApiError 已在 service 内处理
    }
  }

  const openCreateRule = () => {
    setEditingRule(null)
    setRuleForm({
      scene_key: 'sales_delivery',
      keyword: '',
      match_type: 'contains',
      priority: 100,
      target: '',
      task_templates: { text: DEFAULT_ROUTE_TEMPLATE_JSON },
      description: '',
      enabled: true,
    })
    setRuleDialogOpen(true)
  }

  const openEditRule = (r: TaskRoutingRule) => {
    setEditingRule(r)
    setRuleForm({
      scene_key: r.scene_key,
      keyword: r.keyword,
      match_type: r.match_type,
      priority: r.priority,
      target: r.target ?? '',
      task_templates: { text: r.task_templates ? JSON.stringify(r.task_templates, null, 2) : '' },
      description: r.description ?? '',
      enabled: r.enabled,
    })
    setRuleDialogOpen(true)
  }

  const submitRule = async (e: FormEvent) => {
    e.preventDefault()
    const scene_key = ruleForm.scene_key.trim()
    const keyword = ruleForm.keyword.trim()
    if (!scene_key) return setError('场景Key不能为空')
    if (!keyword) return setError('关键词不能为空')

    const parsed = safeParseJson(ruleForm.task_templates.text)
    if (!parsed.ok) {
      setRuleForm((prev) => ({ ...prev, task_templates: { text: prev.task_templates.text, error: parsed.error } }))
      return
    }
    const templates = parsed.value === null ? undefined : parsed.value

    try {
      if (editingRule) {
        await taskGovernanceService.updateRoutingRule(editingRule.id, {
          scene_key,
          keyword,
          match_type: ruleForm.match_type,
          priority: ruleForm.priority,
          target: ruleForm.target.trim() || undefined,
          task_templates: templates as any,
          description: ruleForm.description.trim() || undefined,
          enabled: ruleForm.enabled,
        })
        toast.success('更新路由规则成功')
      } else {
        await taskGovernanceService.createRoutingRule({
          scene_key,
          keyword,
          match_type: ruleForm.match_type,
          priority: ruleForm.priority,
          target: ruleForm.target.trim() || undefined,
          task_templates: templates as any,
          description: ruleForm.description.trim() || undefined,
          enabled: ruleForm.enabled,
        } as any)
        toast.success('创建路由规则成功')
      }
      setRuleDialogOpen(false)
      await loadAll()
    } catch {
      // handled in service
    }
  }

  const openCreateSensitive = () => {
    setEditingSensitive(null)
    setSensitiveForm({
      category: 'commitment',
      pattern: '',
      match_type: 'contains',
      priority: 100,
      suggestion_templates: { text: '' },
      description: '',
      enabled: true,
    })
    setSensitiveDialogOpen(true)
  }

  const openEditSensitive = (r: TaskSensitiveRule) => {
    setEditingSensitive(r)
    setSensitiveForm({
      category: r.category,
      pattern: r.pattern,
      match_type: r.match_type,
      priority: r.priority,
      suggestion_templates: { text: r.suggestion_templates ? JSON.stringify(r.suggestion_templates, null, 2) : '' },
      description: r.description ?? '',
      enabled: r.enabled,
    })
    setSensitiveDialogOpen(true)
  }

  const submitSensitive = async (e: FormEvent) => {
    e.preventDefault()
    const pattern = sensitiveForm.pattern.trim()
    if (!pattern) return setError('匹配模式不能为空')

    const parsed = safeParseJson(sensitiveForm.suggestion_templates.text)
    if (!parsed.ok) {
      setSensitiveForm((prev) => ({ ...prev, suggestion_templates: { text: prev.suggestion_templates.text, error: parsed.error } }))
      return
    }
    const templates = parsed.value === null ? undefined : parsed.value

    try {
      if (editingSensitive) {
        await taskGovernanceService.updateSensitiveRule(editingSensitive.id, {
          category: sensitiveForm.category,
          pattern,
          match_type: sensitiveForm.match_type,
          priority: sensitiveForm.priority,
          suggestion_templates: templates as any,
          description: sensitiveForm.description.trim() || undefined,
          enabled: sensitiveForm.enabled,
        })
        toast.success('更新敏感规则成功')
      } else {
        await taskGovernanceService.createSensitiveRule({
          category: sensitiveForm.category,
          pattern,
          match_type: sensitiveForm.match_type,
          priority: sensitiveForm.priority,
          suggestion_templates: templates as any,
          description: sensitiveForm.description.trim() || undefined,
          enabled: sensitiveForm.enabled,
        } as any)
        toast.success('创建敏感规则成功')
      }
      setSensitiveDialogOpen(false)
      await loadAll()
    } catch {
      // handled in service
    }
  }

  const confirmDelete = (kind: 'queue' | 'routing' | 'sensitive', id: string, title: string) => {
    setDeleteTarget({ kind, id, title })
    setDeleteOpen(true)
  }

  const doDelete = async () => {
    if (!deleteTarget) return
    setDeleteLoading(true)
    try {
      if (deleteTarget.kind === 'queue') await taskGovernanceService.deleteQueue(deleteTarget.id)
      if (deleteTarget.kind === 'routing') await taskGovernanceService.deleteRoutingRule(deleteTarget.id)
      if (deleteTarget.kind === 'sensitive') await taskGovernanceService.deleteSensitiveRule(deleteTarget.id)
      toast.success('删除成功')
      setDeleteOpen(false)
      setDeleteTarget(null)
      await loadAll()
    } finally {
      setDeleteLoading(false)
    }
  }

  const runRoute = async () => {
    const scene_key = routeSceneKey.trim()
    const text = routeText.trim()
    if (!scene_key || !text) {
      toast.error('场景Key与触发文本不能为空')
      return
    }
    setRouteLoading(true)
    try {
      const result = await taskGovernanceService.route({ scene_key, text, create_fallback_task: true })
      setRouteResult(result)
      toast.success('路由执行成功')
      await loadAll()
    } catch {
      // handled
    } finally {
      setRouteLoading(false)
    }
  }

  const stats = useMemo(() => {
    const byScene: Record<string, number> = {}
    for (const r of routingRules) byScene[r.scene_key] = (byScene[r.scene_key] || 0) + 1
    return { queues: queues.length, routingRules: routingRules.length, sensitiveRules: sensitiveRules.length, byScene }
  }, [queues.length, routingRules, sensitiveRules.length])

  return (
    <AppLayout>
      <div className="container mx-auto px-4 py-6">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">任务治理</h1>
            <p className="text-gray-600 mt-1">队列 / 路由规则 / 敏感规则 / 路由测试（不影响现有任务功能）</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={loadAll} disabled={loading} className="flex items-center gap-2">
              <RefreshCw className="h-4 w-4" />
              刷新
            </Button>
          </div>
        </div>

        {error && (
          <div className="mb-4 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            {error}
          </div>
        )}

        <div className="mb-6 grid grid-cols-1 gap-4 md:grid-cols-3">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">队列</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.queues}</div>
              <div className="text-xs text-muted-foreground">按场景自动分配的载体</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">路由规则</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.routingRules}</div>
              <div className="text-xs text-muted-foreground">场景 + 关键词 → 任务模板</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">敏感规则</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.sensitiveRules}</div>
              <div className="text-xs text-muted-foreground">少数拦截 + 安全改写建议</div>
            </CardContent>
          </Card>
        </div>

        <Tabs defaultValue="queues" className="space-y-4">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="queues">队列</TabsTrigger>
            <TabsTrigger value="routing">路由规则</TabsTrigger>
            <TabsTrigger value="sensitive">敏感规则</TabsTrigger>
            <TabsTrigger value="route">路由测试</TabsTrigger>
          </TabsList>

          <TabsContent value="queues" className="space-y-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>队列管理</CardTitle>
                <Button onClick={openCreateQueue} className="bg-orange-500 hover:bg-orange-600 flex items-center gap-2">
                  <Plus className="h-4 w-4" />
                  创建队列
                </Button>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {queues.length === 0 ? (
                    <div className="text-sm text-gray-500">暂无队列</div>
                  ) : (
                    <div className="divide-y rounded border">
                      {queues.map((q) => (
                        <div key={q.id} className="flex items-center justify-between p-3">
                          <div className="min-w-0">
                            <div className="flex items-center gap-2">
                              <div className="font-medium text-gray-900 truncate">{q.name}</div>
                              <Badge variant="outline">{q.scene_key}</Badge>
                              {!q.is_active && <Badge className="bg-gray-100 text-gray-800">停用</Badge>}
                              <Badge className="bg-blue-100 text-blue-800">{q.rotation_strategy}</Badge>
                            </div>
                            {q.description && <div className="text-sm text-gray-600 mt-1 line-clamp-1">{q.description}</div>}
                          </div>
                          <div className="flex gap-2">
                            <Button variant="outline" size="sm" onClick={() => openEditQueue(q)} className="flex items-center gap-1">
                              <Pencil className="h-3 w-3" />
                              编辑
                            </Button>
                            <Button variant="outline" size="sm" onClick={() => confirmDelete('queue', q.id, q.name)} className="flex items-center gap-1">
                              <Trash2 className="h-3 w-3" />
                              删除
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="routing" className="space-y-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>路由规则</CardTitle>
                <Button onClick={openCreateRule} className="bg-orange-500 hover:bg-orange-600 flex items-center gap-2">
                  <Plus className="h-4 w-4" />
                  创建规则
                </Button>
              </CardHeader>
              <CardContent>
                {routingRules.length === 0 ? (
                  <div className="text-sm text-gray-500">暂无路由规则</div>
                ) : (
                  <div className="divide-y rounded border">
                    {routingRules.map((r) => (
                      <div key={r.id} className="flex items-center justify-between p-3">
                        <div className="min-w-0">
                          <div className="flex flex-wrap items-center gap-2">
                            <Badge variant="outline">{r.scene_key}</Badge>
                            <Badge className="bg-green-100 text-green-800">{r.match_type}</Badge>
                            <Badge className="bg-gray-100 text-gray-800">P{r.priority}</Badge>
                            {!r.enabled && <Badge className="bg-gray-100 text-gray-800">停用</Badge>}
                            <div className="font-medium text-gray-900 truncate">关键词：{r.keyword}</div>
                          </div>
                          <div className="text-sm text-gray-600 mt-1">
                            模板：{Array.isArray(r.task_templates) ? r.task_templates.length : 0} 条
                            {r.description ? ` · ${r.description}` : ''}
                          </div>
                        </div>
                        <div className="flex gap-2">
                          <Button variant="outline" size="sm" onClick={() => openEditRule(r)} className="flex items-center gap-1">
                            <Pencil className="h-3 w-3" />
                            编辑
                          </Button>
                          <Button variant="outline" size="sm" onClick={() => confirmDelete('routing', r.id, `${r.scene_key}:${r.keyword}`)} className="flex items-center gap-1">
                            <Trash2 className="h-3 w-3" />
                            删除
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="sensitive" className="space-y-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>敏感规则</CardTitle>
                <Button onClick={openCreateSensitive} className="bg-orange-500 hover:bg-orange-600 flex items-center gap-2">
                  <Plus className="h-4 w-4" />
                  创建规则
                </Button>
              </CardHeader>
              <CardContent>
                {sensitiveRules.length === 0 ? (
                  <div className="text-sm text-gray-500">暂无敏感规则</div>
                ) : (
                  <div className="divide-y rounded border">
                    {sensitiveRules.map((r) => (
                      <div key={r.id} className="flex items-center justify-between p-3">
                        <div className="min-w-0">
                          <div className="flex flex-wrap items-center gap-2">
                            <Badge variant="outline">{r.category}</Badge>
                            <Badge className="bg-green-100 text-green-800">{r.match_type}</Badge>
                            <Badge className="bg-gray-100 text-gray-800">P{r.priority}</Badge>
                            {!r.enabled && <Badge className="bg-gray-100 text-gray-800">停用</Badge>}
                            <div className="font-medium text-gray-900 truncate">模式：{r.pattern}</div>
                          </div>
                          <div className="text-sm text-gray-600 mt-1">
                            建议：{Array.isArray(r.suggestion_templates) ? r.suggestion_templates.length : 0} 条
                            {r.description ? ` · ${r.description}` : ''}
                          </div>
                        </div>
                        <div className="flex gap-2">
                          <Button variant="outline" size="sm" onClick={() => openEditSensitive(r)} className="flex items-center gap-1">
                            <Pencil className="h-3 w-3" />
                            编辑
                          </Button>
                          <Button variant="outline" size="sm" onClick={() => confirmDelete('sensitive', r.id, `${r.category}:${r.pattern}`)} className="flex items-center gap-1">
                            <Trash2 className="h-3 w-3" />
                            删除
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="route" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>路由测试</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  <div>
                    <Label htmlFor="scene_key">场景Key</Label>
                    <Input id="scene_key" value={routeSceneKey} onChange={(e) => setRouteSceneKey(e.target.value)} placeholder="例如 sales_delivery" />
                  </div>
                  <div className="flex items-end justify-end">
                    <Button onClick={runRoute} disabled={routeLoading} className="bg-orange-500 hover:bg-orange-600 flex items-center gap-2">
                      <Play className="h-4 w-4" />
                      {routeLoading ? '执行中...' : '执行路由'}
                    </Button>
                  </div>
                </div>
                <div>
                  <Label htmlFor="route_text">触发文本</Label>
                  <Textarea id="route_text" rows={4} value={routeText} onChange={(e) => setRouteText(e.target.value)} placeholder="输入一段对话/消息文本" />
                </div>

                {routeResult && (
                  <div className="rounded border p-3 space-y-3">
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge className="bg-blue-100 text-blue-800">{routeResult.route_type}</Badge>
                      {routeResult.matched_rule_id && <Badge variant="outline">rule: {routeResult.matched_rule_id}</Badge>}
                      {routeResult.matched_sensitive_rule_id && <Badge variant="outline">sensitive: {routeResult.matched_sensitive_rule_id}</Badge>}
                      {routeResult.sensitive_category && <Badge className="bg-red-100 text-red-800">{routeResult.sensitive_category}</Badge>}
                      <Badge variant="outline">created: {routeResult.created_tasks.length}</Badge>
                    </div>

                    {routeResult.suggestions && routeResult.suggestions.length > 0 && (
                      <div>
                        <div className="text-sm font-medium mb-2">安全改写建议</div>
                        <div className="space-y-2">
                          {routeResult.suggestions.map((s, idx) => (
                            <div key={idx} className="rounded bg-gray-50 p-2 text-sm">
                              <pre className="whitespace-pre-wrap">{JSON.stringify(s, null, 2)}</pre>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {routeResult.created_tasks.length > 0 && (
                      <div>
                        <div className="text-sm font-medium mb-2">已创建任务</div>
                        <div className="divide-y rounded border">
                          {routeResult.created_tasks.map((t) => (
                            <div key={t.id} className="p-2 flex items-center justify-between">
                              <div className="min-w-0">
                                <div className="font-medium text-gray-900 truncate">{t.title}</div>
                                <div className="text-xs text-gray-600 mt-1">
                                  {t.task_type} · {t.status} · {t.priority}
                                </div>
                              </div>
                              <Badge variant="outline" className="font-mono text-xs">{t.id}</Badge>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Queue dialog */}
        <Dialog open={queueDialogOpen} onOpenChange={setQueueDialogOpen}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>{editingQueue ? '编辑队列' : '创建队列'}</DialogTitle>
            </DialogHeader>
            <form onSubmit={submitQueue} className="space-y-4">
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div>
                  <Label>队列名称</Label>
                  <Input value={queueForm.name} onChange={(e) => setQueueForm((p) => ({ ...p, name: e.target.value }))} placeholder="例如 PMC队列" />
                </div>
                <div>
                  <Label>场景Key</Label>
                  <Input value={queueForm.scene_key} onChange={(e) => setQueueForm((p) => ({ ...p, scene_key: e.target.value }))} placeholder="例如 sales_delivery" />
                </div>
              </div>
              <div>
                <Label>描述</Label>
                <Textarea value={queueForm.description} onChange={(e) => setQueueForm((p) => ({ ...p, description: e.target.value }))} rows={3} />
              </div>
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div>
                  <Label>分配策略</Label>
                  <Select
                    value={queueForm.rotation_strategy}
                    onValueChange={(v) => setQueueForm((p) => ({ ...p, rotation_strategy: v as TaskQueueRotationStrategy }))}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="选择策略" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="fixed">fixed（固定负责人）</SelectItem>
                      <SelectItem value="round_robin">round_robin（轮值）</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex items-end justify-between rounded border p-3">
                  <div>
                    <div className="text-sm font-medium">启用</div>
                    <div className="text-xs text-gray-500">停用后不会参与自动分配</div>
                  </div>
                  <Switch checked={queueForm.is_active} onCheckedChange={(v) => setQueueForm((p) => ({ ...p, is_active: v }))} />
                </div>
              </div>
              <div>
                <Label>config（JSON，可选）</Label>
                <Textarea
                  value={queueForm.config.text}
                  onChange={(e) => setQueueForm((p) => ({ ...p, config: { text: e.target.value, error: null } }))}
                  rows={6}
                  placeholder='例如：{"assignee_user_id":"usr_xxx"}'
                />
                {queueForm.config.error && <div className="text-sm text-red-600 mt-1">{queueForm.config.error}</div>}
              </div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setQueueDialogOpen(false)}>取消</Button>
                <Button type="submit" className="bg-orange-500 hover:bg-orange-600">保存</Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>

        {/* Routing rule dialog */}
        <Dialog open={ruleDialogOpen} onOpenChange={setRuleDialogOpen}>
          <DialogContent className="max-w-3xl">
            <DialogHeader>
              <DialogTitle>{editingRule ? '编辑路由规则' : '创建路由规则'}</DialogTitle>
            </DialogHeader>
            <form onSubmit={submitRule} className="space-y-4">
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div>
                  <Label>场景Key</Label>
                  <Input value={ruleForm.scene_key} onChange={(e) => setRuleForm((p) => ({ ...p, scene_key: e.target.value }))} />
                </div>
                <div>
                  <Label>关键词</Label>
                  <Input value={ruleForm.keyword} onChange={(e) => setRuleForm((p) => ({ ...p, keyword: e.target.value }))} placeholder="例如 交期/催货/延误" />
                </div>
              </div>
              <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                <div>
                  <Label>匹配类型</Label>
                  <Select value={ruleForm.match_type} onValueChange={(v) => setRuleForm((p) => ({ ...p, match_type: v as TaskRuleMatchType }))}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="contains">contains</SelectItem>
                      <SelectItem value="regex">regex</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>优先级（越小越优先）</Label>
                  <Input
                    type="number"
                    value={ruleForm.priority}
                    onChange={(e) => setRuleForm((p) => ({ ...p, priority: Number(e.target.value || 0) }))}
                  />
                </div>
                <div className="flex items-end justify-between rounded border p-3">
                  <div>
                    <div className="text-sm font-medium">启用</div>
                    <div className="text-xs text-gray-500">停用后不参与匹配</div>
                  </div>
                  <Switch checked={ruleForm.enabled} onCheckedChange={(v) => setRuleForm((p) => ({ ...p, enabled: v }))} />
                </div>
              </div>
              <div>
                <Label>描述（可选）</Label>
                <Input value={ruleForm.description} onChange={(e) => setRuleForm((p) => ({ ...p, description: e.target.value }))} />
              </div>
              <div>
                <Label>任务模板（JSON数组）</Label>
                <Textarea
                  value={ruleForm.task_templates.text}
                  onChange={(e) => setRuleForm((p) => ({ ...p, task_templates: { text: e.target.value, error: null } }))}
                  rows={10}
                />
                {ruleForm.task_templates.error && <div className="text-sm text-red-600 mt-1">{ruleForm.task_templates.error}</div>}
              </div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setRuleDialogOpen(false)}>取消</Button>
                <Button type="submit" className="bg-orange-500 hover:bg-orange-600">保存</Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>

        {/* Sensitive rule dialog */}
        <Dialog open={sensitiveDialogOpen} onOpenChange={setSensitiveDialogOpen}>
          <DialogContent className="max-w-3xl">
            <DialogHeader>
              <DialogTitle>{editingSensitive ? '编辑敏感规则' : '创建敏感规则'}</DialogTitle>
            </DialogHeader>
            <form onSubmit={submitSensitive} className="space-y-4">
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div>
                  <Label>分类</Label>
                  <Select value={sensitiveForm.category} onValueChange={(v) => setSensitiveForm((p) => ({ ...p, category: v as SensitiveCategory }))}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="pricing">pricing（价格）</SelectItem>
                      <SelectItem value="commitment">commitment（承诺）</SelectItem>
                      <SelectItem value="confidential">confidential（保密）</SelectItem>
                      <SelectItem value="destructive">destructive（破坏性动作）</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>匹配模式</Label>
                  <Input value={sensitiveForm.pattern} onChange={(e) => setSensitiveForm((p) => ({ ...p, pattern: e.target.value }))} placeholder="例如 保证/报价/图纸/删除" />
                </div>
              </div>
              <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                <div>
                  <Label>匹配类型</Label>
                  <Select value={sensitiveForm.match_type} onValueChange={(v) => setSensitiveForm((p) => ({ ...p, match_type: v as TaskRuleMatchType }))}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="contains">contains</SelectItem>
                      <SelectItem value="regex">regex</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>优先级（越小越优先）</Label>
                  <Input
                    type="number"
                    value={sensitiveForm.priority}
                    onChange={(e) => setSensitiveForm((p) => ({ ...p, priority: Number(e.target.value || 0) }))}
                  />
                </div>
                <div className="flex items-end justify-between rounded border p-3">
                  <div>
                    <div className="text-sm font-medium">启用</div>
                    <div className="text-xs text-gray-500">停用后不参与拦截</div>
                  </div>
                  <Switch checked={sensitiveForm.enabled} onCheckedChange={(v) => setSensitiveForm((p) => ({ ...p, enabled: v }))} />
                </div>
              </div>
              <div>
                <Label>描述（可选）</Label>
                <Input value={sensitiveForm.description} onChange={(e) => setSensitiveForm((p) => ({ ...p, description: e.target.value }))} />
              </div>
              <div>
                <Label>安全改写建议模板（JSON数组，可选）</Label>
                <Textarea
                  value={sensitiveForm.suggestion_templates.text}
                  onChange={(e) => setSensitiveForm((p) => ({ ...p, suggestion_templates: { text: e.target.value, error: null } }))}
                  rows={10}
                />
                {sensitiveForm.suggestion_templates.error && <div className="text-sm text-red-600 mt-1">{sensitiveForm.suggestion_templates.error}</div>}
              </div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setSensitiveDialogOpen(false)}>取消</Button>
                <Button type="submit" className="bg-orange-500 hover:bg-orange-600">保存</Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>

        {/* Delete confirm */}
        <AlertDialog open={deleteOpen} onOpenChange={setDeleteOpen}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>确认删除？</AlertDialogTitle>
              <AlertDialogDescription>
                将删除：{deleteTarget?.title}
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel disabled={deleteLoading}>取消</AlertDialogCancel>
              <AlertDialogAction onClick={doDelete} disabled={deleteLoading}>
                {deleteLoading ? '删除中...' : '确认删除'}
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    </AppLayout>
  )
}


