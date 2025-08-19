"""添加会话参与者表和消息确认字段

Revision ID: add_dh_participants
Revises: dh_system_v1
Create Date: 2024-12-19 11:03:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_dh_participants'
down_revision = 'dh_system_v1'
branch_labels = None
depends_on = None


def upgrade():
    # 只创建新表，不修改现有表
    print("Creating conversation_participants table...")
    
    op.create_table('conversation_participants',
        sa.Column('id', sa.String(36), nullable=False, comment='参与者ID'),
        sa.Column('conversation_id', sa.String(36), nullable=False, comment='会话ID'),
        sa.Column('user_id', sa.String(36), nullable=True, comment='用户ID'),
        sa.Column('digital_human_id', sa.String(36), nullable=True, comment='数字人ID'),
        sa.Column('role', sa.String(50), nullable=False, default='member', comment='参与者角色'),
        sa.Column('takeover_status', sa.String(50), nullable=False, default='no_takeover', comment='接管状态'),
        sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['digital_human_id'], ['digital_humans.id']),
        sa.PrimaryKeyConstraint('id'),
        comment='会话参与者表'
    )
    
    # 创建索引
    op.create_index('idx_conv_participant_conv', 'conversation_participants', ['conversation_id'])
    op.create_index('idx_conv_participant_user', 'conversation_participants', ['user_id'])
    op.create_index('idx_conv_participant_dh', 'conversation_participants', ['digital_human_id'])
    
    print("Conversation participants table created successfully!")


def downgrade():
    # 删除会话参与者表
    op.drop_index('idx_conv_participant_dh', 'conversation_participants')
    op.drop_index('idx_conv_participant_user', 'conversation_participants')
    op.drop_index('idx_conv_participant_conv', 'conversation_participants')
    op.drop_table('conversation_participants')
