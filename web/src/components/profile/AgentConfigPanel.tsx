'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { 
  Plus, 
  Settings, 
  Trash2, 
  Bot, 
  ArrowUp, 
  ArrowDown,
  Check,
  X
} from 'lucide-react';
import toast from 'react-hot-toast';

interface AgentConfig {
  id: string;
  appName: string;
  appId: string;
  environment: string;
  agentType?: string;
  capabilities?: string[];
  description?: string;
  enabled: boolean;
}

interface DigitalHumanAgentConfig {
  id: string;
  digitalHumanId: string;
  agentConfigId: string;
  priority: number;
  isActive: boolean;
  scenarios?: string[];
  contextPrompt?: string;
  agentConfig: AgentConfig;
}

interface AgentConfigPanelProps {
  digitalHumanId: string;
  onBack: () => void;
}

export default function AgentConfigPanel({
  digitalHumanId,
  onBack
}: AgentConfigPanelProps) {
  const [digitalHumanAgents, setDigitalHumanAgents] = useState<DigitalHumanAgentConfig[]>([]);
  const [availableAgents, setAvailableAgents] = useState<AgentConfig[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [editingAgent, setEditingAgent] = useState<DigitalHumanAgentConfig | null>(null);
  
  // 表单状态
  const [selectedAgentId, setSelectedAgentId] = useState('');
  const [priority, setPriority] = useState(1);
  const [scenarios, setScenarios] = useState<string[]>([]);
  const [contextPrompt, setContextPrompt] = useState('');
  const [newScenario, setNewScenario] = useState('');

  useEffect(() => {
    loadData();
  }, [digitalHumanId]);

  const loadData = async () => {
    setIsLoading(true);
    try {
      // 加载数字人的智能体配置
      const dhAgentsResponse = await fetch(`/api/digital-humans/${digitalHumanId}/agents`);
      const dhAgentsData = await dhAgentsResponse.json();
      setDigitalHumanAgents(dhAgentsData.data || []);

      // 加载可用的智能体配置
      const agentsResponse = await fetch('/api/agent-configs');
      const agentsData = await agentsResponse.json();
      setAvailableAgents(agentsData.data || []);
    } catch (error) {
      console.error('加载数据失败:', error);
      toast.error('加载智能体配置失败');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddAgent = async () => {
    if (!selectedAgentId) {
      toast.error('请选择一个智能体');
      return;
    }

    try {
      const response = await fetch(`/api/digital-humans/${digitalHumanId}/agents`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          agentConfigId: selectedAgentId,
          priority,
          scenarios,
          contextPrompt,
          isActive: true
        }),
      });

      if (response.ok) {
        toast.success('智能体添加成功');
        setAddDialogOpen(false);
        resetForm();
        loadData();
      } else {
        throw new Error('添加失败');
      }
    } catch (error) {
      console.error('添加智能体失败:', error);
      toast.error('添加智能体失败');
    }
  };

  const handleUpdateAgent = async (agentConfig: DigitalHumanAgentConfig) => {
    try {
      const response = await fetch(`/api/digital-humans/${digitalHumanId}/agents/${agentConfig.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          priority: agentConfig.priority,
          isActive: agentConfig.isActive,
          scenarios: agentConfig.scenarios,
          contextPrompt: agentConfig.contextPrompt
        }),
      });

      if (response.ok) {
        toast.success('智能体配置更新成功');
        loadData();
      } else {
        throw new Error('更新失败');
      }
    } catch (error) {
      console.error('更新智能体配置失败:', error);
      toast.error('更新智能体配置失败');
    }
  };

  const handleRemoveAgent = async (agentId: string) => {
    try {
      const response = await fetch(`/api/digital-humans/${digitalHumanId}/agents/${agentId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        toast.success('智能体移除成功');
        loadData();
      } else {
        throw new Error('移除失败');
      }
    } catch (error) {
      console.error('移除智能体失败:', error);
      toast.error('移除智能体失败');
    }
  };

  const handlePriorityChange = async (agentId: string, newPriority: number) => {
    const agent = digitalHumanAgents.find(a => a.id === agentId);
    if (agent) {
      await handleUpdateAgent({ ...agent, priority: newPriority });
    }
  };

  const handleToggleActive = async (agentId: string) => {
    const agent = digitalHumanAgents.find(a => a.id === agentId);
    if (agent) {
      await handleUpdateAgent({ ...agent, isActive: !agent.isActive });
    }
  };

  const resetForm = () => {
    setSelectedAgentId('');
    setPriority(1);
    setScenarios([]);
    setContextPrompt('');
    setNewScenario('');
    setEditingAgent(null);
  };

  const addScenario = () => {
    if (newScenario.trim() && !scenarios.includes(newScenario.trim())) {
      setScenarios([...scenarios, newScenario.trim()]);
      setNewScenario('');
    }
  };

  const removeScenario = (scenario: string) => {
    setScenarios(scenarios.filter(s => s !== scenario));
  };

  const getAvailableAgents = () => {
    const configuredAgentIds = digitalHumanAgents.map(dha => dha.agentConfigId);
    return availableAgents.filter(agent => !configuredAgentIds.includes(agent.id));
  };

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="w-8 h-8 border-2 border-orange-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-gray-600">加载智能体配置...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* 头部操作 */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">智能体配置</h3>
          <p className="text-gray-600 mt-1">为数字人配置智能体能力，按优先级调用</p>
        </div>
        
        <Dialog open={addDialogOpen} onOpenChange={setAddDialogOpen}>
          <DialogTrigger asChild>
            <Button className="flex items-center space-x-2">
              <Plus className="h-4 w-4" />
              <span>添加智能体</span>
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>添加智能体</DialogTitle>
            </DialogHeader>
            
            <div className="space-y-4">
              <div>
                <Label htmlFor="agent-select">选择智能体 *</Label>
                <Select value={selectedAgentId} onValueChange={setSelectedAgentId}>
                  <SelectTrigger>
                    <SelectValue placeholder="选择一个智能体" />
                  </SelectTrigger>
                  <SelectContent>
                    {getAvailableAgents().map(agent => (
                      <SelectItem key={agent.id} value={agent.id}>
                        <div>
                          <div className="font-medium">{agent.appName}</div>
                          <div className="text-sm text-gray-500">{agent.description}</div>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label htmlFor="priority">优先级</Label>
                <Input
                  id="priority"
                  type="number"
                  min="1"
                  value={priority}
                  onChange={(e) => setPriority(parseInt(e.target.value) || 1)}
                  placeholder="数字越小优先级越高"
                />
              </div>

              <div>
                <Label htmlFor="scenarios">适用场景</Label>
                <div className="space-y-2">
                  <div className="flex space-x-2">
                    <Input
                      value={newScenario}
                      onChange={(e) => setNewScenario(e.target.value)}
                      placeholder="输入场景名称"
                      onKeyPress={(e) => e.key === 'Enter' && addScenario()}
                    />
                    <Button type="button" onClick={addScenario} size="sm">
                      添加
                    </Button>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {scenarios.map(scenario => (
                      <Badge key={scenario} variant="secondary" className="flex items-center space-x-1">
                        <span>{scenario}</span>
                        <X 
                          className="h-3 w-3 cursor-pointer hover:text-red-500" 
                          onClick={() => removeScenario(scenario)}
                        />
                      </Badge>
                    ))}
                  </div>
                </div>
              </div>

              <div>
                <Label htmlFor="context-prompt">上下文提示词</Label>
                <Textarea
                  id="context-prompt"
                  value={contextPrompt}
                  onChange={(e) => setContextPrompt(e.target.value)}
                  placeholder="为这个智能体设置特定的上下文提示词"
                  rows={3}
                />
              </div>

              <div className="flex justify-end space-x-2 pt-4">
                <Button variant="outline" onClick={() => setAddDialogOpen(false)}>
                  取消
                </Button>
                <Button onClick={handleAddAgent}>
                  添加智能体
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* 智能体列表 */}
      <div className="space-y-4">
        {digitalHumanAgents.length === 0 ? (
          <div className="text-center py-12">
            <Bot className="h-16 w-16 mx-auto text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">还没有配置智能体</h3>
            <p className="text-gray-500 mb-6">为数字人添加智能体来提供AI能力</p>
            <Button onClick={() => setAddDialogOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              添加第一个智能体
            </Button>
          </div>
        ) : (
          digitalHumanAgents
            .sort((a, b) => a.priority - b.priority)
            .map((agentConfig, index) => (
              <div
                key={agentConfig.id}
                className={`border rounded-lg p-4 ${!agentConfig.isActive ? 'opacity-60' : ''}`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="flex items-center space-x-2">
                      <span className="w-8 h-8 bg-orange-100 text-orange-600 rounded-full flex items-center justify-center text-sm font-medium">
                        {agentConfig.priority}
                      </span>
                      <div>
                        <h4 className="font-semibold text-gray-900">
                          {agentConfig.agentConfig.appName}
                        </h4>
                        <p className="text-sm text-gray-600">
                          {agentConfig.agentConfig.description}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    {/* 优先级调整 */}
                    <div className="flex flex-col space-y-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handlePriorityChange(agentConfig.id, agentConfig.priority - 1)}
                        disabled={index === 0}
                        className="h-6 w-6 p-0"
                      >
                        <ArrowUp className="h-3 w-3" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handlePriorityChange(agentConfig.id, agentConfig.priority + 1)}
                        disabled={index === digitalHumanAgents.length - 1}
                        className="h-6 w-6 p-0"
                      >
                        <ArrowDown className="h-3 w-3" />
                      </Button>
                    </div>

                    {/* 启用/停用 */}
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleToggleActive(agentConfig.id)}
                      className={agentConfig.isActive ? 'text-green-600' : 'text-gray-400'}
                    >
                      {agentConfig.isActive ? <Check className="h-4 w-4" /> : <X className="h-4 w-4" />}
                    </Button>

                    {/* 编辑 */}
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setEditingAgent(agentConfig)}
                    >
                      <Settings className="h-4 w-4" />
                    </Button>

                    {/* 删除 */}
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleRemoveAgent(agentConfig.id)}
                      className="text-red-600 hover:text-red-700"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>

                {/* 智能体详细信息 */}
                <div className="mt-4 space-y-2">
                  <div className="flex items-center space-x-4 text-sm text-gray-600">
                    <span>环境: {agentConfig.agentConfig.environment}</span>
                    <span>应用ID: {agentConfig.agentConfig.appId}</span>
                    <Badge variant={agentConfig.isActive ? 'default' : 'secondary'}>
                      {agentConfig.isActive ? '启用' : '停用'}
                    </Badge>
                  </div>

                  {agentConfig.scenarios && agentConfig.scenarios.length > 0 && (
                    <div>
                      <span className="text-sm text-gray-500">适用场景: </span>
                      <div className="inline-flex flex-wrap gap-1">
                        {agentConfig.scenarios.map(scenario => (
                          <Badge key={scenario} variant="outline" className="text-xs">
                            {scenario}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {agentConfig.contextPrompt && (
                    <div>
                      <span className="text-sm text-gray-500">上下文: </span>
                      <p className="text-sm text-gray-700 mt-1 bg-gray-50 p-2 rounded">
                        {agentConfig.contextPrompt}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            ))
        )}
      </div>
    </div>
  );
}
