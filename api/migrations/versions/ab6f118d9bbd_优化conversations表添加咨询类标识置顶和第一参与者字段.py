"""优化conversations表添加咨询类标识置顶和第一参与者字段

Revision ID: ab6f118d9bbd
Revises: c4293bd072ee
Create Date: 2025-08-22 10:56:52.974588

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ab6f118d9bbd'
down_revision: Union[str, None] = 'c4293bd072ee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 为conversations表添加新字段
    
    # 1. 添加咨询类会话标识（先允许为空）
    op.add_column('conversations', 
                  sa.Column('is_consultation_session', sa.Boolean(), 
                           nullable=True, comment='是否为咨询类会话'))
    
    # 2. 添加置顶功能字段（先允许为空）
    op.add_column('conversations', 
                  sa.Column('is_pinned', sa.Boolean(), 
                           nullable=True, comment='是否置顶'))
    
    op.add_column('conversations', 
                  sa.Column('pinned_at', sa.DateTime(timezone=True), 
                           nullable=True, comment='置顶时间'))
    
    # 3. 添加第一个参与者ID字段（优化查询）
    op.add_column('conversations', 
                  sa.Column('first_participant_id', sa.String(36), 
                           sa.ForeignKey('users.id'), nullable=True, 
                           comment='第一个参与者用户ID'))
    
    # 4. 创建新的索引
    op.create_index('idx_conversation_consultation', 'conversations', ['is_consultation_session'])
    op.create_index('idx_conversation_pinned', 'conversations', ['is_pinned', 'pinned_at'])
    op.create_index('idx_conversation_first_participant', 'conversations', ['first_participant_id'])
    
    # 5. 为现有数据设置默认值
    op.execute("UPDATE conversations SET is_consultation_session = FALSE WHERE is_consultation_session IS NULL")
    op.execute("UPDATE conversations SET is_pinned = FALSE WHERE is_pinned IS NULL")
    
    # 6. 设置字段为NOT NULL
    op.alter_column('conversations', 'is_consultation_session', nullable=False)
    op.alter_column('conversations', 'is_pinned', nullable=False)


def downgrade() -> None:
    # 删除索引
    op.drop_index('idx_conversation_first_participant', 'conversations')
    op.drop_index('idx_conversation_pinned', 'conversations')
    op.drop_index('idx_conversation_consultation', 'conversations')
    
    # 删除字段
    op.drop_column('conversations', 'first_participant_id')
    op.drop_column('conversations', 'pinned_at')
    op.drop_column('conversations', 'is_pinned')
    op.drop_column('conversations', 'is_consultation_session')
