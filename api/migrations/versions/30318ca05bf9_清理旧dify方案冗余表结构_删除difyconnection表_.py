"""清理旧Dify方案冗余表结构_删除DifyConnection表_清理AIModelConfig冗余字段

Revision ID: 30318ca05bf9
Revises: 27fca9bcdf63
Create Date: 2025-07-11 16:00:49.619548

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '30318ca05bf9'
down_revision: Union[str, None] = '27fca9bcdf63'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """删除旧Dify方案的冗余表结构"""
    
    # 1. 删除AIModelConfig表中的Dify相关字段和约束
    # 首先删除相关的外键约束
    op.drop_constraint('ai_model_configs_dify_connection_id_fkey', 'ai_model_configs', type_='foreignkey')
    
    # 删除相关索引
    op.drop_index('idx_ai_model_dify_connection', table_name='ai_model_configs')
    op.drop_index('idx_ai_model_agent_type_default', table_name='ai_model_configs')
    
    # 删除唯一约束
    op.drop_constraint('uq_default_agent_per_type', 'ai_model_configs', type_='unique')
    
    # 删除Dify相关字段
    op.drop_column('ai_model_configs', 'dify_connection_id')
    op.drop_column('ai_model_configs', 'dify_app_id')
    op.drop_column('ai_model_configs', 'dify_app_name')
    op.drop_column('ai_model_configs', 'dify_app_mode')
    op.drop_column('ai_model_configs', 'agent_type')
    op.drop_column('ai_model_configs', 'is_default_for_type')
    
    # 2. 删除整个DifyConnection表
    op.drop_table('dify_connections')
    
    # 3. 删除相关的枚举类型
    op.execute("DROP TYPE IF EXISTS agenttype")
    op.execute("DROP TYPE IF EXISTS syncstatus")


def downgrade() -> None:
    """回滚操作 - 恢复旧表结构（仅用于紧急回滚）"""
    
    # 1. 重新创建枚举类型
    op.execute("CREATE TYPE agenttype AS ENUM ('GENERAL_CHAT', 'BEAUTY_PLAN', 'CONSULTATION', 'CUSTOMER_SERVICE', 'MEDICAL_ADVICE')")
    op.execute("CREATE TYPE syncstatus AS ENUM ('NOT_SYNCED', 'SYNCING', 'SUCCESS', 'FAILED')")
    
    # 2. 重新创建DifyConnection表
    op.create_table(
        'dify_connections',
        sa.Column('id', sa.String(length=36), nullable=False, comment='连接配置ID'),
        sa.Column('name', sa.String(length=255), nullable=False, comment='连接名称'),
        sa.Column('api_base_url', sa.String(length=1024), nullable=False, comment='Dify API基础URL'),
        sa.Column('api_key', sa.Text(), nullable=False, comment='Dify API密钥（加密存储）'),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True, comment='是否为活跃连接'),
        sa.Column('is_default', sa.Boolean(), nullable=False, default=False, comment='是否为默认连接'),
        sa.Column('description', sa.Text(), nullable=True, comment='连接描述'),
        sa.Column('last_sync_at', sa.DateTime(), nullable=True, comment='最后同步时间'),
        sa.Column('sync_status', sa.Enum('NOT_SYNCED', 'SYNCING', 'SUCCESS', 'FAILED', name='syncstatus'), 
                 nullable=False, default='NOT_SYNCED', comment='同步状态'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        comment='Dify实例连接配置表'
    )
    
    # 3. 添加AIModelConfig表的Dify相关字段
    op.add_column('ai_model_configs', sa.Column('dify_connection_id', sa.String(length=36), nullable=True, comment='Dify连接ID'))
    op.add_column('ai_model_configs', sa.Column('dify_app_id', sa.String(length=255), nullable=True, comment='Dify应用ID'))
    op.add_column('ai_model_configs', sa.Column('dify_app_name', sa.String(length=255), nullable=True, comment='Dify应用名称'))
    op.add_column('ai_model_configs', sa.Column('dify_app_mode', sa.String(length=50), nullable=True, comment='Dify应用模式'))
    op.add_column('ai_model_configs', sa.Column('agent_type', 
                 sa.Enum('GENERAL_CHAT', 'BEAUTY_PLAN', 'CONSULTATION', 'CUSTOMER_SERVICE', 'MEDICAL_ADVICE', name='agenttype'), 
                 nullable=True, comment='Agent类型'))
    op.add_column('ai_model_configs', sa.Column('is_default_for_type', sa.Boolean(), nullable=False, default=False, comment='是否为该类型的默认模型'))
    
    # 4. 重新创建约束和索引
    op.create_foreign_key('ai_model_configs_dify_connection_id_fkey', 'ai_model_configs', 'dify_connections', ['dify_connection_id'], ['id'])
    op.create_index('idx_ai_model_dify_connection', 'ai_model_configs', ['dify_connection_id'])
    op.create_index('idx_ai_model_agent_type_default', 'ai_model_configs', ['agent_type', 'is_default_for_type'])
    op.create_unique_constraint('uq_default_agent_per_type', 'ai_model_configs', ['agent_type', 'is_default_for_type'])
    
    # 5. 为DifyConnection表添加索引和约束
    op.create_index('idx_dify_connections_active_default', 'dify_connections', ['is_active', 'is_default'])
    op.create_index('idx_dify_connections_sync_status', 'dify_connections', ['sync_status'])
    op.create_unique_constraint('uq_default_connection', 'dify_connections', ['is_default'])
