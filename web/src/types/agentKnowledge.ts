/**
 * Agent 知识库（RAG）类型
 */

export interface AgentKnowledgeBase {
  id: string;
  agentConfigId: string;
  name: string;
  description?: string;
  embeddingModel: string;
  chunkSize: number;
  chunkOverlap: number;
  enabled: boolean;
  indexTableName: string;
  createdAt?: string;
}

export interface AgentKnowledgeDocument {
  id: string;
  knowledgeBaseId: string;
  fileId?: string;
  name: string;
  status: 'pending' | 'indexed' | 'failed';
  chunkCount: number;
  errorMessage?: string;
  createdAt?: string;
}

export interface KnowledgeBaseCreatePayload {
  name: string;
  description?: string;
  linkToAgent?: boolean;
}

export interface KnowledgeDocumentIndexPayload {
  fileId: string;
}
