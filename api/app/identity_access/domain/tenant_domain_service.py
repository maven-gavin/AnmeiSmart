"""
租户领域服务

处理租户管理相关的业务逻辑。
"""

from typing import Optional, List
import logging

from .entities.tenant import TenantEntity
from .value_objects.tenant_status import TenantStatus
from .value_objects.tenant_type import TenantType

logger = logging.getLogger(__name__)


class TenantDomainService:
    """租户领域服务"""
    
    def __init__(self, tenant_repository, user_repository):
        self.tenant_repository = tenant_repository
        self.user_repository = user_repository
    
    async def create_tenant(
        self,
        name: str,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        tenant_type: TenantType = TenantType.STANDARD,
        contact_name: Optional[str] = None,
        contact_email: Optional[str] = None,
        contact_phone: Optional[str] = None
    ) -> TenantEntity:
        """创建新租户"""
        # 检查租户名称是否已存在
        existing_tenant = await self.tenant_repository.get_by_name(name)
        if existing_tenant:
            raise ValueError(f"租户名称 '{name}' 已存在")
        
        # 创建租户
        tenantEntity = TenantEntity.create(
            name=name,
            displayName=display_name,
            description=description,
            tenantType=tenant_type,
            contactName=contact_name,
            contactEmail=contact_email,
            contactPhone=contact_phone
        )
        
        # 保存租户
        await self.tenant_repository.save(tenantEntity)
        logger.info(f"创建租户: {tenantEntity.name} (ID: {tenantEntity.id})")
        
        return tenantEntity
    
    async def get_tenant_by_id(self, tenant_id: str) -> Optional[TenantEntity]:
        """根据ID获取租户"""
        return await self.tenant_repository.get_by_id(tenant_id)
    
    async def get_tenant_by_name(self, name: str) -> Optional[TenantEntity]:
        """根据名称获取租户"""
        return await self.tenant_repository.get_by_name(name)
    
    async def get_system_tenant(self) -> Optional[TenantEntity]:
        """获取系统租户"""
        return await self.tenant_repository.get_system_tenant()
    
    async def list_active_tenants(self) -> List[TenantEntity]:
        """获取所有激活的租户"""
        return await self.tenant_repository.list_by_status(TenantStatus.ACTIVE)
    
    async def list_by_status(self, status: TenantStatus) -> List[TenantEntity]:
        """根据状态获取租户列表"""
        return await self.tenant_repository.list_by_status(status)
    
    async def activate_tenant(self, tenant_id: str) -> bool:
        """激活租户"""
        tenantEntity = await self.tenant_repository.get_by_id(tenant_id)
        if not tenantEntity:
            return False
        
        try:
            tenantEntity.activate()
            await self.tenant_repository.save(tenantEntity)
            logger.info(f"激活租户: {tenantEntity.name}")
            return True
        except ValueError as e:
            logger.warning(f"激活租户失败: {e}")
            return False
    
    async def deactivate_tenant(self, tenant_id: str) -> bool:
        """停用租户"""
        tenantEntity = await self.tenant_repository.get_by_id(tenant_id)
        if not tenantEntity:
            return False
        
        try:
            tenantEntity.deactivate()
            await self.tenant_repository.save(tenantEntity)
            logger.info(f"停用租户: {tenantEntity.name}")
            return True
        except ValueError as e:
            logger.warning(f"停用租户失败: {e}")
            return False
    
    async def update_tenant_contact_info(
        self,
        tenant_id: str,
        contact_name: Optional[str] = None,
        contact_email: Optional[str] = None,
        contact_phone: Optional[str] = None
    ) -> bool:
        """更新租户联系信息"""
        tenantEntity = await self.tenant_repository.get_by_id(tenant_id)
        if not tenantEntity:
            return False
        
        tenantEntity.update_contact_info(contact_name, contact_email, contact_phone)
        await self.tenant_repository.save(tenantEntity)
        logger.info(f"更新租户联系信息: {tenantEntity.name}")
        
        return True
    
    async def delete_tenant(self, tenant_id: str) -> bool:
        """删除租户"""
        tenantEntity = await self.tenant_repository.get_by_id(tenant_id)
        if not tenantEntity:
            return False
        
        if not tenantEntity.can_be_deleted():
            raise ValueError("系统租户不能被删除")
        
        # 检查是否有用户关联
        user_count = await self.user_repository.count_by_tenant_id(tenant_id)
        if user_count > 0:
            raise ValueError(f"租户 '{tenantEntity.name}' 下还有 {user_count} 个用户，无法删除")
        
        await self.tenant_repository.delete(tenant_id)
        logger.info(f"删除租户: {tenantEntity.name}")
        
        return True
    
    async def get_tenant_statistics(self, tenant_id: str) -> dict:
        """获取租户统计信息"""
        tenantEntity = await self.tenant_repository.get_by_id(tenant_id)
        if not tenantEntity:
            return {}
        
        user_count = await self.user_repository.count_by_tenant_id(tenant_id)
        
        return {
            "tenant_id": tenant_id,
            "tenant_name": tenantEntity.name,
            "user_count": user_count,
            "status": tenantEntity.status.value,
            "created_at": tenantEntity.createdAt.isoformat()
        }
