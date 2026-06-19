/**
 * Agent 知识库（RAG）API
 */

import { apiClient } from './apiClient';
import type {
  AgentKnowledgeBase,
  AgentKnowledgeDocument,
  KnowledgeBaseCreatePayload,
  KnowledgeDocumentIndexPayload,
} from '@/types/agentKnowledge';

const mapKb = (raw: Record<string, unknown>): AgentKnowledgeBase => ({
  id: raw.id as string,
  agentConfigId: (raw.agent_config_id ?? raw.agentConfigId) as string,
  name: raw.name as string,
  description: (raw.description as string) || undefined,
  embeddingModel: (raw.embedding_model ?? raw.embeddingModel) as string,
  chunkSize: (raw.chunk_size ?? raw.chunkSize) as number,
  chunkOverlap: (raw.chunk_overlap ?? raw.chunkOverlap) as number,
  enabled: Boolean(raw.enabled),
  indexTableName: (raw.index_table_name ?? raw.indexTableName) as string,
  createdAt: (raw.created_at ?? raw.createdAt) as string | undefined,
});

const mapDoc = (raw: Record<string, unknown>): AgentKnowledgeDocument => ({
  id: raw.id as string,
  knowledgeBaseId: (raw.knowledge_base_id ?? raw.knowledgeBaseId) as string,
  fileId: (raw.file_id ?? raw.fileId) as string | undefined,
  name: raw.name as string,
  status: raw.status as AgentKnowledgeDocument['status'],
  chunkCount: (raw.chunk_count ?? raw.chunkCount ?? 0) as number,
  errorMessage: (raw.error_message ?? raw.errorMessage) as string | undefined,
  createdAt: (raw.created_at ?? raw.createdAt) as string | undefined,
});

export async function listKnowledgeBases(agentConfigId: string): Promise<AgentKnowledgeBase[]> {
  const response = await apiClient.get<{ items: Record<string, unknown>[] }>(
    `/agent/${agentConfigId}/knowledge-bases`,
  );
  const items = response.data?.items ?? [];
  return Array.isArray(items) ? items.map(mapKb) : [];
}

export async function createKnowledgeBase(
  agentConfigId: string,
  payload: KnowledgeBaseCreatePayload,
): Promise<AgentKnowledgeBase> {
  const response = await apiClient.post<Record<string, unknown>>(
    `/agent/${agentConfigId}/knowledge-bases`,
    {
      body: {
        name: payload.name,
        description: payload.description,
        link_to_agent: payload.linkToAgent ?? true,
      },
    },
  );
  const data = response.data as Record<string, unknown>;
  return mapKb(data);
}

export async function listKnowledgeDocuments(
  agentConfigId: string,
  knowledgeBaseId: string,
): Promise<AgentKnowledgeDocument[]> {
  const response = await apiClient.get<{ items: Record<string, unknown>[] }>(
    `/agent/${agentConfigId}/knowledge-bases/${knowledgeBaseId}/documents`,
  );
  const items = response.data?.items ?? [];
  return Array.isArray(items) ? items.map(mapDoc) : [];
}

export async function indexKnowledgeDocument(
  agentConfigId: string,
  knowledgeBaseId: string,
  payload: KnowledgeDocumentIndexPayload,
): Promise<AgentKnowledgeDocument> {
  const response = await apiClient.post<{ document: Record<string, unknown> }>(
    `/agent/${agentConfigId}/knowledge-bases/${knowledgeBaseId}/documents`,
    { body: { file_id: payload.fileId } },
  );
  const doc = response.data?.document;
  return mapDoc(doc as Record<string, unknown>);
}

const agentKnowledgeService = {
  listKnowledgeBases,
  createKnowledgeBase,
  listKnowledgeDocuments,
  indexKnowledgeDocument,
};

export default agentKnowledgeService;
