from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, JSON, Integer, Index, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.common.infrastructure.db.base_model import BaseModel
from app.common.infrastructure.db.uuid_utils import friendship_id, tag_id, group_id, relation_id, record_id, setting_id


class Friendship(BaseModel):
    """好友关系聚合根 - 管理用户间的好友关系"""
    __tablename__ = "friendships"
    __table_args__ = (
        Index('idx_friendship_user_friend', 'user_id', 'friend_id'),
        Index('idx_friendship_status', 'status'),
        Index('idx_friendship_created_at', 'created_at'),
        Index('idx_friendship_last_interaction', 'last_interaction_at'),
        UniqueConstraint('user_id', 'friend_id', name='uq_friendship_pair'),
        {"comment": "好友关系表，存储用户间的好友关系"}
    )

    id = Column(String(36), primary_key=True, default=friendship_id, comment="好友关系ID")
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), 
                    nullable=False, comment="用户ID")
    friend_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), 
                      nullable=False, comment="好友用户ID")
    
    # 关系状态
    status = Column(String(20), default="pending", comment="好友状态：待确认、已接受、已屏蔽、已删除")
    
    # 关系元数据
    nickname = Column(String(100), nullable=True, comment="给好友设置的昵称")
    remark = Column(Text, nullable=True, comment="好友备注")
    source = Column(String(50), nullable=True, comment="添加来源：search、qr_code、recommendation等")
    
    # 关系设置
    is_starred = Column(Boolean, default=False, comment="是否星标好友")
    is_muted = Column(Boolean, default=False, comment="是否免打扰")
    is_pinned = Column(Boolean, default=False, comment="是否置顶显示")
    is_blocked = Column(Boolean, default=False, comment="是否已屏蔽")
    
    # 时间信息
    requested_at = Column(DateTime(timezone=True), server_default=func.now(), comment="请求时间")
    accepted_at = Column(DateTime(timezone=True), nullable=True, comment="接受时间")
    last_interaction_at = Column(DateTime(timezone=True), nullable=True, comment="最后互动时间")
    
    # 统计信息
    interaction_count = Column(Integer, default=0, comment="互动次数")
    
    # 关联关系
    user = relationship("app.identity_access.infrastructure.db.user.User", foreign_keys=[user_id], back_populates="friendships")
    friend = relationship("app.identity_access.infrastructure.db.user.User", foreign_keys=[friend_id])
    tags = relationship("app.contacts.infrastructure.db.contacts.FriendshipTag", back_populates="friendship", cascade="all, delete-orphan")
    group_memberships = relationship("app.contacts.infrastructure.db.contacts.ContactGroupMember", back_populates="friendship", cascade="all, delete-orphan")
    interaction_records = relationship("app.contacts.infrastructure.db.contacts.InteractionRecord", back_populates="friendship", cascade="all, delete-orphan")


class ContactTag(BaseModel):
    """联系人标签实体 - 用户自定义的好友分类标签"""
    __tablename__ = "contact_tags"
    __table_args__ = (
        Index('idx_contact_tag_user', 'user_id'),
        Index('idx_contact_tag_category', 'category'),
        Index('idx_contact_tag_usage', 'usage_count'),
        UniqueConstraint('user_id', 'name', name='uq_contact_tag_user_name'),
        {"comment": "联系人标签表，用户自定义的好友分类"}
    )

    id = Column(String(36), primary_key=True, default=tag_id, comment="标签ID")
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), 
                    nullable=False, comment="创建用户ID")
    
    # 标签信息
    name = Column(String(50), nullable=False, comment="标签名称")
    color = Column(String(7), default="#3B82F6", comment="标签颜色（HEX格式）")
    icon = Column(String(50), nullable=True, comment="标签图标")
    description = Column(String(200), nullable=True, comment="标签描述")
    
    # 标签分类
    category = Column(String(20), default="custom", comment="标签分类")
    
    # 显示设置
    is_system_tag = Column(Boolean, default=False, comment="是否系统预设标签")
    display_order = Column(Integer, default=0, comment="显示顺序")
    is_visible = Column(Boolean, default=True, comment="是否可见")
    
    # 统计信息
    usage_count = Column(Integer, default=0, comment="使用次数")
    
    # 关联关系
    user = relationship("app.identity_access.infrastructure.db.user.User", back_populates="contact_tags")
    friendship_tags = relationship("app.contacts.infrastructure.db.contacts.FriendshipTag", back_populates="tag", cascade="all, delete-orphan")


class FriendshipTag(BaseModel):
    """好友标签关联表 - 多对多关系"""
    __tablename__ = "friendship_tags"
    __table_args__ = (
        Index('idx_friendship_tag_friendship', 'friendship_id'),
        Index('idx_friendship_tag_tag', 'tag_id'),
        UniqueConstraint('friendship_id', 'tag_id', name='uq_friendship_tag_pair'),
        {"comment": "好友标签关联表，建立好友与标签的多对多关系"}
    )

    id = Column(String(36), primary_key=True, default=relation_id, comment="关联ID")
    friendship_id = Column(String(36), ForeignKey("friendships.id", ondelete="CASCADE"), 
                          nullable=False, comment="好友关系ID")
    tag_id = Column(String(36), ForeignKey("contact_tags.id", ondelete="CASCADE"), 
                   nullable=False, comment="标签ID")
    
    # 关联元数据
    assigned_at = Column(DateTime(timezone=True), server_default=func.now(), comment="分配时间")
    assigned_by = Column(String(36), ForeignKey("users.id"), nullable=True, comment="分配人（支持系统自动分配）")
    
    # 关联关系
    friendship = relationship("app.contacts.infrastructure.db.friendship.Friendship", back_populates="tags")
    tag = relationship("app.contacts.infrastructure.db.contacts.ContactTag", back_populates="friendship_tags")
    assigned_by_user = relationship("app.identity_access.infrastructure.db.user.User", foreign_keys=[assigned_by])


class ContactGroup(BaseModel):
    """联系人分组实体 - 用户自定义的好友分组"""
    __tablename__ = "contact_groups"
    __table_args__ = (
        Index('idx_contact_group_user', 'user_id'),
        Index('idx_contact_group_type', 'group_type'),
        UniqueConstraint('user_id', 'name', name='uq_contact_group_user_name'),
        {"comment": "联系人分组表，用户自定义的好友分组"}
    )

    id = Column(String(36), primary_key=True, default=group_id, comment="分组ID")
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), 
                    nullable=False, comment="创建用户ID")
    
    # 分组信息
    name = Column(String(100), nullable=False, comment="分组名称")
    description = Column(Text, nullable=True, comment="分组描述")
    avatar = Column(String(1024), nullable=True, comment="分组头像URL")
    
    # 分组类型
    group_type = Column(String(20), default="personal", comment="分组类型")
    
    # 显示设置
    color_theme = Column(String(7), default="#3B82F6", comment="分组主题色")
    display_order = Column(Integer, default=0, comment="显示顺序")
    is_collapsed = Column(Boolean, default=False, comment="是否折叠显示")
    
    # 分组设置
    max_members = Column(Integer, nullable=True, comment="最大成员数（可选限制）")
    is_private = Column(Boolean, default=False, comment="是否私有分组")
    
    # 统计信息
    member_count = Column(Integer, default=0, comment="当前成员数")
    
    # 关联关系
    user = relationship("app.identity_access.infrastructure.db.user.User", back_populates="contact_groups")
    members = relationship("app.contacts.infrastructure.db.contacts.ContactGroupMember", back_populates="group", cascade="all, delete-orphan")


class ContactGroupMember(BaseModel):
    """分组成员关联表"""
    __tablename__ = "contact_group_members"
    __table_args__ = (
        Index('idx_group_member_group', 'group_id'),
        Index('idx_group_member_friendship', 'friendship_id'),
        UniqueConstraint('group_id', 'friendship_id', name='uq_group_member_pair'),
        {"comment": "分组成员表，建立分组与好友的关联"}
    )

    id = Column(String(36), primary_key=True, default=relation_id, comment="关联ID")
    group_id = Column(String(36), ForeignKey("contact_groups.id", ondelete="CASCADE"), 
                     nullable=False, comment="分组ID")
    friendship_id = Column(String(36), ForeignKey("friendships.id", ondelete="CASCADE"), 
                          nullable=False, comment="好友关系ID")
    
    # 成员角色
    role = Column(String(20), default="member", comment="在分组中的角色")
    
    # 加入信息
    joined_at = Column(DateTime(timezone=True), server_default=func.now(), comment="加入时间")
    invited_by = Column(String(36), ForeignKey("users.id"), nullable=True, comment="邀请人ID")
    
    # 关联关系
    group = relationship("app.contacts.infrastructure.db.contacts.ContactGroup", back_populates="members")
    friendship = relationship("app.contacts.infrastructure.db.friendship.Friendship", back_populates="group_memberships")
    invited_by_user = relationship("app.identity_access.infrastructure.db.user.User", foreign_keys=[invited_by])


class ContactPrivacySetting(BaseModel):
    """联系人隐私设置实体"""
    __tablename__ = "contact_privacy_settings"
    __table_args__ = (
        Index('idx_privacy_setting_user', 'user_id'),
        UniqueConstraint('user_id', name='uq_privacy_setting_user'),
        {"comment": "联系人隐私设置表，管理用户的通讯录隐私配置"}
    )

    id = Column(String(36), primary_key=True, default=setting_id, comment="设置ID")
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), 
                    nullable=False, comment="用户ID")
    
    # 可发现性设置
    allow_search_by_phone = Column(Boolean, default=True, comment="允许通过手机号搜索")
    allow_search_by_email = Column(Boolean, default=True, comment="允许通过邮箱搜索")
    allow_search_by_username = Column(Boolean, default=True, comment="允许通过用户名搜索")
    
    # 好友请求设置
    auto_accept_from_contacts = Column(Boolean, default=False, comment="自动接受通讯录好友请求")
    require_verification_message = Column(Boolean, default=True, comment="要求验证消息")
    
    # 信息可见性
    show_online_status = Column(Boolean, default=True, comment="显示在线状态")
    show_last_seen = Column(Boolean, default=False, comment="显示最后在线时间")
    show_profile_to_friends = Column(Boolean, default=True, comment="向好友显示详细资料")
    
    # 关联关系
    user = relationship("app.identity_access.infrastructure.db.user.User", back_populates="contact_privacy_setting", uselist=False)


class InteractionRecord(BaseModel):
    """互动记录表"""
    __tablename__ = "interaction_records"
    __table_args__ = (
        Index('idx_interaction_friendship', 'friendship_id'),
        Index('idx_interaction_type', 'interaction_type'),
        Index('idx_interaction_occurred_at', 'occurred_at'),
        {"comment": "互动记录表，跟踪好友间的互动历史"}
    )

    id = Column(String(36), primary_key=True, default=record_id, comment="记录ID")
    friendship_id = Column(String(36), ForeignKey("friendships.id", ondelete="CASCADE"), 
                          nullable=False, comment="好友关系ID")
    
    # 互动类型
    interaction_type = Column(String(50), nullable=False, comment="互动类型")
    
    # 关联对象
    related_object_type = Column(String(50), nullable=True, comment="关联对象类型：conversation、message、task等")
    related_object_id = Column(String(36), nullable=True, comment="关联对象ID")
    
    # 互动内容
    interaction_data = Column(JSON, nullable=True, comment="互动相关数据")
    
    # 时间信息
    occurred_at = Column(DateTime(timezone=True), server_default=func.now(), comment="发生时间")
    
    # 关联关系
    friendship = relationship("app.contacts.infrastructure.db.friendship.Friendship", back_populates="interaction_records")
