from sqlalchemy import Boolean, Column, String, DateTime, ForeignKey, Table, Text, JSON, Integer, UniqueConstraint, Enum
from sqlalchemy.orm import relationship, foreign, remote
from sqlalchemy.sql import func, and_

from app.common.models.base_model import BaseModel
from app.common.deps.database import Base
from app.common.deps.uuid_utils import user_id, role_id, tenant_id, permission_id, resource_id
from app.identity_access.enums import AdminLevel, TenantStatus, UserStatus, PermissionType, PermissionScope

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
    status = Column(Enum(TenantStatus, values_callable=lambda obj: [e.value for e in obj]), default=TenantStatus.ACTIVE, comment="租户状态")

    is_system = Column(Boolean, default=False, comment="是否系统租户")
    is_admin = Column(Boolean, default=False, comment="是否管理员租户")
    priority = Column(Integer, default=0, comment="租户优先级")

    encrypted_pub_key = Column(String(255), nullable=True, comment="加密公钥")
    contact_phone = Column(String(20), nullable=True, comment="负责人联系电话")
    contact_email = Column(String(50), nullable=True, comment="负责人邮箱")
    contact_name = Column(String(50), nullable=True, comment="负责人姓名")

    # 租户关联的用户（明确指定使用 User.tenant_id 作为外键）
    users = relationship("User", primaryjoin="Tenant.id == User.tenant_id", back_populates="tenant")
    # 租户关联的角色（资源和权限是全局的，不再关联租户）
    roles = relationship("Role", primaryjoin="Tenant.id == Role.tenant_id", back_populates="tenant")

class Role(BaseModel):
    """角色数据库模型，存储系统中所有角色信息"""
    __tablename__ = "roles"
    __table_args__ = (
        UniqueConstraint('name', 'tenant_id', name='uq_role_name_tenant'),
        {"comment": "角色表，存储系统所有角色信息"}
    )

    id = Column(String(36), primary_key=True, default=role_id, comment="角色ID")
    name = Column(String(50), index=True, nullable=False, comment="角色名称")
    display_name = Column(String(50), nullable=True, comment="角色显示名称")
    description = Column(String(255), nullable=True, comment="角色描述")
    is_active = Column(Boolean, default=True, comment="是否启用")
    is_system = Column(Boolean, default=False, comment="是否系统角色")
    is_admin = Column(Boolean, default=False, comment="是否管理员角色")
    priority = Column(Integer, default=0, comment="角色优先级")
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), default="system", comment="租户ID")

    # 租户关联
    tenant = relationship("Tenant", primaryjoin="Role.tenant_id == Tenant.id", back_populates="roles")
    # 角色关联的用户
    users = relationship("User", secondary="user_roles", back_populates="roles")
    # 权限关联
    permissions = relationship("Permission", secondary="role_permissions", back_populates="roles")

class Permission(BaseModel):
    """权限配置表，存储系统所有权限配置信息（全局，不区分租户）"""
    __tablename__ = "permissions"
    __table_args__ = (
        UniqueConstraint('code', name='uq_permission_code'),
        UniqueConstraint('name', name='uq_permission_name'),
        {"comment": "权限配置表，存储系统所有权限配置信息（全局）"}
    )
    
    id = Column(String(36), primary_key=True, default=permission_id, comment="权限ID")
    code = Column(String(100), unique=True, index=True, nullable=False, comment="权限标识码，如 user:create")
    name = Column(String(50), unique=True, index=True, nullable=False, comment="权限名称")
    display_name = Column(String(50), nullable=True, comment="权限显示名称")
    description = Column(String(255), nullable=True, comment="权限描述")
    permission_type = Column(Enum(PermissionType, values_callable=lambda obj: [e.value for e in obj]), default=PermissionType.ACTION, comment="权限类型")
    scope = Column(Enum(PermissionScope, values_callable=lambda obj: [e.value for e in obj]), default=PermissionScope.TENANT, comment="权限范围")
    
    is_active = Column(Boolean, default=True, comment="是否启用")
    is_system = Column(Boolean, default=False, comment="是否系统权限")
    is_admin = Column(Boolean, default=False, comment="是否管理员权限")
    priority = Column(Integer, default=0, comment="权限优先级")

    # 权限关联的角色
    roles = relationship("Role", secondary="role_permissions", back_populates="permissions")
    # 权限关联的资源
    resources = relationship("Resource", secondary="resource_permissions", back_populates="permissions")


class Resource(BaseModel):
    """资源表：API端点和菜单项（全局，不区分租户）"""
    __tablename__ = "resources"
    __table_args__ = (
        UniqueConstraint('resource_path', 'http_method', name='uq_resource_path_method'),
        {"comment": "资源表，存储API端点和菜单项（全局）"}
    )
    
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
    
    # 资源关联的权限
    permissions = relationship("Permission", secondary="resource_permissions", back_populates="resources")
    # 子资源（菜单层级）
    children = relationship("Resource", backref="parent", remote_side=[id])


class User(BaseModel):
    """用户基础数据库模型，存储所有类型用户共有的信息"""
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint('email', 'tenant_id', name='uq_user_email_tenant'),
        UniqueConstraint('username', 'tenant_id', name='uq_user_username_tenant'),
        {"comment": "用户表，存储所有用户基础信息"}
    )

    id = Column(String(36), primary_key=True, default=user_id, comment="用户ID")
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), default="system", comment="租户ID")
    email = Column(String(255), index=True, nullable=False, comment="邮箱")
    username = Column(String(255), index=True, nullable=False, comment="用户名")
    hashed_password = Column(String(255), nullable=False, comment="加密密码")
    phone = Column(String(50), index=True, nullable=True, comment="手机号")
    avatar = Column(String(255), nullable=True, comment="头像URL")
    status = Column(Enum(UserStatus, values_callable=lambda obj: [e.value for e in obj]), default=UserStatus.PENDING, comment="用户状态")
    
    # 租户关联（明确指定使用 User.tenant_id 作为外键）
    tenant = relationship("Tenant", primaryjoin="User.tenant_id == Tenant.id", back_populates="users")
    
    # 用户角色关联
    roles = relationship("Role", secondary="user_roles", back_populates="users")
    
    # 扩展表关联
    # 使用 backref 自动生成，避免循环依赖
    # customer, doctor, consultant, operator, administrator 已在各自模型中定义
    
    # 上传会话关联
    # 使用 backref 自动生成，避免循环依赖
    # upload_sessions 已在 UploadSession 模型中定义
    
    # 数字人关联
    # 使用 backref 自动生成，避免循环依赖
    # digital_humans 已在 DigitalHuman 模型中定义
    owned_conversations = relationship("app.chat.models.chat.Conversation", foreign_keys="app.chat.models.chat.Conversation.owner_id", back_populates="owner")
    
    # 通讯录关联（新增）
    # 使用 backref 自动生成，避免循环依赖
    # friendships, contact_tags, contact_groups, contact_privacy_setting 已在 contacts 模块中定义

class Doctor(BaseModel):
    """医生特有信息表，存储医生扩展信息"""
    __tablename__ = "doctors"
    __table_args__ = {"comment": "医生表，存储医生扩展信息"}
    
    user_id = Column(String(36), ForeignKey("users.id"), unique=True, nullable=False, comment="用户ID")
    specialization = Column(String(255), nullable=True, comment="专科方向")
    certification = Column(String(255), nullable=True, comment="资格证书")
    license_number = Column(String(100), nullable=True, comment="执业证号")
    
    # 关联到基础用户表
    from sqlalchemy.orm import backref
    user = relationship("User", foreign_keys=[user_id], backref=backref("doctor", uselist=False, cascade="all, delete-orphan"))

class Consultant(BaseModel):
    """顾问特有信息表，存储顾问扩展信息"""
    __tablename__ = "consultants"
    __table_args__ = {"comment": "顾问表，存储顾问扩展信息"}
    
    user_id = Column(String(36), ForeignKey("users.id"), unique=True, nullable=False, comment="用户ID")
    expertise = Column(String(255), nullable=True, comment="专长领域")
    performance_metrics = Column(JSON, nullable=True, comment="业绩指标")
    
    # 关联到基础用户表
    from sqlalchemy.orm import backref
    user = relationship("User", foreign_keys=[user_id], backref=backref("consultant", uselist=False, cascade="all, delete-orphan"))

class Operator(BaseModel):
    """机构运营人员特有信息表，存储运营人员扩展信息"""
    __tablename__ = "operators"
    __table_args__ = {"comment": "运营人员表，存储机构运营人员扩展信息"}
    
    user_id = Column(String(36), ForeignKey("users.id"), unique=True, nullable=False, comment="用户ID")
    department = Column(String(100), nullable=True, comment="所属部门")
    responsibilities = Column(Text, nullable=True, comment="职责描述")
    
    # 关联到基础用户表
    from sqlalchemy.orm import backref
    user = relationship("User", foreign_keys=[user_id], backref=backref("operator", uselist=False, cascade="all, delete-orphan"))

class Administrator(BaseModel):
    """系统管理员特有信息表，存储管理员扩展信息"""
    __tablename__ = "administrators"
    __table_args__ = {"comment": "系统管理员表，存储管理员扩展信息"}
    
    user_id = Column(String(36), ForeignKey("users.id"), unique=True, nullable=False, comment="用户ID")
    admin_level = Column(String(20), default=AdminLevel.BASIC, comment="管理员级别")
    access_permissions = Column(JSON, nullable=True, comment="权限描述")
    
    # 关联到基础用户表
    from sqlalchemy.orm import backref
    user = relationship("User", foreign_keys=[user_id], backref=backref("administrator", uselist=False, cascade="all, delete-orphan"))
