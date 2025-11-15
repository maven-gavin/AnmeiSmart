"""
租户聚合根

租户是身份与权限上下文的核心聚合根，负责管理多租户架构中的租户信息。
"""

import uuid
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field

from ..value_objects.tenant_status import TenantStatus
from ..value_objects.tenant_type import TenantType


@dataclass
class TenantEntity:
    """租户聚合根"""
    
    # 身份标识
    id: str
    
    # 基本信息
    name: str
    displayName: Optional[str] = None
    description: Optional[str] = None
    
    # 状态信息
    status: TenantStatus = TenantStatus.ACTIVE
    tenantType: TenantType = TenantType.STANDARD
    
    # 优先级和系统标识
    priority: int = 0
    isSystem: bool = False
    isAdmin: bool = False
    
    # 联系信息
    contactName: Optional[str] = None
    contactEmail: Optional[str] = None
    contactPhone: Optional[str] = None
    
    # 加密配置
    encryptedPubKey: Optional[str] = None
    
    # 时间戳
    createdAt: datetime = field(default_factory=datetime.utcnow)
    updatedAt: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """后初始化验证"""
        if not self.id or not self.id.strip():
            raise ValueError("租户ID不能为空")
        
        if not self.name or not self.name.strip():
            raise ValueError("租户名称不能为空")
        
        if len(self.name) > 50:
            raise ValueError("租户名称长度不能超过50个字符")
        
        if self.displayName is None:
            self.displayName = self.name
    
    @classmethod
    def create(
        cls,
        name: str,
        displayName: Optional[str] = None,
        description: Optional[str] = None,
        tenantType: TenantType = TenantType.STANDARD,
        status: TenantStatus = TenantStatus.ACTIVE,
        isSystem: bool = False,
        isAdmin: bool = False,
        priority: int = 0,
        encryptedPubKey: Optional[str] = None,
        contactName: Optional[str] = None,
        contactEmail: Optional[str] = None,
        contactPhone: Optional[str] = None
    ) -> "TenantEntity":
        """创建新租户"""
        tenant_id = str(uuid.uuid4())
        
        return cls(
            id=tenant_id,
            name=name,
            displayName=displayName or name,
            description=description,
            tenantType=tenantType,
            status=status,
            isSystem=isSystem,
            isAdmin=isAdmin,
            priority=priority,
            # 空字符串转换为 None，非空字符串保留并去除首尾空格
            encryptedPubKey=encryptedPubKey.strip() if encryptedPubKey and isinstance(encryptedPubKey, str) and encryptedPubKey.strip() else None,
            contactName=contactName,
            contactEmail=contactEmail,
            contactPhone=contactPhone
        )
    
    @classmethod
    def create_system_tenant(cls) -> "TenantEntity":
        """创建系统租户"""
        return cls(
            id="system-tenant",
            name="system",
            displayName="系统租户",
            description="系统默认租户",
            tenantType=TenantType.SYSTEM,
            isSystem=True,
            isAdmin=True,
            priority=1000
        )
    
    def activate(self) -> None:
        """激活租户"""
        if self.status == TenantStatus.ACTIVE:
            raise ValueError("租户已经是激活状态")
        
        self.status = TenantStatus.ACTIVE
        self.updatedAt = datetime.utcnow()
    
    def deactivate(self) -> None:
        """停用租户"""
        if self.status == TenantStatus.INACTIVE:
            raise ValueError("租户已经是停用状态")
        
        if self.isSystem:
            raise ValueError("系统租户不能被停用")
        
        self.status = TenantStatus.INACTIVE
        self.updatedAt = datetime.utcnow()
    
    def update_contact_info(
        self,
        contactName: Optional[str] = None,
        contactEmail: Optional[str] = None,
        contactPhone: Optional[str] = None
    ) -> None:
        """更新联系信息"""
        if contactName is not None:
            self.contactName = contactName
        if contactEmail is not None:
            self.contactEmail = contactEmail
        if contactPhone is not None:
            self.contactPhone = contactPhone
        
        self.updatedAt = datetime.utcnow()
    
    def update_name(self, name: str) -> None:
        """更新租户名称"""
        if not name or not name.strip():
            raise ValueError("租户名称不能为空")
        
        if len(name) > 50:
            raise ValueError("租户名称长度不能超过50个字符")
        
        self.name = name.strip()
        self.updatedAt = datetime.utcnow()
    
    def update_basic_info(
        self,
        displayName: Optional[str] = None,
        description: Optional[str] = None
    ) -> None:
        """更新基本信息"""
        if displayName is not None:
            self.displayName = displayName
        if description is not None:
            self.description = description
        
        self.updatedAt = datetime.utcnow()
    
    def update_attributes(
        self,
        tenantType: Optional[TenantType] = None,
        status: Optional[TenantStatus] = None,
        isSystem: Optional[bool] = None,
        isAdmin: Optional[bool] = None,
        priority: Optional[int] = None,
        encryptedPubKey: Optional[str] = None
    ) -> None:
        """更新租户属性"""
        if tenantType is not None:
            self.tenantType = tenantType
        if status is not None:
            self.status = status
        if isSystem is not None:
            self.isSystem = isSystem
        if isAdmin is not None:
            self.isAdmin = isAdmin
        if priority is not None:
            self.priority = priority
        # 允许设置为空字符串来清空加密公钥
        if encryptedPubKey is not None:
            self.encryptedPubKey = encryptedPubKey if encryptedPubKey else None
        
        self.updatedAt = datetime.utcnow()
    
    def set_encrypted_pub_key(self, encrypted_key: str) -> None:
        """设置加密公钥"""
        self.encryptedPubKey = encrypted_key
        self.updatedAt = datetime.utcnow()
    
    def can_be_deleted(self) -> bool:
        """检查租户是否可以被删除"""
        return not self.isSystem
    
    def is_active(self) -> bool:
        """检查租户是否激活"""
        return self.status == TenantStatus.ACTIVE
    
    def is_admin_tenant(self) -> bool:
        """检查是否为管理员租户"""
        return self.isAdmin
    
    def is_system_tenant(self) -> bool:
        """检查是否为系统租户"""
        return self.isSystem
    
    def get_effective_name(self) -> str:
        """获取有效显示名称"""
        return self.displayName or self.name
    
    def __str__(self) -> str:
        return (
            f"TenantEntity(id={self.id}, name={self.name}, displayName={self.displayName}, "
            f"description={self.description}, status={self.status.value}, tenantType={self.tenantType.value}, "
            f"priority={self.priority}, isSystem={self.isSystem}, isAdmin={self.isAdmin}, "
            f"contactName={self.contactName}, contactEmail={self.contactEmail}, contactPhone={self.contactPhone}, "
            f"encryptedPubKey={self.encryptedPubKey}, createdAt={self.createdAt}, updatedAt={self.updatedAt})"
        )
    
    def __repr__(self) -> str:
        return (
            f"TenantEntity(id={self.id}, name={self.name}, displayName={self.displayName}, "
            f"description={self.description}, status={self.status.value}, tenantType={self.tenantType.value}, "
            f"priority={self.priority}, isSystem={self.isSystem}, isAdmin={self.isAdmin}, "
            f"contactName={self.contactName}, contactEmail={self.contactEmail}, contactPhone={self.contactPhone}, "
            f"encryptedPubKey={self.encryptedPubKey}, createdAt={self.createdAt}, updatedAt={self.updatedAt})"
        )
