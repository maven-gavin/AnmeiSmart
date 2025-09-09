"""
租户领域服务

处理租户管理相关的业务逻辑。
"""

from typing import Optional, List
import logging

from .entities.tenant import Tenant
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
    ) -> Tenant:
        """创建新租户"""
        # 检查租户名称是否已存在
        existing_tenant = await self.tenant_repository.get_by_name(name)
        if existing_tenant:
            raise ValueError(f"租户名称 '{name}' 已存在")
        
        # 创建租户
        tenant = Tenant.create(
            name=name,
            display_name=display_name,
            description=description,
            tenant_type=tenant_type,
            contact_name=contact_name,
            contact_email=contact_email,
            contact_phone=contact_phone
        )
        
        # 保存租户
        await self.tenant_repository.save(tenant)
        logger.info(f"创建租户: {tenant.name} (ID: {tenant.id})")
        
        return tenant
    
    async def get_tenant_by_id(self, tenant_id: str) -> Optional[Tenant]:
        """根据ID获取租户"""
        return await self.tenant_repository.get_by_id(tenant_id)
    
    async def get_tenant_by_name(self, name: str) -> Optional[Tenant]:
        """根据名称获取租户"""
        return await self.tenant_repository.get_by_name(name)
    
    async def get_system_tenant(self) -> Optional[Tenant]:
        """获取系统租户"""
        return await self.tenant_repository.get_system_tenant()
    
    async def list_active_tenants(self) -> List[Tenant]:
        """获取所有激活的租户"""
        return await self.tenant_repository.list_by_status(TenantStatus.ACTIVE)
    
    async def activate_tenant(self, tenant_id: str) -> bool:
        """激活租户"""
        tenant = await self.tenant_repository.get_by_id(tenant_id)
        if not tenant:
            return False
        
        try:
            tenant.activate()
            await self.tenant_repository.save(tenant)
            logger.info(f"激活租户: {tenant.name}")
            return True
        except ValueError as e:
            logger.warning(f"激活租户失败: {e}")
            return False
    
    async def deactivate_tenant(self, tenant_id: str) -> bool:
        """停用租户"""
        tenant = await self.tenant_repository.get_by_id(tenant_id)
        if not tenant:
            return False
        
        try:
            tenant.deactivate()
            await self.tenant_repository.save(tenant)
            logger.info(f"停用租户: {tenant.name}")
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
        tenant = await self.tenant_repository.get_by_id(tenant_id)
        if not tenant:
            return False
        
        tenant.update_contact_info(contact_name, contact_email, contact_phone)
        await self.tenant_repository.save(tenant)
        logger.info(f"更新租户联系信息: {tenant.name}")
        
        return True
    
    async def delete_tenant(self, tenant_id: str) -> bool:
        """删除租户"""
        tenant = await self.tenant_repository.get_by_id(tenant_id)
        if not tenant:
            return False
        
        if not tenant.can_be_deleted():
            raise ValueError("系统租户不能被删除")
        
        # 检查是否有用户关联
        user_count = await self.user_repository.count_by_tenant_id(tenant_id)
        if user_count > 0:
            raise ValueError(f"租户 '{tenant.name}' 下还有 {user_count} 个用户，无法删除")
        
        await self.tenant_repository.delete(tenant_id)
        logger.info(f"删除租户: {tenant.name}")
        
        return True
    
    async def get_tenant_statistics(self, tenant_id: str) -> dict:
        """获取租户统计信息"""
        tenant = await self.tenant_repository.get_by_id(tenant_id)
        if not tenant:
            return {}
        
        user_count = await self.user_repository.count_by_tenant_id(tenant_id)
        
        return {
            "tenant_id": tenant_id,
            "tenant_name": tenant.name,
            "user_count": user_count,
            "status": tenant.status.value,
            "created_at": tenant.created_at.isoformat()
        }
