"""add_agent_runtime_tables

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-06-19 16:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # pgvector 扩展需在 PostgreSQL 侧安装（RAG 功能依赖，见 env.example 说明）
    # LlamaIndex PGVectorStore 首次索引时会创建向量表

    op.create_table(
        "agent_conversations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("agent_config_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False, server_default="新对话"),
        sa.ForeignKeyConstraint(["agent_config_id"], ["agent_configs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        comment="Agent 会话表",
    )
    op.create_index("idx_agent_conv_config_user", "agent_conversations", ["agent_config_id", "user_id"])
    op.create_index("idx_agent_conv_updated", "agent_conversations", ["updated_at"])

    op.create_table(
        "agent_messages",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("conversation_id", sa.String(length=36), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_error", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["conversation_id"], ["agent_conversations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        comment="Agent 消息表",
    )
    op.create_index("idx_agent_msg_conversation", "agent_messages", ["conversation_id", "created_at"])

    op.create_table(
        "agent_message_feedbacks",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("message_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("rating", sa.String(length=20), nullable=False),
        sa.ForeignKeyConstraint(["message_id"], ["agent_messages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        comment="Agent 消息反馈表",
    )
    op.create_index(
        "idx_agent_feedback_message_user",
        "agent_message_feedbacks",
        ["message_id", "user_id"],
        unique=True,
    )

    op.create_table(
        "agent_knowledge_bases",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("agent_config_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("embedding_model", sa.String(length=100), nullable=False),
        sa.Column("chunk_size", sa.Integer(), nullable=False),
        sa.Column("chunk_overlap", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("index_table_name", sa.String(length=100), nullable=False),
        sa.ForeignKeyConstraint(["agent_config_id"], ["agent_configs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        comment="Agent 知识库表",
    )
    op.create_index("idx_agent_kb_config", "agent_knowledge_bases", ["agent_config_id"])

    op.create_table(
        "agent_knowledge_documents",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("knowledge_base_id", sa.String(length=36), nullable=False),
        sa.Column("file_id", sa.String(length=36), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("chunk_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["file_id"], ["files.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["knowledge_base_id"], ["agent_knowledge_bases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        comment="Agent 知识库文档表",
    )
    op.create_index("idx_agent_kdoc_kb", "agent_knowledge_documents", ["knowledge_base_id"])


def downgrade() -> None:
    op.drop_index("idx_agent_kdoc_kb", table_name="agent_knowledge_documents")
    op.drop_table("agent_knowledge_documents")
    op.drop_index("idx_agent_kb_config", table_name="agent_knowledge_bases")
    op.drop_table("agent_knowledge_bases")
    op.drop_index("idx_agent_feedback_message_user", table_name="agent_message_feedbacks")
    op.drop_table("agent_message_feedbacks")
    op.drop_index("idx_agent_msg_conversation", table_name="agent_messages")
    op.drop_table("agent_messages")
    op.drop_index("idx_agent_conv_updated", table_name="agent_conversations")
    op.drop_index("idx_agent_conv_config_user", table_name="agent_conversations")
    op.drop_table("agent_conversations")
