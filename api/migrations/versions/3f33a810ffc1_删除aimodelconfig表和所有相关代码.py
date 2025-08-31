"""删除AIModelConfig表和所有相关代码

Revision ID: 3f33a810ffc1
Revises: a68c22d20005
Create Date: 2025-08-31 10:47:02.134189

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3f33a810ffc1'
down_revision: Union[str, None] = 'a68c22d20005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """删除AIModelConfig表"""
    # 删除ai_model_configs表
    op.drop_table('ai_model_configs')


def downgrade() -> None:
    """恢复AIModelConfig表"""
    # 重新创建ai_model_configs表
    op.create_table('ai_model_configs',
        sa.Column('id', sa.String(length=36), nullable=False, comment='模型配置ID'),
        sa.Column('model_name', sa.String(length=255), nullable=False, comment='模型名称'),
        sa.Column('api_key', sa.Text(), nullable=True, comment='API密钥（加密存储）'),
        sa.Column('base_url', sa.String(length=1024), nullable=True, comment='API基础URL'),
        sa.Column('max_tokens', sa.Integer(), nullable=True, comment='最大Token数'),
        sa.Column('temperature', sa.Float(), nullable=True, comment='采样温度'),
        sa.Column('enabled', sa.Boolean(), nullable=False, comment='是否启用'),
        sa.Column('provider', sa.String(length=255), nullable=False, comment='服务商'),
        sa.Column('description', sa.Text(), nullable=True, comment='模型描述'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='更新时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_ai_model_provider_enabled', 'provider', 'enabled')
    )
