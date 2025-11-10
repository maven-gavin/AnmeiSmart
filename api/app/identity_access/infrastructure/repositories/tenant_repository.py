"""
租户仓储实现

实现租户相关的数据访问操作。
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.identity_access.infrastructure.db.user import Tenant
from app.identity_access.interfaces.repository_interfaces import ITenantRepository
from app.identity_access.domain.entities.tenant import TenantEntity
from app.identity_access.domain.value_objects.tenant_status import TenantStatus
from app.identity_access.domain.value_objects.tenant_type import TenantType


class TenantRepository(ITenantRepository):
    """租户仓储实现"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_by_id(self, tenant_id: str) -> Optional[TenantEntity]:
        """根据ID获取租户"""
        db_tenant = self.db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not db_tenant:
            return None
        
        return self._to_entity(db_tenant)
    
    async def get_by_name(self, name: str) -> Optional[TenantEntity]:
        """根据名称获取租户"""
        db_tenant = self.db.query(Tenant).filter(Tenant.name == name).first()
        if not db_tenant:
            return None
        
        return self._to_entity(db_tenant)
    
    async def get_system_tenant(self) -> Optional[TenantEntity]:
        """获取系统租户"""
        db_tenant = self.db.query(Tenant).filter(Tenant.is_system == True).first()
        if not db_tenant:
            return None
        
        return self._to_entity(db_tenant)
    
    async def save(self, tenant: TenantEntity) -> TenantEntity:
        """保存租户"""
        db_tenant = self.db.query(Tenant).filter(Tenant.id == tenant.id).first()
        
        if db_tenant:
            # 更新现有租户
            self._update_db_model(db_tenant, tenant)
        else:
            # 创建新租户
            db_tenant = self._to_db_model(tenant)
            self.db.add(db_tenant)
        
        self.db.commit()
        self.db.refresh(db_tenant)
        
        return self._to_entity(db_tenant)
    
    async def delete(self, tenant_id: str) -> bool:
        """删除租户"""
        db_tenant = self.db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not db_tenant:
            return False
        
        self.db.delete(db_tenant)
        self.db.commit()
        return True
    
    async def list_by_status(self, status: TenantStatus) -> List[TenantEntity]:
        """根据状态获取租户列表"""
        db_tenants = self.db.query(Tenant).filter(Tenant.status == status.value).all()
        return [self._to_entity(tenant) for tenant in db_tenants]
    
    async def list_active(self) -> List[TenantEntity]:
        """获取活跃租户列表"""
        db_tenants = self.db.query(Tenant).filter(Tenant.is_active == True).all()
        return [self._to_entity(tenant) for tenant in db_tenants]
    
    def _to_entity(self, db_tenant: Tenant) -> TenantEntity:
        """将数据库模型转换为领域实体"""
        return TenantEntity(
            id=db_tenant.id,
            name=db_tenant.name,
            displayName=db_tenant.display_name,
            description=db_tenant.description,
            status=TenantStatus(db_tenant.status) if db_tenant.status else TenantStatus.ACTIVE,
            tenantType=TenantType(db_tenant.tenant_type) if db_tenant.tenant_type else TenantType.STANDARD,
            priority=db_tenant.priority,
            isSystem=db_tenant.is_system,
            isAdmin=db_tenant.is_admin,
            contactName=db_tenant.contact_name,
            contactEmail=db_tenant.contact_email,
            contactPhone=db_tenant.contact_phone,
            encryptedPubKey=db_tenant.encrypted_pub_key,
            createdAt=db_tenant.created_at,
            updatedAt=db_tenant.updated_at
        )
    
    def _to_db_model(self, tenant: TenantEntity) -> Tenant:
        """将领域实体转换为数据库模型"""
        return Tenant(
            id=tenant.id,
            name=tenant.name,
            display_name=tenant.displayName,
            description=tenant.description,
            status=tenant.status.value,
            tenant_type=tenant.tenantType.value,
            priority=tenant.priority,
            is_system=tenant.isSystem,
            is_admin=tenant.isAdmin,
            contact_name=tenant.contactName,
            contact_email=tenant.contactEmail,
            contact_phone=tenant.contactPhone,
            encrypted_pub_key=tenant.encryptedPubKey,
            created_at=tenant.createdAt,
            updated_at=tenant.updatedAt
        )
    
    def _update_db_model(self, db_tenant: Tenant, tenant: TenantEntity) -> None:
        """更新数据库模型"""
        db_tenant.name = tenant.name
        db_tenant.display_name = tenant.displayName
        db_tenant.description = tenant.description
        db_tenant.status = tenant.status.value
        db_tenant.tenant_type = tenant.tenantType.value
        db_tenant.priority = tenant.priority
        db_tenant.is_system = tenant.isSystem
        db_tenant.is_admin = tenant.isAdmin
        db_tenant.contact_name = tenant.contactName
        db_tenant.contact_email = tenant.contactEmail
        db_tenant.contact_phone = tenant.contactPhone
        db_tenant.encrypted_pub_key = tenant.encryptedPubKey
        db_tenant.updated_at = tenant.updatedAt
