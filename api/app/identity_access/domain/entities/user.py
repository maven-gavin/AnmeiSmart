"""
用户聚合根

用户是身份与权限上下文的核心聚合根，负责管理用户身份和基本信息。
"""

import uuid
from datetime import datetime
from typing import List, Optional, Set
from dataclasses import dataclass, field

from ..value_objects.email import Email
from ..value_objects.password import Password
from ..value_objects.user_status import UserStatus
from ..value_objects.role_type import RoleType


@dataclass
class UserEntity:
    """用户聚合根"""
    
    # 角色优先级（用于获取主要角色）
    _ROLE_PRIORITY = [
        RoleType.ADMINISTRATOR,
        RoleType.OPERATOR,
        RoleType.DOCTOR,
        RoleType.CONSULTANT,
        RoleType.CUSTOMER,
    ]
    
    # 身份标识
    id: str
    
    # 基本信息
    username: str
    email: Email
    password: Password
    phone: Optional[str] = None
    avatar: Optional[str] = None
    
    # 状态信息
    status: UserStatus = UserStatus.ACTIVE
    
    # 时间戳
    createdAt: datetime = field(default_factory=datetime.utcnow)
    updatedAt: datetime = field(default_factory=datetime.utcnow)
    lastLoginAt: Optional[datetime] = None
    
    # 角色集合（支持数据库配置的角色）
    roles: Set[str] = field(default_factory=set)
    
    # 租户关联
    tenantId: Optional[str] = None
    
    def __post_init__(self):
        """后初始化验证"""
        if not self.id or not self.id.strip():
            raise ValueError("用户ID不能为空")
        
        if not self.username or not self.username.strip():
            raise ValueError("用户名不能为空")
        
        # 确保有默认角色（如果没有指定角色）
        if not self.roles:
            self.roles = {RoleType.CUSTOMER.value}
    
    @staticmethod
    def _is_valid_role(role_name: str) -> bool:
        """检查角色名称是否有效"""
        valid_roles = {rt.value for rt in RoleType.get_all_roles()}
        return role_name in valid_roles
    
    def _update_timestamp(self) -> None:
        """更新修改时间戳"""
        self.updatedAt = datetime.utcnow()
    
    @classmethod
    def create(
        cls,
        username: str,
        email: str,
        password: str,
        phone: Optional[str] = None,
        avatar: Optional[str] = None,
        roles: Optional[List[str]] = None,
        tenantId: Optional[str] = None
    ) -> "UserEntity":
        """创建用户 - 工厂方法"""
        # 验证输入
        if not username or not username.strip():
            raise ValueError("用户名不能为空")
        
        if not email or not email.strip():
            raise ValueError("邮箱不能为空")
        
        if not password:
            raise ValueError("密码不能为空")
        
        # 创建值对象
        email_obj = Email(email.strip())
        password_obj = Password.create(password)
        
        # 处理角色：过滤有效角色
        role_set = {
            role for role in (roles or [])
            if cls._is_valid_role(role)
        }
        
        # 确保有默认角色
        if not role_set:
            role_set = {RoleType.CUSTOMER.value}
        
        return cls(
            id=str(uuid.uuid4()),
            username=username.strip(),
            email=email_obj,
            password=password_obj,
            phone=phone,
            avatar=avatar,
            roles=role_set,
            tenantId=tenantId
        )
    
    def update_profile(
        self,
        username: Optional[str] = None,
        phone: Optional[str] = None,
        avatar: Optional[str] = None
    ) -> None:
        """更新用户资料"""
        if username is not None:
            if not username.strip():
                raise ValueError("用户名不能为空")
            self.username = username.strip()
        
        if phone is not None:
            self.phone = phone
        
        if avatar is not None:
            self.avatar = avatar
        
        self._update_timestamp()
    
    def change_password(self, old_password: str, new_password: str) -> None:
        """修改密码"""
        if not self.password.verify(old_password):
            raise ValueError("原密码不正确")
        
        self.password = Password.create(new_password)
        self._update_timestamp()
    
    def activate(self) -> None:
        """激活用户"""
        self.status = UserStatus.ACTIVE
        self._update_timestamp()
    
    def deactivate(self) -> None:
        """停用用户"""
        self.status = UserStatus.INACTIVE
        self._update_timestamp()
    
    def suspend(self) -> None:
        """暂停用户"""
        self.status = UserStatus.SUSPENDED
        self._update_timestamp()
    
    def record_login(self) -> None:
        """记录登录时间"""
        self.lastLoginAt = datetime.utcnow()
        self._update_timestamp()
    
    def add_role(self, role_name: str) -> None:
        """添加角色"""
        if not self._is_valid_role(role_name):
            raise ValueError(f"无效的角色: {role_name}")
        
        self.roles.add(role_name)
        self._update_timestamp()
    
    def remove_role(self, role_name: str) -> None:
        """移除角色"""
        if role_name in self.roles:
            self.roles.remove(role_name)
            self._update_timestamp()
    
    def has_role(self, role_name: str) -> bool:
        """检查是否有特定角色"""
        return role_name in self.roles
    
    def has_any_role(self, role_names: List[str]) -> bool:
        """检查是否有任意一个角色"""
        return bool(self.roles & set(role_names))
    
    def is_admin(self) -> bool:
        """是否为管理员"""
        admin_roles = {rt.value for rt in RoleType.get_admin_roles()}
        return bool(self.roles & admin_roles)
    
    def is_medical_staff(self) -> bool:
        """是否为医疗人员"""
        medical_roles = {rt.value for rt in RoleType.get_medical_roles()}
        return bool(self.roles & medical_roles)
    
    def can_login(self) -> bool:
        """是否可以登录"""
        return self.status.can_login()
    
    def can_access_system(self) -> bool:
        """是否可以访问系统"""
        return self.status.can_access_system()
    
    def get_primary_role(self) -> Optional[str]:
        """获取主要角色（按优先级返回）"""
        for role_type in self._ROLE_PRIORITY:
            if self.has_role(role_type.value):
                return role_type.value
        return None
    
    def get_email_value(self) -> str:
        """获取邮箱字符串值"""
        return self.email.value
    
    def get_password_hash(self) -> str:
        """获取密码哈希值"""
        return self.password.hashed_value
    
    def verify_password(self, plain_password: str) -> bool:
        """验证密码"""
        return self.password.verify(plain_password)
    
    def __str__(self) -> str:
        return (
            f"UserEntity(id={self.id}, username={self.username}, email={self.email.value}, "
            f"phone={self.phone}, avatar={self.avatar}, status={self.status.value}, "
            f"tenantId={self.tenantId}, roles={sorted(self.roles)}, createdAt={self.createdAt}, "
            f"updatedAt={self.updatedAt}, lastLoginAt={self.lastLoginAt})"
        )
    
    def __repr__(self) -> str:
        return str(self)
