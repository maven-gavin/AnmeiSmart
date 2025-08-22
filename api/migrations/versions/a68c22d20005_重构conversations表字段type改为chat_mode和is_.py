"""重构conversations表字段type改为chat_mode和is_consultation_session改为tag

Revision ID: a68c22d20005
Revises: ab6f118d9bbd
Create Date: 2025-08-22 11:43:22.115584

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a68c22d20005'
down_revision: Union[str, None] = 'ab6f118d9bbd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 重构conversations表字段
    
    # 1. 添加新字段chat_mode
    op.add_column('conversations', 
                  sa.Column('chat_mode', sa.String(50), 
                           nullable=True, comment='会话模式：单聊、群聊'))
    
    # 2. 从旧字段type复制数据到新字段chat_mode
    op.execute("UPDATE conversations SET chat_mode = type WHERE chat_mode IS NULL")
    
    # 3. 设置chat_mode为NOT NULL并设置默认值
    op.alter_column('conversations', 'chat_mode', nullable=False, server_default='single')
    
    # 4. 添加新字段tag
    op.add_column('conversations', 
                  sa.Column('tag', sa.String(50), 
                           nullable=True, comment='会话标签：chat(普通聊天)、consultation(咨询会话)'))
    
    # 5. 从旧字段is_consultation_session转换数据到新字段tag
    op.execute("""
        UPDATE conversations 
        SET tag = CASE 
            WHEN is_consultation_session = TRUE THEN 'consultation'
            ELSE 'chat'
        END 
        WHERE tag IS NULL
    """)
    
    # 6. 设置tag为NOT NULL并设置默认值
    op.alter_column('conversations', 'tag', nullable=False, server_default='chat')
    
    # 7. 删除旧索引
    op.drop_index('idx_conversation_type', 'conversations')
    op.drop_index('idx_conversation_consultation', 'conversations')
    
    # 8. 创建新索引
    op.create_index('idx_conversation_chat_mode', 'conversations', ['chat_mode'])
    op.create_index('idx_conversation_tag', 'conversations', ['tag'])
    
    # 9. 删除旧字段
    op.drop_column('conversations', 'type')
    op.drop_column('conversations', 'is_consultation_session')


def downgrade() -> None:
    # 恢复旧字段结构
    
    # 1. 添加旧字段
    op.add_column('conversations', 
                  sa.Column('type', sa.String(50), nullable=False, default='single', comment='会话类型：单聊、群聊'))
    op.add_column('conversations', 
                  sa.Column('is_consultation_session', sa.Boolean(), nullable=False, default=False, comment='是否为咨询类会话'))
    
    # 2. 恢复数据
    op.execute("UPDATE conversations SET type = chat_mode")
    op.execute("UPDATE conversations SET is_consultation_session = (tag = 'consultation')")
    
    # 3. 删除新索引
    op.drop_index('idx_conversation_tag', 'conversations')
    op.drop_index('idx_conversation_chat_mode', 'conversations')
    
    # 4. 恢复旧索引
    op.create_index('idx_conversation_type', 'conversations', ['type'])
    op.create_index('idx_conversation_consultation', 'conversations', ['is_consultation_session'])
    
    # 5. 删除新字段
    op.drop_column('conversations', 'tag')
    op.drop_column('conversations', 'chat_mode')
