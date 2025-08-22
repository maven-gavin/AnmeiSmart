"""为conversation_participants表添加缺失字段

Revision ID: c4293bd072ee
Revises: 68a2162c82ec
Create Date: 2025-08-21 23:43:51.108247

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4293bd072ee'
down_revision: Union[str, None] = '68a2162c82ec'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 为conversation_participants表添加缺失字段
    
    # 1. 添加left_at字段（可为空）
    op.add_column('conversation_participants', 
                  sa.Column('left_at', sa.DateTime(timezone=True), 
                           nullable=True, comment='离开时间'))
    
    # 2. 添加is_muted字段（先允许为空）
    op.add_column('conversation_participants', 
                  sa.Column('is_muted', sa.Boolean(), 
                           nullable=True, comment='个人免打扰'))
    
    # 3. 为现有数据设置默认值
    op.execute("UPDATE conversation_participants SET is_muted = FALSE WHERE is_muted IS NULL")
    
    # 4. 设置字段为NOT NULL
    op.alter_column('conversation_participants', 'is_muted', nullable=False)
    
    # 5. 添加last_read_at字段（可为空）
    op.add_column('conversation_participants', 
                  sa.Column('last_read_at', sa.DateTime(timezone=True), 
                           nullable=True, comment='最后阅读时间'))


def downgrade() -> None:
    # 删除添加的字段
    op.drop_column('conversation_participants', 'last_read_at')
    op.drop_column('conversation_participants', 'is_muted')
    op.drop_column('conversation_participants', 'left_at')
