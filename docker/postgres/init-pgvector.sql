-- 首次初始化数据库时启用 pgvector（RAG 向量检索依赖）
CREATE EXTENSION IF NOT EXISTS vector;
