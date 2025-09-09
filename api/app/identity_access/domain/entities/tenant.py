"""
租户聚合根

租户是身份与权限上下文的核心聚合根，负责管理多租户架构中的租户信息。
"""

import uuid
from datetime import datetime
from typing import Optional, List, Set
from dataclasses import dataclass, field

from ..value_objects.tenant_status import TenantStatus
from ..value_objects.tenant_type import TenantType


@dataclass
class Tenant:
    """租户聚合根"""
    
    # 身份标识
    id: str
    
    # 基本信息
    name: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    
    # 状态信息
    status: TenantStatus = TenantStatus.ACTIVE
    tenant_type: TenantType = TenantType.STANDARD
    
    # 优先级和系统标识
    priority: int = 0
    is_system: bool = False
    is_admin: bool = False
    
    # 联系信息
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    
    # 加密配置
    encrypted_pub_key: Optional[str] = None
    
    # 时间戳
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """后初始化验证"""
        if not self.id or not self.id.strip():
            raise ValueError("租户ID不能为空")
        
        if not self.name or not self.name.strip():
            raise ValueError("租户名称不能为空")
        
        if len(self.name) > 50:
            raise ValueError("租户名称长度不能超过50个字符")
    
    @classmethod
    def create(
        cls,
        name: str,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        tenant_type: TenantType = TenantType.STANDARD,
        contact_name: Optional[str] = None,
        contact_email: Optional[str] = None,
        contact_phone: Optional[str] = None
    ) -> "Tenant":
        """创建新租户"""
        tenant_id = str(uuid.uuid4())
        
        return cls(
            id=tenant_id,
            name=name,
            display_name=display_name or name,
            description=description,
            tenant_type=tenant_type,
            contact_name=contact_name,
            contact_email=contact_email,
            contact_phone=contact_phone
        )
    
    @classmethod
    def create_system_tenant(cls) -> "Tenant":
        """创建系统租户"""
        return cls(
            id="system-tenant",
            name="system",
            display_name="系统租户",
            description="系统默认租户",
            tenant_type=TenantType.SYSTEM,
            is_system=True,
            is_admin=True,
            priority=1000
        )
    
    def activate(self) -> None:
        """激活租户"""
        if self.status == TenantStatus.ACTIVE:
            raise ValueError("租户已经是激活状态")
        
        self.status = TenantStatus.ACTIVE
        self.updated_at = datetime.utcnow()
    
    def deactivate(self) -> None:
        """停用租户"""
        if self.status == TenantStatus.INACTIVE:
            raise ValueError("租户已经是停用状态")
        
        if self.is_system:
            raise ValueError("系统租户不能被停用")
        
        self.status = TenantStatus.INACTIVE
        self.updated_at = datetime.utcnow()
    
    def update_contact_info(
        self,
        contact_name: Optional[str] = None,
        contact_email: Optional[str] = None,
        contact_phone: Optional[str] = None
    ) -> None:
        """更新联系信息"""
        if contact_name is not None:
            self.contact_name = contact_name
        if contact_email is not None:
            self.contact_email = contact_email
        if contact_phone is not None:
            self.contact_phone = contact_phone
        
        self.updated_at = datetime.utcnow()
    
    def set_encrypted_pub_key(self, encrypted_key: str) -> None:
        """设置加密公钥"""
        self.encrypted_pub_key = encrypted_key
        self.updated_at = datetime.utcnow()
    
    def can_be_deleted(self) -> bool:
        """检查租户是否可以被删除"""
        return not self.is_system
    
    def is_active(self) -> bool:
        """检查租户是否激活"""
        return self.status == TenantStatus.ACTIVE
    
    def is_admin_tenant(self) -> bool:
        """检查是否为管理员租户"""
        return self.is_admin
    
    def is_system_tenant(self) -> bool:
        """检查是否为系统租户"""
        return self.is_system
    
    def get_effective_name(self) -> str:
        """获取有效显示名称"""
        return self.display_name or self.name
    
    def __str__(self) -> str:
        return f"Tenant(id={self.id}, name={self.name}, status={self.status.value})"
    
    def __repr__(self) -> str:
        return f"Tenant(id={self.id}, name={self.name}, type={self.tenant_type.value}, status={self.status.value})"
