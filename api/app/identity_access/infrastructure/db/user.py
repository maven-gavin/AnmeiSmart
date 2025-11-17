from sqlalchemy import Boolean, Column, String, DateTime, ForeignKey, Table, Text, JSON, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.common.infrastructure.db.base_model import BaseModel
from app.common.infrastructure.db.base import Base
from app.common.infrastructure.db.uuid_utils import user_id, role_id, tenant_id, permission_id, resource_id
from app.identity_access.domain.enums import AdminLevel

# 用户-角色关联表 (使用String类型的外键)
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, comment="用户ID"),
    Column("role_id", String(36), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True, comment="角色ID"),
    Column("assigned_at", DateTime(timezone=True), server_default=func.now(), comment="分配时间")
)

# 角色-权限关联表 (使用String类型的外键)
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", String(36), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True, comment="角色ID"),
    Column("permission_id", String(36), ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True, comment="权限ID"),
)

# 资源-权限关联表 (使用String类型的外键)
resource_permissions = Table(
    "resource_permissions",
    Base.metadata,
    Column("resource_id", String(36), ForeignKey("resources.id", ondelete="CASCADE"), primary_key=True, comment="资源ID"),
    Column("permission_id", String(36), ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True, comment="权限ID"),
)

class Tenant(BaseModel):
    """租户数据库模型，存储系统中所有租户信息"""
    __tablename__ = "tenants"
    __table_args__ = {"comment": "租户表，存储系统所有租户信息"}

    id = Column(String(36), primary_key=True, default=tenant_id, comment="租户ID")
    name = Column(String(50), unique=True, index=True, nullable=False, comment="租户名称")
    display_name = Column(String(50), nullable=True, comment="租户显示名称")
    description = Column(String(255), nullable=True, comment="租户描述")
    tenant_type = Column(String(20), default="standard", comment="租户类型")
    status = Column(String(20), default="active", comment="租户状态")

    is_active = Column(Boolean, default=True, comment="是否启用")
    is_system = Column(Boolean, default=False, comment="是否系统租户")
    is_admin = Column(Boolean, default=False, comment="是否管理员租户")
    priority = Column(Integer, default=0, comment="租户优先级")

    encrypted_pub_key = Column(String(255), nullable=True, comment="加密公钥")
    contact_phone = Column(String(20), nullable=True, comment="负责人联系电话")
    contact_email = Column(String(50), nullable=True, comment="负责人邮箱")
    contact_name = Column(String(50), nullable=True, comment="负责人姓名")

    # 租户关联的用户
    users = relationship("User", back_populates="tenant")

class Role(BaseModel):
    """角色数据库模型，存储系统中所有角色信息"""
    __tablename__ = "roles"
    __table_args__ = {"comment": "角色表，存储系统所有角色信息"}

    id = Column(String(36), primary_key=True, default=role_id, comment="角色ID")
    name = Column(String(50), unique=True, index=True, nullable=False, comment="角色名称")
    display_name = Column(String(50), nullable=True, comment="角色显示名称")
    description = Column(String(255), nullable=True, comment="角色描述")
    is_active = Column(Boolean, default=True, comment="是否启用")
    is_system = Column(Boolean, default=False, comment="是否系统角色")
    is_admin = Column(Boolean, default=False, comment="是否管理员角色")
    priority = Column(Integer, default=0, comment="角色优先级")
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), comment="租户ID")

    # 角色关联的用户
    users = relationship("User", secondary="user_roles", back_populates="roles")
    # 权限关联
    permissions = relationship("Permission", secondary="role_permissions", back_populates="roles")

class Permission(BaseModel):
    """权限配置表，存储系统所有权限配置信息"""
    __tablename__ = "permissions"
    __table_args__ = {"comment": "权限配置表，存储系统所有权限配置信息"}
    
    id = Column(String(36), primary_key=True, default=permission_id, comment="权限ID")
    name = Column(String(50), unique=True, index=True, nullable=False, comment="权限名称")
    display_name = Column(String(50), nullable=True, comment="权限显示名称")
    description = Column(String(255), nullable=True, comment="权限描述")
    permission_type = Column(String(20), default="action", comment="权限类型")
    scope = Column(String(20), default="tenant", comment="权限范围")
    resource = Column(String(50), nullable=True, comment="权限资源")
    action = Column(String(50), nullable=True, comment="权限动作")
    
    is_active = Column(Boolean, default=True, comment="是否启用")
    is_system = Column(Boolean, default=False, comment="是否系统权限")
    is_admin = Column(Boolean, default=False, comment="是否管理员权限")
    priority = Column(Integer, default=0, comment="权限优先级")
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), comment="租户ID")

    # 权限关联的角色
    roles = relationship("Role", secondary="role_permissions", back_populates="permissions")
    # 权限关联的资源
    resources = relationship("Resource", secondary="resource_permissions", back_populates="permissions")


class Resource(BaseModel):
    """资源表：API端点和菜单项"""
    __tablename__ = "resources"
    __table_args__ = {"comment": "资源表，存储API端点和菜单项"}
    
    id = Column(String(36), primary_key=True, default=resource_id, comment="资源ID")
    name = Column(String(100), unique=True, index=True, nullable=False, comment="资源名称，如 menu:home, api:user:create")
    display_name = Column(String(50), nullable=True, comment="资源显示名称")
    description = Column(String(255), nullable=True, comment="资源描述")
    resource_type = Column(String(20), nullable=False, comment="资源类型：api 或 menu")
    resource_path = Column(String(255), nullable=False, comment="API路径或菜单路径")
    http_method = Column(String(10), nullable=True, comment="HTTP方法：GET, POST, PUT, DELETE（仅API资源）")
    parent_id = Column(String(36), ForeignKey("resources.id", ondelete="SET NULL"), nullable=True, comment="父资源ID（菜单层级）")
    
    is_active = Column(Boolean, default=True, comment="是否启用")
    is_system = Column(Boolean, default=False, comment="是否系统资源")
    priority = Column(Integer, default=0, comment="资源优先级")
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, comment="租户ID")
    
    # 资源关联的权限
    permissions = relationship("Permission", secondary="resource_permissions", back_populates="resources")
    # 子资源（菜单层级）
    children = relationship("Resource", backref="parent", remote_side=[id])


class User(BaseModel):
    """用户基础数据库模型，存储所有类型用户共有的信息"""
    __tablename__ = "users"
    __table_args__ = {"comment": "用户表，存储所有用户基础信息"}

    id = Column(String(36), primary_key=True, default=user_id, comment="用户ID")
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), comment="租户ID")
    email = Column(String, unique=True, index=True, nullable=False, comment="邮箱")
    username = Column(String, unique=True, index=True, nullable=False, comment="用户名")
    hashed_password = Column(String, nullable=False, comment="加密密码")
    phone = Column(String, unique=True, index=True, nullable=True, comment="手机号")
    avatar = Column(String, nullable=True, comment="头像URL")
    is_active = Column(Boolean, default=True, comment="是否激活")
    
    # 租户关联
    tenant = relationship("Tenant", back_populates="users")
    
    # 用户角色关联
    roles = relationship("Role", secondary="user_roles", back_populates="users")
    
    # 扩展表关联
    customer = relationship("app.customer.infrastructure.db.customer.Customer", back_populates="user", uselist=False, cascade="all, delete-orphan")
    doctor = relationship("Doctor", back_populates="user", uselist=False, cascade="all, delete-orphan")
    consultant = relationship("Consultant", back_populates="user", uselist=False, cascade="all, delete-orphan")
    operator = relationship("Operator", back_populates="user", uselist=False, cascade="all, delete-orphan")
    administrator = relationship("Administrator", back_populates="user", uselist=False, cascade="all, delete-orphan")
    
    # 上传会话关联
    upload_sessions = relationship("app.common.infrastructure.db.upload.UploadSession", back_populates="user", cascade="all, delete-orphan")
    
    # 数字人关联（新增）
    digital_humans = relationship("app.digital_humans.infrastructure.db.digital_human.DigitalHuman", back_populates="user", cascade="all, delete-orphan")
    owned_conversations = relationship("app.chat.infrastructure.db.chat.Conversation", foreign_keys="app.chat.infrastructure.db.chat.Conversation.owner_id", back_populates="owner")
    
    # 通讯录关联（新增）
    friendships = relationship("app.contacts.infrastructure.db.contacts.Friendship", foreign_keys="app.contacts.infrastructure.db.contacts.Friendship.user_id", 
                              back_populates="user", cascade="all, delete-orphan")
    contact_tags = relationship("app.contacts.infrastructure.db.contacts.ContactTag", back_populates="user", cascade="all, delete-orphan")
    contact_groups = relationship("app.contacts.infrastructure.db.contacts.ContactGroup", back_populates="user", cascade="all, delete-orphan")
    contact_privacy_setting = relationship("app.contacts.infrastructure.db.contacts.ContactPrivacySetting", back_populates="user", 
                                          uselist=False, cascade="all, delete-orphan")

class Doctor(BaseModel):
    """医生特有信息表，存储医生扩展信息"""
    __tablename__ = "doctors"
    __table_args__ = {"comment": "医生表，存储医生扩展信息"}
    
    user_id = Column(String(36), ForeignKey("users.id"), unique=True, nullable=False, comment="用户ID")
    specialization = Column(String, nullable=True, comment="专科方向")
    certification = Column(String, nullable=True, comment="资格证书")
    license_number = Column(String, nullable=True, comment="执业证号")
    
    # 关联到基础用户表
    user = relationship("User", back_populates="doctor")

class Consultant(BaseModel):
    """医美顾问特有信息表，存储顾问扩展信息"""
    __tablename__ = "consultants"
    __table_args__ = {"comment": "医美顾问表，存储顾问扩展信息"}
    
    user_id = Column(String(36), ForeignKey("users.id"), unique=True, nullable=False, comment="用户ID")
    expertise = Column(String, nullable=True, comment="专长领域")
    performance_metrics = Column(Text, nullable=True, comment="业绩指标")
    
    # 关联到基础用户表
    user = relationship("User", back_populates="consultant")

class Operator(BaseModel):
    """机构运营人员特有信息表，存储运营人员扩展信息"""
    __tablename__ = "operators"
    __table_args__ = {"comment": "运营人员表，存储机构运营人员扩展信息"}
    
    user_id = Column(String(36), ForeignKey("users.id"), unique=True, nullable=False, comment="用户ID")
    department = Column(String, nullable=True, comment="所属部门")
    responsibilities = Column(Text, nullable=True, comment="职责描述")
    
    # 关联到基础用户表
    user = relationship("User", back_populates="operator")

class Administrator(BaseModel):
    """系统管理员特有信息表，存储管理员扩展信息"""
    __tablename__ = "administrators"
    __table_args__ = {"comment": "系统管理员表，存储管理员扩展信息"}
    
    user_id = Column(String(36), ForeignKey("users.id"), unique=True, nullable=False, comment="用户ID")
    admin_level = Column(String, default=AdminLevel.BASIC, comment="管理员级别")
    access_permissions = Column(Text, nullable=True, comment="权限描述")
    
    # 关联到基础用户表
    user = relationship("User", back_populates="administrator") 