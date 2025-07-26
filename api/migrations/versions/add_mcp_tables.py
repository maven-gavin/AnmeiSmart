"""添加MCP工具分组管理相关表结构

Revision ID: add_mcp_tables
Revises: 723c0cbcec54
Create Date: 2025-01-XX XX:XX:XX.XXXXXX

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e1234567890a'
down_revision = '848ce2a2d9bf'
branch_labels = None
depends_on = None


def upgrade():
    # 创建MCP工具分组表
    op.create_table('mcp_tool_groups',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('api_key', sa.String(length=255), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=True),
        sa.Column('created_by', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_mcp_tool_groups_id'), 'mcp_tool_groups', ['id'], unique=False)
    op.create_index(op.f('ix_mcp_tool_groups_name'), 'mcp_tool_groups', ['name'], unique=True)
    op.create_index(op.f('ix_mcp_tool_groups_enabled'), 'mcp_tool_groups', ['enabled'], unique=False)
    op.create_index(op.f('ix_mcp_tool_groups_created_by'), 'mcp_tool_groups', ['created_by'], unique=False)

    # 创建MCP工具配置表
    op.create_table('mcp_tools',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tool_name', sa.String(length=100), nullable=False),
        sa.Column('group_id', sa.String(length=36), nullable=False),
        sa.Column('version', sa.String(length=20), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=True),
        sa.Column('timeout_seconds', sa.Integer(), nullable=True),
        sa.Column('config_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['group_id'], ['mcp_tool_groups.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_mcp_tools_id'), 'mcp_tools', ['id'], unique=False)
    op.create_index(op.f('ix_mcp_tools_tool_name'), 'mcp_tools', ['tool_name'], unique=True)
    op.create_index(op.f('ix_mcp_tools_group_enabled'), 'mcp_tools', ['group_id', 'enabled'], unique=False)

    # 创建MCP调用日志表
    op.create_table('mcp_call_logs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tool_name', sa.String(length=100), nullable=False),
        sa.Column('group_id', sa.String(length=36), nullable=False),
        sa.Column('caller_app_id', sa.String(length=100), nullable=True),
        sa.Column('request_data', sa.JSON(), nullable=True),
        sa.Column('response_data', sa.JSON(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_mcp_call_logs_id'), 'mcp_call_logs', ['id'], unique=False)
    op.create_index(op.f('ix_mcp_call_logs_tool_success_time'), 'mcp_call_logs', ['tool_name', 'success', 'created_at'], unique=False)
    op.create_index(op.f('ix_mcp_call_logs_group_time'), 'mcp_call_logs', ['group_id', 'created_at'], unique=False)
    op.create_index(op.f('ix_mcp_call_logs_caller_time'), 'mcp_call_logs', ['caller_app_id', 'created_at'], unique=False)


def downgrade():
    # 删除索引和表（与创建顺序相反）
    op.drop_index(op.f('ix_mcp_call_logs_caller_time'), table_name='mcp_call_logs')
    op.drop_index(op.f('ix_mcp_call_logs_group_time'), table_name='mcp_call_logs')
    op.drop_index(op.f('ix_mcp_call_logs_tool_success_time'), table_name='mcp_call_logs')
    op.drop_index(op.f('ix_mcp_call_logs_id'), table_name='mcp_call_logs')
    op.drop_table('mcp_call_logs')

    op.drop_index(op.f('ix_mcp_tools_group_enabled'), table_name='mcp_tools')
    op.drop_index(op.f('ix_mcp_tools_tool_name'), table_name='mcp_tools')
    op.drop_index(op.f('ix_mcp_tools_id'), table_name='mcp_tools')
    op.drop_table('mcp_tools')

    op.drop_index(op.f('ix_mcp_tool_groups_created_by'), table_name='mcp_tool_groups')
    op.drop_index(op.f('ix_mcp_tool_groups_enabled'), table_name='mcp_tool_groups')
    op.drop_index(op.f('ix_mcp_tool_groups_name'), table_name='mcp_tool_groups')
    op.drop_index(op.f('ix_mcp_tool_groups_id'), table_name='mcp_tool_groups')
    op.drop_table('mcp_tool_groups') 