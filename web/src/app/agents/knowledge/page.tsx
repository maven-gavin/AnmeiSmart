'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import toast from 'react-hot-toast';
import { Database, FileUp, Plus, RefreshCw } from 'lucide-react';

import AppLayout from '@/components/layout/AppLayout';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Checkbox } from '@/components/ui/checkbox';
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
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { useAuthContext } from '@/contexts/AuthContext';
import { useAgentConfigs } from '@/hooks/useAgentConfigs';
import agentKnowledgeService from '@/service/agentKnowledgeService';
import { uploadAgentFile } from '@/service/agentFileService';
import type { AgentKnowledgeBase, AgentKnowledgeDocument } from '@/types/agentKnowledge';

const ACCEPTED_EXTENSIONS = ['.pdf', '.txt', '.md', '.docx'];

function statusBadge(status: AgentKnowledgeDocument['status']) {
  if (status === 'indexed') return 'bg-green-100 text-green-800';
  if (status === 'failed') return 'bg-red-100 text-red-800';
  return 'bg-yellow-100 text-yellow-800';
}

function statusLabel(status: AgentKnowledgeDocument['status']) {
  if (status === 'indexed') return '已索引';
  if (status === 'failed') return '失败';
  return '处理中';
}

export default function AgentKnowledgePage() {
  const { user } = useAuthContext();
  const router = useRouter();
  const { configs, isLoading: configsLoading, refreshConfigs } = useAgentConfigs();

  const [selectedAgentId, setSelectedAgentId] = useState('');
  const [knowledgeBases, setKnowledgeBases] = useState<AgentKnowledgeBase[]>([]);
  const [selectedKbId, setSelectedKbId] = useState('');
  const [documents, setDocuments] = useState<AgentKnowledgeDocument[]>([]);
  const [loadingKb, setLoadingKb] = useState(false);
  const [loadingDocs, setLoadingDocs] = useState(false);
  const [uploading, setUploading] = useState(false);

  const [showCreateKb, setShowCreateKb] = useState(false);
  const [kbName, setKbName] = useState('');
  const [kbDescription, setKbDescription] = useState('');
  const [linkToAgent, setLinkToAgent] = useState(true);
  const [creatingKb, setCreatingKb] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (user && !user.roles.includes('admin')) {
      router.push('/unauthorized');
    }
  }, [user, router]);

  const enabledConfigs = configs.filter((c) => c.enabled);

  const loadKnowledgeBases = useCallback(async (agentId: string) => {
    if (!agentId) {
      setKnowledgeBases([]);
      setSelectedKbId('');
      return;
    }
    setLoadingKb(true);
    try {
      const items = await agentKnowledgeService.listKnowledgeBases(agentId);
      setKnowledgeBases(items);
      setSelectedKbId((prev) => {
        if (prev && items.some((kb) => kb.id === prev)) return prev;
        return items[0]?.id ?? '';
      });
    } catch (err) {
      console.error(err);
      toast.error('加载知识库失败');
    } finally {
      setLoadingKb(false);
    }
  }, []);

  const loadDocuments = useCallback(async (agentId: string, kbId: string) => {
    if (!agentId || !kbId) {
      setDocuments([]);
      return;
    }
    setLoadingDocs(true);
    try {
      const items = await agentKnowledgeService.listKnowledgeDocuments(agentId, kbId);
      setDocuments(items);
    } catch (err) {
      console.error(err);
      toast.error('加载文档列表失败');
    } finally {
      setLoadingDocs(false);
    }
  }, []);

  useEffect(() => {
    if (!selectedAgentId && enabledConfigs.length > 0) {
      setSelectedAgentId(enabledConfigs[0].id);
    }
  }, [enabledConfigs, selectedAgentId]);

  useEffect(() => {
    loadKnowledgeBases(selectedAgentId);
  }, [selectedAgentId, loadKnowledgeBases]);

  useEffect(() => {
    loadDocuments(selectedAgentId, selectedKbId);
  }, [selectedAgentId, selectedKbId, loadDocuments]);

  const handleCreateKb = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedAgentId || !kbName.trim()) return;
    setCreatingKb(true);
    try {
      const kb = await agentKnowledgeService.createKnowledgeBase(selectedAgentId, {
        name: kbName.trim(),
        description: kbDescription.trim() || undefined,
        linkToAgent,
      });
      toast.success('知识库创建成功');
      setShowCreateKb(false);
      setKbName('');
      setKbDescription('');
      setLinkToAgent(true);
      await loadKnowledgeBases(selectedAgentId);
      setSelectedKbId(kb.id);
    } catch (err) {
      console.error(err);
      toast.error('创建知识库失败');
    } finally {
      setCreatingKb(false);
    }
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!file || !selectedAgentId || !selectedKbId) return;

    const ext = file.name.slice(file.name.lastIndexOf('.')).toLowerCase();
    if (!ACCEPTED_EXTENSIONS.includes(ext)) {
      toast.error(`不支持的文件类型，请上传 ${ACCEPTED_EXTENSIONS.join(' ')}`);
      return;
    }

    setUploading(true);
    try {
      const uploaded = await uploadAgentFile(selectedAgentId, file);
      await agentKnowledgeService.indexKnowledgeDocument(selectedAgentId, selectedKbId, {
        fileId: uploaded.id,
      });
      toast.success('文档已上传并开始索引');
      await loadDocuments(selectedAgentId, selectedKbId);
    } catch (err) {
      console.error(err);
      toast.error(err instanceof Error ? err.message : '上传或索引失败');
    } finally {
      setUploading(false);
    }
  };

  const selectedAgent = enabledConfigs.find((c) => c.id === selectedAgentId);
  const selectedKb = knowledgeBases.find((kb) => kb.id === selectedKbId);

  if (configsLoading && enabledConfigs.length === 0) {
    return (
      <AppLayout requiredRole={user?.currentRole}>
        <div className="flex h-[calc(100vh-4rem)] items-center justify-center">
          <div className="am-spinner h-8 w-8" />
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout requiredRole={user?.currentRole}>
      <div className="am-page">
        <div className="am-container">
          <div className="mb-6 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <h1 className="am-page-title flex items-center gap-2">
                <Database className="h-6 w-6 text-brand-primary" />
                Agent 知识库管理
              </h1>
              <p className="mt-1 text-sm text-gray-500">
                为 Agent 创建 RAG 知识库并上传文档（LlamaIndex + pgvector）
              </p>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" className="am-btn-reset" onClick={() => refreshConfigs()}>
                <RefreshCw className="mr-1 h-4 w-4" />
                刷新
              </Button>
              <Button
                className="am-btn-primary"
                disabled={!selectedAgentId}
                onClick={() => setShowCreateKb(true)}
              >
                <Plus className="mr-1 h-4 w-4" />
                新建知识库
              </Button>
            </div>
          </div>

          <div className="am-filter-bar mb-6">
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <div>
                <Label htmlFor="agent-select" className="mb-2 block text-sm font-medium">
                  关联 Agent
                </Label>
                <Select value={selectedAgentId} onValueChange={setSelectedAgentId}>
                  <SelectTrigger id="agent-select" className="am-field">
                    <SelectValue placeholder="选择 Agent 配置" />
                  </SelectTrigger>
                  <SelectContent>
                    {enabledConfigs.map((config) => (
                      <SelectItem key={config.id} value={config.id}>
                        [{config.environment}] {config.appName}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              {selectedAgent && (
                <div className="flex items-end text-sm text-gray-600">
                  <span>
                    模型：{' '}
                    <code className="am-mono rounded bg-white px-1">
                      {(selectedAgent.capabilities?.model as string) || 'gpt-4o-mini'}
                    </code>
                    {' · '}
                    RAG：{selectedAgent.capabilities?.enable_rag ? '已启用' : '未启用'}
                  </span>
                </div>
              )}
            </div>
          </div>

          {enabledConfigs.length === 0 ? (
            <div className="am-card p-8 text-center text-gray-500">
              暂无已启用的 Agent 配置，请先在「智能体配置」中创建并启用。
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
              <div className="am-card lg:col-span-1">
                <div className="border-b border-gray-200 p-4">
                  <h2 className="font-medium text-gray-900">知识库列表</h2>
                </div>
                <div className="max-h-[480px] overflow-y-auto p-2">
                  {loadingKb ? (
                    <div className="flex justify-center py-8">
                      <div className="am-spinner h-6 w-6" />
                    </div>
                  ) : knowledgeBases.length === 0 ? (
                    <p className="py-8 text-center text-sm text-gray-500">暂无知识库</p>
                  ) : (
                    knowledgeBases.map((kb) => (
                      <button
                        key={kb.id}
                        type="button"
                        onClick={() => setSelectedKbId(kb.id)}
                        className={`mb-1 w-full rounded-lg border p-3 text-left transition-colors ${
                          selectedKbId === kb.id
                            ? 'border-brand-primary bg-brand-soft'
                            : 'border-gray-200 hover:bg-gray-50'
                        }`}
                      >
                        <div className="font-medium text-gray-900">{kb.name}</div>
                        {kb.description && (
                          <div className="mt-1 line-clamp-2 text-xs text-gray-500">{kb.description}</div>
                        )}
                        <div className="mt-2 text-xs text-gray-400 am-mono">{kb.embeddingModel}</div>
                      </button>
                    ))
                  )}
                </div>
              </div>

              <div className="am-card lg:col-span-2">
                <div className="flex items-center justify-between border-b border-gray-200 p-4">
                  <div>
                    <h2 className="font-medium text-gray-900">
                      {selectedKb ? selectedKb.name : '文档列表'}
                    </h2>
                    {selectedKb && (
                      <p className="text-xs text-gray-500">
                        分块 {selectedKb.chunkSize} / 重叠 {selectedKb.chunkOverlap}
                      </p>
                    )}
                  </div>
                  <div>
                    <input
                      ref={fileInputRef}
                      type="file"
                      className="hidden"
                      accept={ACCEPTED_EXTENSIONS.join(',')}
                      onChange={handleFileSelect}
                    />
                    <Button
                      className="am-btn-primary"
                      disabled={!selectedKbId || uploading}
                      onClick={() => fileInputRef.current?.click()}
                    >
                      <FileUp className="mr-1 h-4 w-4" />
                      {uploading ? '处理中…' : '上传并索引'}
                    </Button>
                  </div>
                </div>

                {!selectedKbId ? (
                  <p className="p-8 text-center text-sm text-gray-500">请先选择或创建知识库</p>
                ) : loadingDocs ? (
                  <div className="flex justify-center py-12">
                    <div className="am-spinner h-8 w-8" />
                  </div>
                ) : documents.length === 0 ? (
                  <p className="p-8 text-center text-sm text-gray-500">
                    暂无文档，支持 {ACCEPTED_EXTENSIONS.join(' ')}
                  </p>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">
                            文档
                          </th>
                          <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">
                            状态
                          </th>
                          <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">
                            分块数
                          </th>
                          <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">
                            上传时间
                          </th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-200 bg-white">
                        {documents.map((doc) => (
                          <tr key={doc.id} className="hover:bg-gray-50">
                            <td className="px-4 py-3 text-sm text-gray-900">{doc.name}</td>
                            <td className="px-4 py-3">
                              <span
                                className={`rounded-full px-2 py-1 text-xs font-medium ${statusBadge(doc.status)}`}
                              >
                                {statusLabel(doc.status)}
                              </span>
                              {doc.errorMessage && (
                                <p className="mt-1 text-xs text-red-600">{doc.errorMessage}</p>
                              )}
                            </td>
                            <td className="px-4 py-3 text-sm text-gray-600">{doc.chunkCount}</td>
                            <td className="px-4 py-3 text-sm text-gray-500">
                              {doc.createdAt
                                ? new Date(doc.createdAt).toLocaleString('zh-CN')
                                : '-'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      <Dialog open={showCreateKb} onOpenChange={setShowCreateKb}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>新建知识库</DialogTitle>
            <DialogDescription>
              创建后将写入 pgvector 索引表，可选择自动绑定到当前 Agent。
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleCreateKb} className="space-y-4">
            <div>
              <Label htmlFor="kb-name">名称 *</Label>
              <Input
                id="kb-name"
                className="am-field mt-1"
                value={kbName}
                onChange={(e) => setKbName(e.target.value)}
                placeholder="例如：产品手册"
                required
              />
            </div>
            <div>
              <Label htmlFor="kb-desc">描述</Label>
              <Textarea
                id="kb-desc"
                className="am-field mt-1"
                value={kbDescription}
                onChange={(e) => setKbDescription(e.target.value)}
                rows={2}
              />
            </div>
            <div className="flex items-center space-x-2">
              <Checkbox
                id="link-agent"
                checked={linkToAgent}
                onCheckedChange={(v) => setLinkToAgent(v === true)}
              />
              <Label htmlFor="link-agent" className="text-sm">
                自动绑定到 Agent（启用 RAG 并设置 knowledge_base_id）
              </Label>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setShowCreateKb(false)}>
                取消
              </Button>
              <Button type="submit" className="am-btn-primary" disabled={creatingKb}>
                {creatingKb ? '创建中…' : '创建'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </AppLayout>
  );
}
