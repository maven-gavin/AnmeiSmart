'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { AIModelConfig } from '@/service/systemService';

interface AIModelConfigPanelProps {
  models: AIModelConfig[];
  defaultModelId: string;
  onAddModel: (model: AIModelConfig) => Promise<void>;
  onRemoveModel: (modelName: string) => Promise<void>;
  onToggleModel: (modelName: string) => Promise<void>;
  onUpdateDefaultModel: (modelId: string) => Promise<void>;
}

export default function AIModelConfigPanel({
  models,
  defaultModelId,
  onAddModel,
  onRemoveModel,
  onToggleModel,
  onUpdateDefaultModel
}: AIModelConfigPanelProps) {
  const [newModel, setNewModel] = useState<AIModelConfig>({
    modelName: '',
    apiKey: '',
    baseUrl: '',
    maxTokens: 2000,
    temperature: 0.7,
    enabled: true,
    provider: 'openai',
    appId: ''
  });

  const { register, handleSubmit, setValue, watch } = useForm({
    defaultValues: { defaultModelId }
  });

  const handleAddModel = async () => {
    // 基本验证
    if (!newModel.modelName || !newModel.apiKey || !newModel.baseUrl) {
      alert('请填写所有必填字段');
      return;
    }
    
    // 特定提供商验证
    if (newModel.provider === 'agent' && !newModel.appId) {
  alert('使用Agent时必须填写应用ID');
  return;
}
    
    await onAddModel(newModel);
    
    // 重置表单
    setNewModel({
      modelName: '',
      apiKey: '',
      baseUrl: '',
      maxTokens: 2000,
      temperature: 0.7,
      enabled: true,
      provider: 'openai',
      appId: ''
    });
  };

  const handleDefaultModelChange = async (data: { defaultModelId: string }) => {
    await onUpdateDefaultModel(data.defaultModelId);
  };

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow">
      <h2 className="mb-4 text-xl font-semibold text-gray-800">AI模型配置</h2>
      
      <div className="mb-6 max-h-96 overflow-y-auto pr-2">
        <h3 className="mb-3 text-lg font-medium text-gray-700">已配置模型</h3>
        
        {models.length === 0 ? (
          <p className="text-gray-500">尚未配置任何AI模型</p>
        ) : (
          <div className="space-y-4">
            {models.map((model, index) => (
              <div key={index} className="rounded-lg border border-gray-200 bg-gray-50 p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <span className={`mr-2 h-3 w-3 rounded-full ${model.enabled ? 'bg-green-500' : 'bg-red-500'}`}></span>
                    <h4 className="font-medium">{model.modelName}</h4>
                    {model.provider && (
                      <Badge variant="secondary" className="ml-2">
                        {model.provider.toUpperCase()}
                      </Badge>
                    )}
                  </div>
                  <div className="flex space-x-2">
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      onClick={() => onToggleModel(model.modelName)}
                    >
                      {model.enabled ? '停用' : '启用'}
                    </Button>
                    <Button
                      type="button"
                      size="sm"
                      variant="destructive"
                      onClick={() => onRemoveModel(model.modelName)}
                    >
                      删除
                    </Button>
                  </div>
                </div>
                
                <div className="mt-3 grid grid-cols-2 gap-4">
                  <div>
                    <span className="text-sm font-medium text-gray-500">API基础URL:</span>
                    <p className="text-sm">{model.baseUrl}</p>
                  </div>
                  <div>
                    <span className="text-sm font-medium text-gray-500">API密钥:</span>
                    <p className="text-sm">••••••••••••••••••••</p>
                  </div>
                  {model.provider === 'agent' && model.appId && (
                    <div>
                      <span className="text-sm font-medium text-gray-500">应用ID:</span>
                      <p className="text-sm">{model.appId}</p>
                    </div>
                  )}
                  <div>
                    <span className="text-sm font-medium text-gray-500">最大Token数:</span>
                    <p className="text-sm">{model.maxTokens}</p>
                  </div>
                  <div>
                    <span className="text-sm font-medium text-gray-500">温度系数:</span>
                    <p className="text-sm">{model.temperature}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      
        <h3 className="mb-3 mt-6 text-lg font-medium text-gray-700">添加新模型</h3>
        <div className="space-y-4 rounded-lg border border-gray-200 bg-white p-4">
          <div>
            <Label className="mb-1 block text-sm font-medium text-gray-700">
              AI提供商 *
            </Label>
            <Select
              value={newModel.provider}
              onValueChange={(value) => setNewModel({...newModel, provider: value})}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="openai">OpenAI</SelectItem>
                <SelectItem value="agent">Agent</SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div>
              <Label className="mb-1 block text-sm font-medium text-gray-700">
                模型名称 *
              </Label>
              <Input
                type="text"
                value={newModel.modelName}
                onChange={(e) => setNewModel({...newModel, modelName: e.target.value})}
                placeholder={newModel.provider === 'openai' ? "例如: GPT-4, GPT-3.5-turbo" : "例如: Agent-Claude"}
              />
            </div>
            
            <div>
              <Label className="mb-1 block text-sm font-medium text-gray-700">
                API密钥 *
              </Label>
              <Input
                type="password"
                value={newModel.apiKey}
                onChange={(e) => setNewModel({...newModel, apiKey: e.target.value})}
                placeholder={newModel.provider === 'openai' ? "sk-..." : "Bearer token"}
              />
            </div>
            
            <div>
              <Label className="mb-1 block text-sm font-medium text-gray-700">
                API基础URL *
              </Label>
              <Input
                type="text"
                value={newModel.baseUrl}
                onChange={(e) => setNewModel({...newModel, baseUrl: e.target.value})}
                placeholder={newModel.provider === 'openai' ? "https://api.openai-proxy.com/v1" : "http://localhost/v1"}
              />
            </div>
            
            {newModel.provider === 'agent' && (
              <div>
                <Label className="mb-1 block text-sm font-medium text-gray-700">
                  应用ID *
                </Label>
                <Input
                  type="text"
                  value={newModel.appId}
                  onChange={(e) => setNewModel({...newModel, appId: e.target.value})}
                  placeholder="例如: e15daecf-548c-47da-986c-ed37036d33ea"
                />
              </div>
            )}
            
            <div>
              <Label className="mb-1 block text-sm font-medium text-gray-700">
                最大Token数
              </Label>
              <Input
                type="number"
                value={newModel.maxTokens}
                onChange={(e) => setNewModel({...newModel, maxTokens: parseInt(e.target.value)})}
              />
            </div>
            
            <div>
              <Label className="mb-1 block text-sm font-medium text-gray-700">
                温度系数
              </Label>
              <Input
                type="number"
                step="0.1"
                min="0"
                max="2"
                value={newModel.temperature}
                onChange={(e) => setNewModel({...newModel, temperature: parseFloat(e.target.value)})}
              />
            </div>
            
            <div className="flex items-center">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={newModel.enabled}
                  onChange={(e) => setNewModel({...newModel, enabled: e.target.checked})}
                  className="h-4 w-4 rounded border-gray-300 text-orange-600 focus:ring-orange-500"
                />
                <span className="ml-2 text-sm text-gray-700">启用此模型</span>
              </label>
            </div>
          </div>
          
          <div className="flex justify-end">
            <Button
              type="button"
              onClick={handleAddModel}
              className="bg-orange-500 hover:bg-orange-600"
            >
              添加模型
            </Button>
          </div>
        </div>
      </div>
      
      <form onSubmit={handleSubmit(handleDefaultModelChange)}>
        <div className="mb-4">
          <Label className="mb-2 block text-sm font-medium text-gray-700">
            默认AI模型
          </Label>
          <Select
            value={watch('defaultModelId')}
            onValueChange={(value) => setValue('defaultModelId', value)}
          >
            <SelectTrigger>
              <SelectValue placeholder="请先添加模型" />
            </SelectTrigger>
            <SelectContent>
              {models.length > 0 ? (
                models.map((model, index) => (
                  <SelectItem key={index} value={model.modelName}>
                    {model.modelName} {!model.enabled && '(已停用)'} 
                    {model.provider && ` - ${model.provider.toUpperCase()}`}
                  </SelectItem>
                ))
              ) : (
                <SelectItem value="" disabled>请先添加模型</SelectItem>
              )}
            </SelectContent>
          </Select>
        </div>

        <div className="flex justify-end">
          <Button
            type="submit"
            className="bg-orange-500 hover:bg-orange-600"
          >
            保存默认模型
          </Button>
        </div>
      </form>
    </div>
  );
} 