"""安全地重新创建核心表

Revision ID: recreate_tables_safe
Revises: step3_cleanup_upload
Create Date: 2024-12-19 12:15:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'recreate_tables_safe'
down_revision = 'step3_cleanup_upload'
branch_labels = None
depends_on = None


def upgrade():
    print("安全地重新创建核心表...")
    
    # 1. 使用CASCADE删除所有相关表
    print("删除现有表（CASCADE模式）...")
    
    tables_to_drop = [
        'message_attachments',
        'conversation_participants', 
        'messages',
        'upload_chunks',
        'upload_sessions',
        'conversations'
    ]
    
    for table in tables_to_drop:
        try:
            op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
            print(f"  ✅ 删除 {table} 表")
        except Exception as e:
            print(f"  ⚠️ {table}: {e}")
    
    # 2. 重新创建表（按PRD设计）
    print("\\n重新创建表...")
    
    # 创建conversations表
    op.create_table('conversations',
        sa.Column('id', sa.String(36), nullable=False, comment='会话ID'),
        sa.Column('title', sa.String(), nullable=False, comment='会话标题'),
        sa.Column('type', sa.String(50), nullable=False, default='single', comment='会话类型：单聊、群聊'),
        sa.Column('owner_id', sa.String(36), nullable=False, comment='会话所有者用户ID'),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True, comment='会话是否激活'),
        sa.Column('is_archived', sa.Boolean(), nullable=False, default=False, comment='是否已归档'),
        sa.Column('message_count', sa.Integer(), nullable=False, default=0, comment='消息总数'),
        sa.Column('unread_count', sa.Integer(), nullable=False, default=0, comment='未读消息数'),
        sa.Column('last_message_at', sa.DateTime(timezone=True), nullable=True, comment='最后消息时间'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        comment='会话表，存储用户会话信息'
    )
    print("  ✅ 创建 conversations 表")
    
    # 创建conversations表索引
    op.create_index('idx_conversation_owner', 'conversations', ['owner_id'])
    op.create_index('idx_conversation_type', 'conversations', ['type'])
    op.create_index('idx_conversation_status', 'conversations', ['is_active'])
    
    # 创建messages表
    op.create_table('messages',
        sa.Column('id', sa.String(36), nullable=False, comment='消息ID'),
        sa.Column('conversation_id', sa.String(36), nullable=False, comment='会话ID'),
        sa.Column('content', sa.JSON(), nullable=False, comment='结构化的消息内容'),
        sa.Column('type', sa.String(50), nullable=False, comment='消息主类型'),
        sa.Column('sender_id', sa.String(36), nullable=True, comment='发送者用户ID'),
        sa.Column('sender_digital_human_id', sa.String(36), nullable=True, comment='发送者数字人ID'),
        sa.Column('sender_type', sa.String(50), nullable=False, comment='发送者类型'),
        sa.Column('is_read', sa.Boolean(), nullable=False, default=False, comment='是否已读'),
        sa.Column('is_important', sa.Boolean(), nullable=False, default=False, comment='是否重要'),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='消息时间戳'),
        sa.Column('requires_confirmation', sa.Boolean(), nullable=False, default=False, comment='是否需要确认（半接管模式）'),
        sa.Column('is_confirmed', sa.Boolean(), nullable=False, default=True, comment='是否已确认'),
        sa.Column('confirmed_by', sa.String(36), nullable=True, comment='确认人ID'),
        sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=True, comment='确认时间'),
        sa.Column('reply_to_message_id', sa.String(36), nullable=True, comment='回复的消息ID'),
        sa.Column('reactions', sa.JSON(), nullable=True, comment='消息回应'),
        sa.Column('extra_metadata', sa.JSON(), nullable=True, comment='附加元数据'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['sender_id'], ['users.id']),
        sa.ForeignKeyConstraint(['sender_digital_human_id'], ['digital_humans.id']),
        sa.ForeignKeyConstraint(['confirmed_by'], ['users.id']),
        sa.ForeignKeyConstraint(['reply_to_message_id'], ['messages.id']),
        sa.PrimaryKeyConstraint('id'),
        comment='消息表，存储会话中的消息内容'
    )
    print("  ✅ 创建 messages 表")
    
    # 创建messages表索引
    op.create_index('idx_message_conversation', 'messages', ['conversation_id'])
    op.create_index('idx_message_sender', 'messages', ['sender_id'])
    op.create_index('idx_message_sender_dh', 'messages', ['sender_digital_human_id'])
    op.create_index('idx_message_timestamp', 'messages', ['timestamp'])
    
    # 创建upload_sessions表（独立组件）
    op.create_table('upload_sessions',
        sa.Column('id', sa.String(36), nullable=False, comment='记录ID'),
        sa.Column('upload_id', sa.String(64), unique=True, index=True, nullable=False, comment='上传ID'),
        sa.Column('file_name', sa.String(255), nullable=False, comment='原始文件名'),
        sa.Column('file_size', sa.BigInteger(), nullable=False, comment='文件总大小（字节）'),
        sa.Column('chunk_size', sa.Integer(), nullable=False, comment='分片大小（字节）'),
        sa.Column('total_chunks', sa.Integer(), nullable=False, comment='总分片数'),
        sa.Column('content_type', sa.String(100), nullable=True, comment='文件MIME类型'),
        sa.Column('file_extension', sa.String(10), nullable=True, comment='文件扩展名'),
        sa.Column('user_id', sa.String(36), nullable=False, comment='上传用户ID'),
        sa.Column('business_type', sa.String(50), nullable=True, comment='业务类型：avatar, message, document等'),
        sa.Column('business_id', sa.String(36), nullable=True, comment='关联的业务对象ID'),
        sa.Column('status', sa.String(20), nullable=False, default='uploading', comment='上传状态'),
        sa.Column('final_object_name', sa.String(500), nullable=True, comment='合并后的文件对象名'),
        sa.Column('is_public', sa.Boolean(), nullable=False, default=False, comment='是否公开访问'),
        sa.Column('access_token', sa.String(64), nullable=True, comment='访问令牌（私有文件）'),
        sa.Column('expires_at', sa.DateTime(), nullable=True, comment='过期时间（临时文件）'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        comment='上传会话表，独立的文件上传组件'
    )
    print("  ✅ 创建 upload_sessions 表")
    
    # 创建upload_chunks表
    op.create_table('upload_chunks',
        sa.Column('id', sa.String(36), nullable=False, comment='分片ID'),
        sa.Column('upload_id', sa.String(64), nullable=False, comment='关联上传ID'),
        sa.Column('chunk_index', sa.Integer(), nullable=False, comment='分片索引（从0开始）'),
        sa.Column('object_name', sa.String(500), nullable=False, comment='分片在MinIO中的对象名'),
        sa.Column('chunk_size', sa.Integer(), nullable=False, comment='分片实际大小（字节）'),
        sa.Column('status', sa.String(20), nullable=False, default='uploading', comment='分片状态'),
        sa.Column('checksum', sa.String(64), nullable=True, comment='分片校验和（可选）'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['upload_id'], ['upload_sessions.upload_id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('upload_id', 'chunk_index', name='uk_upload_chunk_index'),
        comment='上传分片表'
    )
    print("  ✅ 创建 upload_chunks 表")
    
    # 创建conversation_participants表
    op.create_table('conversation_participants',
        sa.Column('id', sa.String(36), nullable=False, comment='参与者ID'),
        sa.Column('conversation_id', sa.String(36), nullable=False, comment='会话ID'),
        sa.Column('user_id', sa.String(36), nullable=True, comment='用户ID'),
        sa.Column('digital_human_id', sa.String(36), nullable=True, comment='数字人ID'),
        sa.Column('role', sa.String(50), nullable=False, default='member', comment='参与者角色'),
        sa.Column('takeover_status', sa.String(50), nullable=False, default='no_takeover', comment='接管状态'),
        sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='加入时间'),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True, comment='是否活跃'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['digital_human_id'], ['digital_humans.id']),
        sa.PrimaryKeyConstraint('id'),
        comment='会话参与者表，支持用户和数字人参与'
    )
    print("  ✅ 创建 conversation_participants 表")
    
    # 创建conversation_participants表索引
    op.create_index('idx_conversation_participant_conv', 'conversation_participants', ['conversation_id'])
    op.create_index('idx_conversation_participant_user', 'conversation_participants', ['user_id'])
    op.create_index('idx_conversation_participant_dh', 'conversation_participants', ['digital_human_id'])
    
    # 重新创建message_attachments表
    op.create_table('message_attachments',
        sa.Column('id', sa.String(36), nullable=False, comment='关联ID'),
        sa.Column('message_id', sa.String(36), nullable=False, comment='消息ID'),
        sa.Column('upload_session_id', sa.String(64), nullable=False, comment='上传会话ID'),
        sa.Column('display_order', sa.Integer(), nullable=False, default=0, comment='在消息中的显示顺序'),
        sa.Column('display_name', sa.String(255), nullable=True, comment='显示名称（可自定义）'),
        sa.Column('description', sa.Text(), nullable=True, comment='附件描述'),
        sa.Column('attachment_type', sa.String(50), nullable=False, default='other', comment='附件类型'),
        sa.Column('usage_context', sa.String(100), nullable=True, comment='使用场景'),
        sa.Column('is_primary', sa.Boolean(), nullable=False, default=False, comment='是否为主要附件'),
        sa.Column('is_public', sa.Boolean(), nullable=False, default=True, comment='是否公开可见'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['message_id'], ['messages.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['upload_session_id'], ['upload_sessions.upload_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='消息附件表，建立消息与上传文件的多对多关联'
    )
    print("  ✅ 创建 message_attachments 表")
    
    # 创建message_attachments表索引
    op.create_index('idx_message_attachment_message', 'message_attachments', ['message_id'])
    op.create_index('idx_message_attachment_upload', 'message_attachments', ['upload_session_id'])
    
    print("\\n🎉 核心表重新创建完成！")


def downgrade():
    print("回滚核心表重新创建...")
    
    # 删除重新创建的表
    tables_to_drop = [
        'message_attachments',
        'conversation_participants',
        'messages', 
        'upload_chunks',
        'upload_sessions',
        'conversations'
    ]
    
    for table in tables_to_drop:
        try:
            op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
        except:
            pass
    
    print("回滚完成")
