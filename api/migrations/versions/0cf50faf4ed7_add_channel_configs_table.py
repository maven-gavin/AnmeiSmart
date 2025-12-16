"""add_channel_configs_table

Revision ID: 0cf50faf4ed7
Revises: 9b10c1943252
Create Date: 2025-12-16 09:30:27.550441

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0cf50faf4ed7'
down_revision: Union[str, None] = '9b10c1943252'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 创建渠道配置表
    op.create_table(
        'channel_configs',
        sa.Column('id', sa.String(36), nullable=False, comment='配置ID'),
        sa.Column('channel_type', sa.String(50), nullable=False, comment='渠道类型：wechat_work, wechat, whatsapp等'),
        sa.Column('name', sa.String(100), nullable=False, comment='渠道名称'),
        sa.Column('config', sa.JSON(), nullable=False, comment='渠道配置（API密钥、Webhook URL等）'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true', comment='是否激活'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True, comment='更新时间'),
        sa.Column('created_by', sa.String(36), nullable=True, comment='创建人ID'),
        sa.Column('updated_by', sa.String(36), nullable=True, comment='修改人ID'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ondelete='SET NULL'),
        comment='渠道配置表，存储各渠道的配置信息'
    )


def downgrade() -> None:
    # 删除渠道配置表
    op.drop_table('channel_configs')
