"""重命名dify_configs表为agent_configs

Revision ID: 6e9a9cccd06b
Revises: 23747bb7569c
Create Date: 2025-01-27 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6e9a9cccd06b'
down_revision: Union[str, None] = '23747bb7569c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 重命名表
    op.rename_table('dify_configs', 'agent_configs')
    
    # 重命名索引
    op.drop_index('idx_dify_config_environment', table_name='agent_configs')
    op.drop_index('idx_dify_config_enabled', table_name='agent_configs')
    op.drop_index('idx_dify_config_env_app', table_name='agent_configs')
    
    op.create_index('idx_agent_config_environment', 'agent_configs', ['environment'], unique=False)
    op.create_index('idx_agent_config_enabled', 'agent_configs', ['enabled'], unique=False)
    op.create_index('idx_agent_config_env_app', 'agent_configs', ['environment', 'app_id'], unique=True)
    
    # 更新表注释
    op.execute("COMMENT ON TABLE agent_configs IS 'Agent配置表，存储独立的Agent应用配置'")
    
    # 更新列注释
    op.execute("COMMENT ON COLUMN agent_configs.id IS 'Agent配置ID'")


def downgrade() -> None:
    # 重命名索引
    op.drop_index('idx_agent_config_environment', table_name='agent_configs')
    op.drop_index('idx_agent_config_enabled', table_name='agent_configs')
    op.drop_index('idx_agent_config_env_app', table_name='agent_configs')
    
    op.create_index('idx_dify_config_environment', 'agent_configs', ['environment'], unique=False)
    op.create_index('idx_dify_config_enabled', 'agent_configs', ['enabled'], unique=False)
    op.create_index('idx_dify_config_env_app', 'agent_configs', ['environment', 'app_id'], unique=True)
    
    # 重命名表
    op.rename_table('agent_configs', 'dify_configs')
    
    # 恢复表注释
    op.execute("COMMENT ON TABLE dify_configs IS 'Dify配置表，存储独立的Dify应用配置'")
    
    # 恢复列注释
    op.execute("COMMENT ON COLUMN dify_configs.id IS 'Dify配置ID'")
