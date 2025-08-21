"""创建通讯录表结构

Revision ID: ea045294461a
Revises: add_missing_fields_simple
Create Date: 2025-08-20 11:10:35.991052

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ea045294461a'
down_revision: Union[str, None] = 'add_missing_fields_simple'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 创建枚举类型
    op.execute("CREATE TYPE friendship_status AS ENUM ('pending', 'accepted', 'blocked', 'deleted')")
    op.execute("CREATE TYPE tag_category AS ENUM ('work', 'personal', 'business', 'medical', 'custom')")
    op.execute("CREATE TYPE group_type AS ENUM ('personal', 'work', 'project', 'temporary')")
    op.execute("CREATE TYPE group_member_role AS ENUM ('member', 'admin', 'owner')")
    op.execute("CREATE TYPE interaction_type AS ENUM ('chat_started', 'message_sent', 'call_made', 'meeting_scheduled', 'profile_viewed', 'tag_added', 'group_added')")
    
    # 创建好友关系表
    op.create_table(
        'friendships',
        sa.Column('id', sa.String(36), primary_key=True, comment='好友关系ID'),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, comment='用户ID'),
        sa.Column('friend_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, comment='好友用户ID'),
        sa.Column('status', sa.Enum('pending', 'accepted', 'blocked', 'deleted', name='friendship_status'), default='pending', comment='好友状态：待确认、已接受、已屏蔽、已删除'),
        sa.Column('nickname', sa.String(100), nullable=True, comment='给好友设置的昵称'),
        sa.Column('remark', sa.Text(), nullable=True, comment='好友备注'),
        sa.Column('source', sa.String(50), nullable=True, comment='添加来源：search、qr_code、recommendation等'),
        sa.Column('is_starred', sa.Boolean(), default=False, comment='是否星标好友'),
        sa.Column('is_muted', sa.Boolean(), default=False, comment='是否免打扰'),
        sa.Column('is_pinned', sa.Boolean(), default=False, comment='是否置顶显示'),
        sa.Column('is_blocked', sa.Boolean(), default=False, comment='是否已屏蔽'),
        sa.Column('requested_at', sa.DateTime(timezone=True), server_default=sa.func.now(), comment='请求时间'),
        sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True, comment='接受时间'),
        sa.Column('last_interaction_at', sa.DateTime(timezone=True), nullable=True, comment='最后互动时间'),
        sa.Column('interaction_count', sa.Integer(), default=0, comment='互动次数'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment='更新时间'),
        comment='好友关系表，存储用户间的好友关系'
    )
    
    # 创建联系人标签表
    op.create_table(
        'contact_tags',
        sa.Column('id', sa.String(36), primary_key=True, comment='标签ID'),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, comment='创建用户ID'),
        sa.Column('name', sa.String(50), nullable=False, comment='标签名称'),
        sa.Column('color', sa.String(7), default='#3B82F6', comment='标签颜色（HEX格式）'),
        sa.Column('icon', sa.String(50), nullable=True, comment='标签图标'),
        sa.Column('description', sa.String(200), nullable=True, comment='标签描述'),
        sa.Column('category', sa.Enum('work', 'personal', 'business', 'medical', 'custom', name='tag_category'), default='custom', comment='标签分类'),
        sa.Column('is_system_tag', sa.Boolean(), default=False, comment='是否系统预设标签'),
        sa.Column('display_order', sa.Integer(), default=0, comment='显示顺序'),
        sa.Column('is_visible', sa.Boolean(), default=True, comment='是否可见'),
        sa.Column('usage_count', sa.Integer(), default=0, comment='使用次数'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment='更新时间'),
        comment='联系人标签表，用户自定义的好友分类'
    )
    
    # 创建好友标签关联表
    op.create_table(
        'friendship_tags',
        sa.Column('id', sa.String(36), primary_key=True, comment='关联ID'),
        sa.Column('friendship_id', sa.String(36), sa.ForeignKey('friendships.id', ondelete='CASCADE'), nullable=False, comment='好友关系ID'),
        sa.Column('tag_id', sa.String(36), sa.ForeignKey('contact_tags.id', ondelete='CASCADE'), nullable=False, comment='标签ID'),
        sa.Column('assigned_at', sa.DateTime(timezone=True), server_default=sa.func.now(), comment='分配时间'),
        sa.Column('assigned_by', sa.String(36), sa.ForeignKey('users.id'), nullable=True, comment='分配人（支持系统自动分配）'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment='更新时间'),
        comment='好友标签关联表，建立好友与标签的多对多关系'
    )
    
    # 创建联系人分组表
    op.create_table(
        'contact_groups',
        sa.Column('id', sa.String(36), primary_key=True, comment='分组ID'),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, comment='创建用户ID'),
        sa.Column('name', sa.String(100), nullable=False, comment='分组名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='分组描述'),
        sa.Column('avatar', sa.String(1024), nullable=True, comment='分组头像URL'),
        sa.Column('group_type', sa.Enum('personal', 'work', 'project', 'temporary', name='group_type'), default='personal', comment='分组类型'),
        sa.Column('color_theme', sa.String(7), default='#3B82F6', comment='分组主题色'),
        sa.Column('display_order', sa.Integer(), default=0, comment='显示顺序'),
        sa.Column('is_collapsed', sa.Boolean(), default=False, comment='是否折叠显示'),
        sa.Column('max_members', sa.Integer(), nullable=True, comment='最大成员数（可选限制）'),
        sa.Column('is_private', sa.Boolean(), default=False, comment='是否私有分组'),
        sa.Column('member_count', sa.Integer(), default=0, comment='当前成员数'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment='更新时间'),
        comment='联系人分组表，用户自定义的好友分组'
    )
    
    # 创建分组成员表
    op.create_table(
        'contact_group_members',
        sa.Column('id', sa.String(36), primary_key=True, comment='关联ID'),
        sa.Column('group_id', sa.String(36), sa.ForeignKey('contact_groups.id', ondelete='CASCADE'), nullable=False, comment='分组ID'),
        sa.Column('friendship_id', sa.String(36), sa.ForeignKey('friendships.id', ondelete='CASCADE'), nullable=False, comment='好友关系ID'),
        sa.Column('role', sa.Enum('member', 'admin', 'owner', name='group_member_role'), default='member', comment='在分组中的角色'),
        sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.func.now(), comment='加入时间'),
        sa.Column('invited_by', sa.String(36), sa.ForeignKey('users.id'), nullable=True, comment='邀请人ID'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment='更新时间'),
        comment='分组成员表，建立分组与好友的关联'
    )
    
    # 创建联系人隐私设置表
    op.create_table(
        'contact_privacy_settings',
        sa.Column('id', sa.String(36), primary_key=True, comment='设置ID'),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, comment='用户ID'),
        sa.Column('allow_search_by_phone', sa.Boolean(), default=True, comment='允许通过手机号搜索'),
        sa.Column('allow_search_by_email', sa.Boolean(), default=True, comment='允许通过邮箱搜索'),
        sa.Column('allow_search_by_username', sa.Boolean(), default=True, comment='允许通过用户名搜索'),
        sa.Column('auto_accept_from_contacts', sa.Boolean(), default=False, comment='自动接受通讯录好友请求'),
        sa.Column('require_verification_message', sa.Boolean(), default=True, comment='要求验证消息'),
        sa.Column('show_online_status', sa.Boolean(), default=True, comment='显示在线状态'),
        sa.Column('show_last_seen', sa.Boolean(), default=False, comment='显示最后在线时间'),
        sa.Column('show_profile_to_friends', sa.Boolean(), default=True, comment='向好友显示详细资料'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment='更新时间'),
        comment='联系人隐私设置表，管理用户的通讯录隐私配置'
    )
    
    # 创建互动记录表
    op.create_table(
        'interaction_records',
        sa.Column('id', sa.String(36), primary_key=True, comment='记录ID'),
        sa.Column('friendship_id', sa.String(36), sa.ForeignKey('friendships.id', ondelete='CASCADE'), nullable=False, comment='好友关系ID'),
        sa.Column('interaction_type', sa.Enum('chat_started', 'message_sent', 'call_made', 'meeting_scheduled', 'profile_viewed', 'tag_added', 'group_added', name='interaction_type'), nullable=False, comment='互动类型'),
        sa.Column('related_object_type', sa.String(50), nullable=True, comment='关联对象类型：conversation、message、task等'),
        sa.Column('related_object_id', sa.String(36), nullable=True, comment='关联对象ID'),
        sa.Column('interaction_data', sa.JSON(), nullable=True, comment='互动相关数据'),
        sa.Column('occurred_at', sa.DateTime(timezone=True), server_default=sa.func.now(), comment='发生时间'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment='创建时间'),
        comment='互动记录表，跟踪好友间的互动历史'
    )
    
    # 创建索引
    op.create_index('idx_friendship_user_friend', 'friendships', ['user_id', 'friend_id'])
    op.create_index('idx_friendship_status', 'friendships', ['status'])
    op.create_index('idx_friendship_created_at', 'friendships', ['created_at'])
    op.create_index('idx_friendship_last_interaction', 'friendships', ['last_interaction_at'])
    
    op.create_index('idx_contact_tag_user', 'contact_tags', ['user_id'])
    op.create_index('idx_contact_tag_category', 'contact_tags', ['category'])
    op.create_index('idx_contact_tag_usage', 'contact_tags', ['usage_count'])
    
    op.create_index('idx_friendship_tag_friendship', 'friendship_tags', ['friendship_id'])
    op.create_index('idx_friendship_tag_tag', 'friendship_tags', ['tag_id'])
    
    op.create_index('idx_contact_group_user', 'contact_groups', ['user_id'])
    op.create_index('idx_contact_group_type', 'contact_groups', ['group_type'])
    
    op.create_index('idx_group_member_group', 'contact_group_members', ['group_id'])
    op.create_index('idx_group_member_friendship', 'contact_group_members', ['friendship_id'])
    
    op.create_index('idx_privacy_setting_user', 'contact_privacy_settings', ['user_id'])
    
    op.create_index('idx_interaction_friendship', 'interaction_records', ['friendship_id'])
    op.create_index('idx_interaction_type', 'interaction_records', ['interaction_type'])
    op.create_index('idx_interaction_occurred_at', 'interaction_records', ['occurred_at'])
    
    # 创建唯一约束
    op.create_unique_constraint('uq_friendship_pair', 'friendships', ['user_id', 'friend_id'])
    op.create_unique_constraint('uq_contact_tag_user_name', 'contact_tags', ['user_id', 'name'])
    op.create_unique_constraint('uq_friendship_tag_pair', 'friendship_tags', ['friendship_id', 'tag_id'])
    op.create_unique_constraint('uq_contact_group_user_name', 'contact_groups', ['user_id', 'name'])
    op.create_unique_constraint('uq_group_member_pair', 'contact_group_members', ['group_id', 'friendship_id'])
    op.create_unique_constraint('uq_privacy_setting_user', 'contact_privacy_settings', ['user_id'])


def downgrade() -> None:
    # 删除表（按依赖关系逆序删除）
    op.drop_table('interaction_records')
    op.drop_table('contact_privacy_settings')
    op.drop_table('contact_group_members')
    op.drop_table('contact_groups')
    op.drop_table('friendship_tags')
    op.drop_table('contact_tags')
    op.drop_table('friendships')
    
    # 删除枚举类型
    op.execute("DROP TYPE IF EXISTS interaction_type")
    op.execute("DROP TYPE IF EXISTS group_member_role")
    op.execute("DROP TYPE IF EXISTS group_type")
    op.execute("DROP TYPE IF EXISTS tag_category")
    op.execute("DROP TYPE IF EXISTS friendship_status")
