"""重构会话模型：将个人化字段移至参与者表

Revision ID: 7e61fced6500
Revises: 
Create Date: 2025-11-30 19:33:05.667953

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '7e61fced6500'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """升级：将个人化字段从 conversations 表移到 conversation_participants 表"""
    
    # 1. 在 conversation_participants 表中添加新字段
    op.add_column('conversation_participants', sa.Column('is_pinned', sa.Boolean(), nullable=True, comment='是否置顶（个人设置）'))
    op.add_column('conversation_participants', sa.Column('pinned_at', sa.DateTime(timezone=True), nullable=True, comment='置顶时间（个人设置）'))
    op.add_column('conversation_participants', sa.Column('message_count', sa.Integer(), nullable=True, comment='该参与者的消息总数（从该参与者视角）'))
    op.add_column('conversation_participants', sa.Column('unread_count', sa.Integer(), nullable=True, comment='该参与者的未读消息数'))
    op.add_column('conversation_participants', sa.Column('last_message_at', sa.DateTime(timezone=True), nullable=True, comment='最后消息时间（从该参与者视角）'))
    
    # 2. 设置默认值
    op.execute(sa.text("""
        UPDATE conversation_participants
        SET 
            message_count = COALESCE(message_count, 0),
            unread_count = COALESCE(unread_count, 0),
            is_pinned = COALESCE(is_pinned, false)
        WHERE message_count IS NULL OR unread_count IS NULL OR is_pinned IS NULL
    """))
    
    # 3. 添加索引
    op.create_index('idx_conversation_participant_pinned', 'conversation_participants', ['is_pinned', 'pinned_at'], unique=False)
    
    # 4. 从 conversations 表删除旧字段
    # 先删除索引和外键约束
    op.execute(sa.text("DROP INDEX IF EXISTS idx_conversation_first_participant"))
    op.execute(sa.text("DROP INDEX IF EXISTS idx_conversation_pinned"))
    op.execute(sa.text("ALTER TABLE conversations DROP CONSTRAINT IF EXISTS conversations_first_participant_id_fkey"))
    
    # 删除字段
    op.drop_column('conversations', 'pinned_at')
    op.drop_column('conversations', 'message_count')
    op.drop_column('conversations', 'last_message_at')
    op.drop_column('conversations', 'is_pinned')
    op.drop_column('conversations', 'first_participant_id')
    op.drop_column('conversations', 'unread_count')


def downgrade() -> None:
    """降级：将个人化字段从 conversation_participants 表移回 conversations 表"""
    
    # 1. 在 conversations 表中恢复字段
    op.add_column('conversations', sa.Column('unread_count', sa.Integer(), nullable=False, comment='未读消息数', server_default='0'))
    op.add_column('conversations', sa.Column('first_participant_id', sa.String(length=36), nullable=True, comment='第一个参与者用户ID'))
    op.add_column('conversations', sa.Column('is_pinned', sa.Boolean(), nullable=False, comment='是否置顶', server_default='false'))
    op.add_column('conversations', sa.Column('last_message_at', postgresql.TIMESTAMP(timezone=True), nullable=True, comment='最后消息时间'))
    op.add_column('conversations', sa.Column('message_count', sa.Integer(), nullable=False, comment='消息总数', server_default='0'))
    op.add_column('conversations', sa.Column('pinned_at', postgresql.TIMESTAMP(timezone=True), nullable=True, comment='置顶时间'))
    
    # 恢复外键和索引
    op.create_foreign_key('conversations_first_participant_id_fkey', 'conversations', 'users', ['first_participant_id'], ['id'])
    op.create_index('idx_conversation_pinned', 'conversations', ['is_pinned', 'pinned_at'], unique=False)
    op.create_index('idx_conversation_first_participant', 'conversations', ['first_participant_id'], unique=False)
    
    # 2. 从 conversation_participants 表删除新字段
    op.drop_index('idx_conversation_participant_pinned', table_name='conversation_participants')
    op.drop_column('conversation_participants', 'last_message_at')
    op.drop_column('conversation_participants', 'unread_count')
    op.drop_column('conversation_participants', 'message_count')
    op.drop_column('conversation_participants', 'pinned_at')
    op.drop_column('conversation_participants', 'is_pinned')
