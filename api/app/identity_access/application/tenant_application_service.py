"""
租户应用服务

处理租户管理相关的应用用例。
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..domain.tenant_domain_service import TenantDomainService
from ..domain.entities.tenant import TenantEntity
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
        status: str = "active",
        is_system: bool = False,
        is_admin: bool = False,
        priority: int = 0,
        encrypted_pub_key: Optional[str] = None,
        contact_name: Optional[str] = None,
        contact_email: Optional[str] = None,
        contact_phone: Optional[str] = None
    ) -> Dict[str, Any]:
        """创建租户用例"""
        try:
            # 转换租户类型和状态
            tenant_type_enum = TenantType(tenant_type)
            from ..domain.value_objects.tenant_status import TenantStatus
            status_enum = TenantStatus(status)
            
            # 创建租户
            tenantEntity = await self.tenant_domain_service.create_tenant(
                name=name,
                display_name=display_name,
                description=description,
                tenant_type=tenant_type_enum,
                status=status_enum,
                is_system=is_system,
                is_admin=is_admin,
                priority=priority,
                encrypted_pub_key=encrypted_pub_key if encrypted_pub_key is not None else None,
                contact_name=contact_name,
                contact_email=contact_email,
                contact_phone=contact_phone
            )
            
            return {
                "id": tenantEntity.id,
                "name": tenantEntity.name,
                "display_name": tenantEntity.displayName,
                "description": tenantEntity.description,
                "tenant_type": tenantEntity.tenantType.value,
                "status": tenantEntity.status.value,
                "is_active": tenantEntity.is_active(),  # 使用 is_active() 方法
                "is_system": tenantEntity.isSystem,
                "is_admin": tenantEntity.isAdmin,
                "priority": tenantEntity.priority,
                "encrypted_pub_key": tenantEntity.encryptedPubKey,
                "contact_name": tenantEntity.contactName,
                "contact_email": tenantEntity.contactEmail,
                "contact_phone": tenantEntity.contactPhone,
                "created_at": tenantEntity.createdAt.isoformat(),
                "updated_at": tenantEntity.updatedAt.isoformat()
            }
            
        except Exception as e:
            logger.error(f"创建租户失败: {str(e)}", exc_info=True)
            raise
    
    async def get_tenant(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """获取租户用例"""
        try:
            tenantEntity = await self.tenant_domain_service.get_tenant_by_id(tenant_id)
            if not tenantEntity:
                return None
            
            return {
                "id": tenantEntity.id,
                "name": tenantEntity.name,
                "display_name": tenantEntity.displayName,
                "description": tenantEntity.description,
                "tenant_type": tenantEntity.tenantType.value,
                "status": tenantEntity.status.value,
                "is_active": tenantEntity.is_active(),  # 使用 is_active() 方法
                "is_system": tenantEntity.isSystem,
                "is_admin": tenantEntity.isAdmin,
                "priority": tenantEntity.priority,
                "encrypted_pub_key": tenantEntity.encryptedPubKey,
                "contact_name": tenantEntity.contactName,
                "contact_email": tenantEntity.contactEmail,
                "contact_phone": tenantEntity.contactPhone,
                "created_at": tenantEntity.createdAt.isoformat(),
                "updated_at": tenantEntity.updatedAt.isoformat()
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
                # 如果没有指定状态，返回所有租户
                tenants = await self.tenant_domain_service.list_all_tenants()
            
            return [
                {
                    "id": tenantEntity.id,
                    "name": tenantEntity.name,
                    "display_name": tenantEntity.displayName,
                    "description": tenantEntity.description,
                    "tenant_type": tenantEntity.tenantType.value,
                    "status": tenantEntity.status.value,
                    "is_active": tenantEntity.is_active(),  # 使用 is_active() 方法
                    "is_system": tenantEntity.isSystem,
                    "is_admin": tenantEntity.isAdmin,
                    "priority": tenantEntity.priority,
                    "encrypted_pub_key": tenantEntity.encryptedPubKey,
                    "contact_name": tenantEntity.contactName,
                    "contact_email": tenantEntity.contactEmail,
                    "contact_phone": tenantEntity.contactPhone,
                    "created_at": tenantEntity.createdAt.isoformat(),
                    "updated_at": tenantEntity.updatedAt.isoformat()
                }
                for tenantEntity in tenants
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
    
    async def update_tenant(
        self,
        tenant_id: str,
        name: Optional[str] = None,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        tenant_type: Optional[str] = None,
        status: Optional[str] = None,
        is_system: Optional[bool] = None,
        is_admin: Optional[bool] = None,
        priority: Optional[int] = None,
        encrypted_pub_key: Optional[str] = None,
        contact_name: Optional[str] = None,
        contact_email: Optional[str] = None,
        contact_phone: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """更新租户信息用例（包含基本信息和联系信息）"""
        try:
            # 更新名称（如果提供）
            if name is not None:
                success = await self.tenant_domain_service.update_tenant_name(
                    tenant_id=tenant_id,
                    name=name
                )
                if not success:
                    return None
            
            # 更新基本信息
            if display_name is not None or description is not None:
                success = await self.tenant_domain_service.update_tenant_basic_info(
                    tenant_id=tenant_id,
                    display_name=display_name,
                    description=description
                )
                if not success:
                    return None
            
            # 更新租户类型、状态、系统标志、管理员标志、优先级、加密公钥
            # 注意：encrypted_pub_key 可能是空字符串（用于清空），需要特殊处理
            should_update_attributes = (
                tenant_type is not None or 
                status is not None or 
                is_system is not None or 
                is_admin is not None or 
                priority is not None or 
                encrypted_pub_key is not None  # 包括空字符串的情况
            )
            if should_update_attributes:
                from ..domain.value_objects.tenant_type import TenantType
                from ..domain.value_objects.tenant_status import TenantStatus
                
                tenant_type_enum = None
                if tenant_type:
                    tenant_type_enum = TenantType(tenant_type) if isinstance(tenant_type, str) else tenant_type
                
                status_enum = None
                if status:
                    status_enum = TenantStatus(status) if isinstance(status, str) else status
                
                success = await self.tenant_domain_service.update_tenant_attributes(
                    tenant_id=tenant_id,
                    tenant_type=tenant_type_enum,
                    status=status_enum,
                    is_system=is_system,
                    is_admin=is_admin,
                    priority=priority,
                    encrypted_pub_key=encrypted_pub_key
                )
                if not success:
                    return None
            
            # 更新联系信息
            if contact_name is not None or contact_email is not None or contact_phone is not None:
                success = await self.tenant_domain_service.update_tenant_contact_info(
                    tenant_id=tenant_id,
                    contact_name=contact_name,
                    contact_email=contact_email,
                    contact_phone=contact_phone
                )
                if not success:
                    return None
            
            # 重新获取更新后的租户信息
            tenantEntity = await self.tenant_domain_service.get_tenant_by_id(tenant_id)
            if not tenantEntity:
                return None
            
            return {
                "id": tenantEntity.id,
                "name": tenantEntity.name,
                "display_name": tenantEntity.displayName,
                "description": tenantEntity.description,
                "tenant_type": tenantEntity.tenantType.value,
                "status": tenantEntity.status.value,
                "is_active": tenantEntity.is_active(),
                "is_system": tenantEntity.isSystem,
                "is_admin": tenantEntity.isAdmin,
                "priority": tenantEntity.priority,
                "encrypted_pub_key": tenantEntity.encryptedPubKey,
                "contact_name": tenantEntity.contactName,
                "contact_email": tenantEntity.contactEmail,
                "contact_phone": tenantEntity.contactPhone,
                "created_at": tenantEntity.createdAt.isoformat(),
                "updated_at": tenantEntity.updatedAt.isoformat()
            }
        except Exception as e:
            logger.error(f"更新租户信息失败: {str(e)}", exc_info=True)
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
