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
class User:
    """用户聚合根"""
    
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
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_login_at: Optional[datetime] = None
    
    # 角色集合（支持数据库配置的角色）
    roles: Set[str] = field(default_factory=set)
    
    # 租户关联
    tenant_id: Optional[str] = None
    
    def __post_init__(self):
        """后初始化验证"""
        if not self.id or not self.id.strip():
            raise ValueError("用户ID不能为空")
        
        if not self.username or not self.username.strip():
            raise ValueError("用户名不能为空")
        
        # 确保有默认角色（如果没有指定角色）
        if not self.roles:
            self.roles = {RoleType.CUSTOMER.value}
    
    @classmethod
    def create(
        cls,
        username: str,
        email: str,
        password: str,
        phone: Optional[str] = None,
        avatar: Optional[str] = None,
        roles: Optional[List[str]] = None,
        tenant_id: Optional[str] = None
    ) -> "User":
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
        
        # 处理角色
        role_set = set()
        if roles:
            for role in roles:
                if role in [rt.value for rt in RoleType.get_all_roles()]:
                    role_set.add(role)
        
        # 确保有默认角色
        if not role_set:
            role_set.add(RoleType.CUSTOMER.value)
        
        return cls(
            id=str(uuid.uuid4()),
            username=username.strip(),
            email=email_obj,
            password=password_obj,
            phone=phone,
            avatar=avatar,
            roles=role_set,
            tenant_id=tenant_id
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
        
        self.updated_at = datetime.utcnow()
    
    def change_password(self, old_password: str, new_password: str) -> None:
        """修改密码"""
        if not self.password.verify(old_password):
            raise ValueError("原密码不正确")
        
        self.password = Password.create(new_password)
        self.updated_at = datetime.utcnow()
    
    def activate(self) -> None:
        """激活用户"""
        self.status = UserStatus.ACTIVE
        self.updated_at = datetime.utcnow()
    
    def deactivate(self) -> None:
        """停用用户"""
        self.status = UserStatus.INACTIVE
        self.updated_at = datetime.utcnow()
    
    def suspend(self) -> None:
        """暂停用户"""
        self.status = UserStatus.SUSPENDED
        self.updated_at = datetime.utcnow()
    
    def record_login(self) -> None:
        """记录登录时间"""
        self.last_login_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def add_role(self, role_name: str) -> None:
        """添加角色"""
        if role_name not in [rt.value for rt in RoleType.get_all_roles()]:
            raise ValueError(f"无效的角色: {role_name}")
        
        self.roles.add(role_name)
        self.updated_at = datetime.utcnow()
    
    def remove_role(self, role_name: str) -> None:
        """移除角色"""
        if role_name in self.roles:
            self.roles.remove(role_name)
            self.updated_at = datetime.utcnow()
    
    def has_role(self, role_name: str) -> bool:
        """检查是否有特定角色"""
        return role_name in self.roles
    
    def has_any_role(self, role_names: List[str]) -> bool:
        """检查是否有任意一个角色"""
        return any(role in self.roles for role in role_names)
    
    def is_admin(self) -> bool:
        """是否为管理员"""
        admin_roles = [rt.value for rt in RoleType.get_admin_roles()]
        return self.has_any_role(admin_roles)
    
    def is_medical_staff(self) -> bool:
        """是否为医疗人员"""
        medical_roles = [rt.value for rt in RoleType.get_medical_roles()]
        return self.has_any_role(medical_roles)
    
    def can_login(self) -> bool:
        """是否可以登录"""
        return self.status.can_login()
    
    def can_access_system(self) -> bool:
        """是否可以访问系统"""
        return self.status.can_access_system()
    
    def get_primary_role(self) -> Optional[str]:
        """获取主要角色（优先级：管理员 > 医疗人员 > 客户）"""
        if self.has_role(RoleType.ADMINISTRATOR.value):
            return RoleType.ADMINISTRATOR.value
        elif self.has_role(RoleType.OPERATOR.value):
            return RoleType.OPERATOR.value
        elif self.has_role(RoleType.DOCTOR.value):
            return RoleType.DOCTOR.value
        elif self.has_role(RoleType.CONSULTANT.value):
            return RoleType.CONSULTANT.value
        elif self.has_role(RoleType.CUSTOMER.value):
            return RoleType.CUSTOMER.value
        
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
        return f"User(id={self.id}, username={self.username}, email={self.email.value})"
