"""添加创建人和修改人字段到BaseModel

Revision ID: 9c59fee21a1d
Revises: 5e40eb248348
Create Date: 2025-11-23 15:51:51.992108

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9c59fee21a1d'
down_revision: Union[str, None] = '5e40eb248348'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """为所有继承BaseModel的表添加created_by和updated_by字段"""
    
    # 定义所有需要添加字段的表（继承BaseModel的数据库表）
    tables = [
        'tenants',
        'roles',
        'permissions',
        'resources',
        'users',
        'doctors',
        'consultants',
        'operators',
        'administrators',
        'conversations',
        'messages',
        'conversation_participants',
        'system_settings',
        'mcp_tools',
        'mcp_call_logs',
        'digital_humans',
        'digital_human_agent_configs',
        'customers',
        'customer_profiles',
        'friendships',
        'contact_tags',
        'friendship_tags',
        'contact_groups',
        'contact_group_members',
        'contact_privacy_settings',
        'interaction_records',
        'upload_sessions',
        'upload_chunks',
        'message_attachments',
        'agent_configs',
        'user_preferences',
        'user_default_roles',
        'login_history',
    ]
    
    # pending_tasks 和 mcp_tool_groups 已经有 created_by 字段，只添加 updated_by
    tables_with_created_by = ['pending_tasks', 'mcp_tool_groups']
    
    # 为所有表添加 created_by 和 updated_by 字段
    for table_name in tables:
        try:
            # 检查字段是否已存在
            conn = op.get_bind()
            inspector = sa.inspect(conn)
            existing_columns = [col['name'] for col in inspector.get_columns(table_name)]
            
            if 'created_by' not in existing_columns:
                op.add_column(
                    table_name,
                    sa.Column('created_by', sa.String(36), 
                             sa.ForeignKey('users.id', ondelete='SET NULL'), 
                             nullable=True, 
                             comment='创建人ID')
                )
            
            if 'updated_by' not in existing_columns:
                op.add_column(
                    table_name,
                    sa.Column('updated_by', sa.String(36), 
                             sa.ForeignKey('users.id', ondelete='SET NULL'), 
                             nullable=True, 
                             comment='修改人ID')
                )
        except Exception as e:
            # 如果表不存在或字段已存在，跳过
            print(f"跳过表 {table_name}: {e}")
    
    # 为已有 created_by 的表只添加 updated_by
    for table_name in tables_with_created_by:
        try:
            conn = op.get_bind()
            inspector = sa.inspect(conn)
            existing_columns = [col['name'] for col in inspector.get_columns(table_name)]
            
            if 'updated_by' not in existing_columns:
                op.add_column(
                    table_name,
                    sa.Column('updated_by', sa.String(36), 
                             sa.ForeignKey('users.id', ondelete='SET NULL'), 
                             nullable=True, 
                             comment='修改人ID')
                )
        except Exception as e:
            print(f"跳过表 {table_name}: {e}")


def downgrade() -> None:
    """移除所有表的created_by和updated_by字段"""
    
    tables = [
        'tenants', 'roles', 'permissions', 'resources', 'users',
        'doctors', 'consultants', 'operators', 'administrators',
        'conversations', 'messages', 'conversation_participants',
        'pending_tasks', 'system_settings', 'mcp_tool_groups',
        'mcp_tools', 'mcp_call_logs', 'digital_humans',
        'digital_human_agent_configs', 'customers', 'customer_profiles',
        'friendships', 'contact_tags', 'friendship_tags',
        'contact_groups', 'contact_group_members', 'contact_privacy_settings',
        'interaction_records', 'upload_sessions', 'upload_chunks',
        'message_attachments', 'agent_configs', 'user_preferences',
        'user_default_roles', 'login_history',
    ]
    
    for table_name in tables:
        try:
            # 检查字段是否存在
            conn = op.get_bind()
            inspector = sa.inspect(conn)
            existing_columns = [col['name'] for col in inspector.get_columns(table_name)]
            
            if 'updated_by' in existing_columns:
                op.drop_column(table_name, 'updated_by')
            
            # pending_tasks 和 mcp_tool_groups 保留 created_by，其他表删除
            if table_name not in ['pending_tasks', 'mcp_tool_groups']:
                if 'created_by' in existing_columns:
                    op.drop_column(table_name, 'created_by')
        except Exception as e:
            print(f"跳过表 {table_name}: {e}")
