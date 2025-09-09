"""
租户应用服务

处理租户管理相关的应用用例。
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..domain.tenant_domain_service import TenantDomainService
from ..domain.entities.tenant import Tenant
from ..domain.value_objects.tenant_status import TenantStatus
from ..domain.value_objects.tenant_type import TenantType

logger = logging.getLogger(__name__)


class TenantApplicationService:
    """租户应用服务"""
    
    def __init__(self, tenant_domain_service: TenantDomainService):
        self.tenant_domain_service = tenant_domain_service
    
    async def create_tenant(
        self,
        name: str,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        tenant_type: str = "standard",
        contact_name: Optional[str] = None,
        contact_email: Optional[str] = None,
        contact_phone: Optional[str] = None
    ) -> Dict[str, Any]:
        """创建租户用例"""
        try:
            # 转换租户类型
            tenant_type_enum = TenantType(tenant_type)
            
            # 创建租户
            tenant = await self.tenant_domain_service.create_tenant(
                name=name,
                display_name=display_name,
                description=description,
                tenant_type=tenant_type_enum,
                contact_name=contact_name,
                contact_email=contact_email,
                contact_phone=contact_phone
            )
            
            return {
                "id": tenant.id,
                "name": tenant.name,
                "display_name": tenant.display_name,
                "description": tenant.description,
                "tenant_type": tenant.tenant_type.value,
                "status": tenant.status.value,
                "is_system": tenant.is_system,
                "is_admin": tenant.is_admin,
                "priority": tenant.priority,
                "contact_name": tenant.contact_name,
                "contact_email": tenant.contact_email,
                "contact_phone": tenant.contact_phone,
                "created_at": tenant.created_at.isoformat(),
                "updated_at": tenant.updated_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"创建租户失败: {str(e)}", exc_info=True)
            raise
    
    async def get_tenant(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """获取租户用例"""
        try:
            tenant = await self.tenant_domain_service.get_tenant_by_id(tenant_id)
            if not tenant:
                return None
            
            return {
                "id": tenant.id,
                "name": tenant.name,
                "display_name": tenant.display_name,
                "description": tenant.description,
                "tenant_type": tenant.tenant_type.value,
                "status": tenant.status.value,
                "is_system": tenant.is_system,
                "is_admin": tenant.is_admin,
                "priority": tenant.priority,
                "contact_name": tenant.contact_name,
                "contact_email": tenant.contact_email,
                "contact_phone": tenant.contact_phone,
                "created_at": tenant.created_at.isoformat(),
                "updated_at": tenant.updated_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取租户失败: {str(e)}", exc_info=True)
            raise
    
    async def list_tenants(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取租户列表用例"""
        try:
            if status:
                status_enum = TenantStatus(status)
                tenants = await self.tenant_domain_service.list_by_status(status_enum)
            else:
                tenants = await self.tenant_domain_service.list_active_tenants()
            
            return [
                {
                    "id": tenant.id,
                    "name": tenant.name,
                    "display_name": tenant.display_name,
                    "description": tenant.description,
                    "tenant_type": tenant.tenant_type.value,
                    "status": tenant.status.value,
                    "is_system": tenant.is_system,
                    "is_admin": tenant.is_admin,
                    "priority": tenant.priority,
                    "contact_name": tenant.contact_name,
                    "contact_email": tenant.contact_email,
                    "contact_phone": tenant.contact_phone,
                    "created_at": tenant.created_at.isoformat(),
                    "updated_at": tenant.updated_at.isoformat()
                }
                for tenant in tenants
            ]
            
        except Exception as e:
            logger.error(f"获取租户列表失败: {str(e)}", exc_info=True)
            raise
    
    async def activate_tenant(self, tenant_id: str) -> bool:
        """激活租户用例"""
        try:
            return await self.tenant_domain_service.activate_tenant(tenant_id)
        except Exception as e:
            logger.error(f"激活租户失败: {str(e)}", exc_info=True)
            raise
    
    async def deactivate_tenant(self, tenant_id: str) -> bool:
        """停用租户用例"""
        try:
            return await self.tenant_domain_service.deactivate_tenant(tenant_id)
        except Exception as e:
            logger.error(f"停用租户失败: {str(e)}", exc_info=True)
            raise
    
    async def update_tenant_contact(
        self,
        tenant_id: str,
        contact_name: Optional[str] = None,
        contact_email: Optional[str] = None,
        contact_phone: Optional[str] = None
    ) -> bool:
        """更新租户联系信息用例"""
        try:
            return await self.tenant_domain_service.update_tenant_contact_info(
                tenant_id=tenant_id,
                contact_name=contact_name,
                contact_email=contact_email,
                contact_phone=contact_phone
            )
        except Exception as e:
            logger.error(f"更新租户联系信息失败: {str(e)}", exc_info=True)
            raise
    
    async def delete_tenant(self, tenant_id: str) -> bool:
        """删除租户用例"""
        try:
            return await self.tenant_domain_service.delete_tenant(tenant_id)
        except Exception as e:
            logger.error(f"删除租户失败: {str(e)}", exc_info=True)
            raise
    
    async def get_tenant_statistics(self, tenant_id: str) -> Dict[str, Any]:
        """获取租户统计信息用例"""
        try:
            return await self.tenant_domain_service.get_tenant_statistics(tenant_id)
        except Exception as e:
            logger.error(f"获取租户统计信息失败: {str(e)}", exc_info=True)
            raise
