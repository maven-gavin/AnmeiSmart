"""创建数字人系统表（简化版）

Revision ID: dh_system_v1
Revises: 485f5fdb22b1
Create Date: 2024-12-19 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'dh_system_v1'
down_revision = '485f5fdb22b1'
branch_labels = None
depends_on = None


def upgrade():
    # 获取数据库连接
    connection = op.get_bind()
    
    # 创建数字人表（使用字符串类型避免枚举冲突）
    op.create_table('digital_humans',
        sa.Column('id', sa.String(36), nullable=False, comment='数字人ID'),
        sa.Column('name', sa.String(255), nullable=False, comment='数字人名称'),
        sa.Column('avatar', sa.String(1024), nullable=True, comment='数字人头像URL'),
        sa.Column('description', sa.Text(), nullable=True, comment='数字人描述'),
        sa.Column('type', sa.String(50), nullable=False, default='personal', comment='数字人类型'),
        sa.Column('status', sa.String(50), nullable=False, default='active', comment='数字人状态'),
        sa.Column('is_system_created', sa.Boolean(), nullable=False, default=False, comment='是否系统创建'),
        sa.Column('personality', sa.JSON(), nullable=True, comment='性格特征配置'),
        sa.Column('greeting_message', sa.Text(), nullable=True, comment='默认打招呼消息'),
        sa.Column('welcome_message', sa.Text(), nullable=True, comment='欢迎消息模板'),
        sa.Column('user_id', sa.String(36), nullable=False, comment='所属用户ID'),
        sa.Column('conversation_count', sa.Integer(), nullable=False, default=0, comment='会话总数'),
        sa.Column('message_count', sa.Integer(), nullable=False, default=0, comment='消息总数'),
        sa.Column('last_active_at', sa.DateTime(timezone=True), nullable=True, comment='最后活跃时间'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='更新时间'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        comment='数字人表，存储数字人基础信息和配置'
    )
    
    # 创建数字人表索引
    op.create_index('idx_digital_human_user', 'digital_humans', ['user_id'])
    op.create_index('idx_digital_human_status', 'digital_humans', ['status'])
    op.create_index('idx_digital_human_type', 'digital_humans', ['type'])

    # 为agent_configs表添加新字段（如果表存在）
    try:
        op.add_column('agent_configs', sa.Column('agent_type', sa.String(100), nullable=True, comment='智能体类型'))
    except:
        pass
    try:
        op.add_column('agent_configs', sa.Column('capabilities', sa.JSON(), nullable=True, comment='智能体能力配置'))
    except:
        pass

    # 创建数字人-智能体配置关联表
    op.create_table('digital_human_agent_configs',
        sa.Column('id', sa.String(36), nullable=False, comment='关联ID'),
        sa.Column('digital_human_id', sa.String(36), nullable=False, comment='数字人ID'),
        sa.Column('agent_config_id', sa.String(36), nullable=False, comment='智能体配置ID'),
        sa.Column('priority', sa.Integer(), nullable=False, default=1, comment='优先级'),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True, comment='是否启用此配置'),
        sa.Column('scenarios', sa.JSON(), nullable=True, comment='适用场景配置'),
        sa.Column('context_prompt', sa.Text(), nullable=True, comment='上下文提示词'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['digital_human_id'], ['digital_humans.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['agent_config_id'], ['agent_configs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        comment='数字人与智能体配置关联表，支持多对多关系'
    )
    
    # 创建数字人-智能体配置关联表索引
    op.create_index('idx_dh_agent_digital_human', 'digital_human_agent_configs', ['digital_human_id'])
    op.create_index('idx_dh_agent_config', 'digital_human_agent_configs', ['agent_config_id'])
    op.create_index('idx_dh_agent_priority', 'digital_human_agent_configs', ['priority'])

    # 创建咨询记录表
    op.create_table('consultation_records',
        sa.Column('id', sa.String(36), nullable=False, comment='咨询记录ID'),
        sa.Column('conversation_id', sa.String(36), nullable=False, comment='关联会话ID'),
        sa.Column('customer_id', sa.String(36), nullable=False, comment='客户ID'),
        sa.Column('consultant_id', sa.String(36), nullable=True, comment='顾问ID'),
        sa.Column('digital_human_id', sa.String(36), nullable=True, comment='数字人ID'),
        sa.Column('consultation_type', sa.String(50), nullable=False, comment='咨询类型'),
        sa.Column('title', sa.String(500), nullable=False, comment='咨询标题'),
        sa.Column('description', sa.Text(), nullable=True, comment='咨询描述'),
        sa.Column('status', sa.String(50), nullable=False, default='pending', comment='咨询状态'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True, comment='开始时间'),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True, comment='结束时间'),
        sa.Column('duration_minutes', sa.Integer(), nullable=True, comment='持续时间（分钟）'),
        sa.Column('consultation_summary', sa.JSON(), nullable=True, comment='结构化咨询总结'),
        sa.Column('satisfaction_rating', sa.Integer(), nullable=True, comment='满意度评分（1-5）'),
        sa.Column('follow_up_required', sa.Boolean(), nullable=False, default=False, comment='是否需要跟进'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id']),
        sa.ForeignKeyConstraint(['customer_id'], ['users.id']),
        sa.ForeignKeyConstraint(['consultant_id'], ['users.id']),
        sa.ForeignKeyConstraint(['digital_human_id'], ['digital_humans.id']),
        sa.PrimaryKeyConstraint('id'),
        comment='咨询记录表，记录每次咨询的详细信息'
    )
    
    # 创建咨询记录表索引
    op.create_index('idx_consultation_conversation', 'consultation_records', ['conversation_id'])
    op.create_index('idx_consultation_customer', 'consultation_records', ['customer_id'])
    op.create_index('idx_consultation_consultant', 'consultation_records', ['consultant_id'])
    op.create_index('idx_consultation_type_new', 'consultation_records', ['consultation_type'])

    # 创建待办任务表
    op.create_table('pending_tasks',
        sa.Column('id', sa.String(36), nullable=False, comment='任务ID'),
        sa.Column('title', sa.String(500), nullable=False, comment='任务标题'),
        sa.Column('description', sa.Text(), nullable=True, comment='任务描述'),
        sa.Column('task_type', sa.String(100), nullable=False, comment='任务类型'),
        sa.Column('status', sa.String(50), nullable=False, default='pending', comment='任务状态'),
        sa.Column('priority', sa.String(50), nullable=False, default='medium', comment='任务优先级'),
        sa.Column('created_by', sa.String(36), nullable=True, comment='创建人ID'),
        sa.Column('assigned_to', sa.String(36), nullable=True, comment='分配给用户ID'),
        sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=True, comment='分配时间'),
        sa.Column('related_object_type', sa.String(100), nullable=True, comment='关联对象类型'),
        sa.Column('related_object_id', sa.String(36), nullable=True, comment='关联对象ID'),
        sa.Column('task_data', sa.JSON(), nullable=True, comment='任务相关数据'),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=True, comment='截止时间'),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True, comment='完成时间'),
        sa.Column('result', sa.JSON(), nullable=True, comment='处理结果'),
        sa.Column('notes', sa.Text(), nullable=True, comment='处理备注'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.ForeignKeyConstraint(['assigned_to'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        comment='待办任务表，记录系统发出的待处理任务'
    )
    
    # 创建待办任务表索引
    op.create_index('idx_pending_task_type', 'pending_tasks', ['task_type'])
    op.create_index('idx_pending_task_status', 'pending_tasks', ['status'])
    op.create_index('idx_pending_task_assignee', 'pending_tasks', ['assigned_to'])
    op.create_index('idx_pending_task_priority', 'pending_tasks', ['priority'])

    # 创建消息附件关联表
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
    
    # 创建消息附件关联表索引
    op.create_index('idx_message_attachment_message', 'message_attachments', ['message_id'])
    op.create_index('idx_message_attachment_upload', 'message_attachments', ['upload_session_id'])


def downgrade():
    # 删除索引
    op.drop_index('idx_message_attachment_upload', 'message_attachments')
    op.drop_index('idx_message_attachment_message', 'message_attachments')
    op.drop_index('idx_pending_task_priority', 'pending_tasks')
    op.drop_index('idx_pending_task_assignee', 'pending_tasks')
    op.drop_index('idx_pending_task_status', 'pending_tasks')
    op.drop_index('idx_pending_task_type', 'pending_tasks')
    op.drop_index('idx_consultation_type_new', 'consultation_records')
    op.drop_index('idx_consultation_consultant', 'consultation_records')
    op.drop_index('idx_consultation_customer', 'consultation_records')
    op.drop_index('idx_consultation_conversation', 'consultation_records')
    op.drop_index('idx_dh_agent_priority', 'digital_human_agent_configs')
    op.drop_index('idx_dh_agent_config', 'digital_human_agent_configs')
    op.drop_index('idx_dh_agent_digital_human', 'digital_human_agent_configs')
    op.drop_index('idx_digital_human_type', 'digital_humans')
    op.drop_index('idx_digital_human_status', 'digital_humans')
    op.drop_index('idx_digital_human_user', 'digital_humans')
    
    # 删除表
    op.drop_table('message_attachments')
    op.drop_table('pending_tasks')
    op.drop_table('consultation_records')
    op.drop_table('digital_human_agent_configs')
    op.drop_table('digital_humans')
    
    # 删除添加的agent_configs字段
    try:
        op.drop_column('agent_configs', 'capabilities')
        op.drop_column('agent_configs', 'agent_type')
    except:
        pass
