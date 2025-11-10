"""
角色权限应用服务

处理角色和权限管理相关的应用用例。
"""

import logging
from typing import List, Optional, Dict, Any, Set
from datetime import datetime

from ..domain.role_permission_domain_service import RolePermissionDomainService
from ..domain.entities.permission import PermissionEntity
from ..domain.value_objects.permission_type import PermissionType
from ..domain.value_objects.permission_scope import PermissionScope

logger = logging.getLogger(__name__)


class RolePermissionApplicationService:
    """角色权限应用服务"""
    
    def __init__(self, role_permission_domain_service: RolePermissionDomainService):
        self.role_permission_domain_service = role_permission_domain_service
    
    # ==================== 角色管理用例 ====================
    
    async def create_role(
        self,
        name: str,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        tenant_id: Optional[str] = None,
        is_system: bool = False,
        is_admin: bool = False
    ) -> Dict[str, Any]:
        """创建角色用例"""
        try:
            role = await self.role_permission_domain_service.create_role(
                name=name,
                display_name=display_name,
                description=description,
                tenant_id=tenant_id,
                is_system=is_system,
                is_admin=is_admin
            )
            
            return {
                "id": role.id,
                "name": role.name,
                "display_name": role.displayName,
                "description": role.description,
                "is_active": role.isActive,
                "is_system": role.isSystem,
                "is_admin": role.isAdmin,
                "priority": role.priority,
                "tenant_id": role.tenantId,
                "created_at": role.createdAt.isoformat(),
                "updated_at": role.updatedAt.isoformat()
            }
            
        except Exception as e:
            logger.error(f"创建角色失败: {str(e)}", exc_info=True)
            raise
    
    async def get_role(self, role_id: str) -> Optional[Dict[str, Any]]:
        """获取角色用例"""
        try:
            role = await self.role_permission_domain_service.get_role_by_id(role_id)
            if not role:
                return None
            
            return {
                "id": role.id,
                "name": role.name,
                "display_name": role.displayName,
                "description": role.description,
                "is_active": role.isActive,
                "is_system": role.isSystem,
                "is_admin": role.isAdmin,
                "priority": role.priority,
                "tenant_id": role.tenantId,
                "created_at": role.createdAt.isoformat(),
                "updated_at": role.updatedAt.isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取角色失败: {str(e)}", exc_info=True)
            raise
    
    async def list_roles(self, tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取角色列表用例"""
        try:
            roles = await self.role_permission_domain_service.list_active_roles(tenant_id)
            
            return [
                {
                    "id": role.id,
                    "name": role.name,
                    "display_name": role.displayName,
                    "description": role.description,
                    "is_active": role.isActive,
                    "is_system": role.isSystem,
                    "is_admin": role.isAdmin,
                    "priority": role.priority,
                    "tenant_id": role.tenantId,
                    "created_at": role.createdAt.isoformat(),
                    "updated_at": role.updatedAt.isoformat()
                }
                for role in roles
            ]
            
        except Exception as e:
            logger.error(f"获取角色列表失败: {str(e)}", exc_info=True)
            raise
    
    # ==================== 权限管理用例 ====================
    
    async def create_permission(
        self,
        name: str,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        permission_type: str = "action",
        scope: str = "tenant",
        resource: Optional[str] = None,
        action: Optional[str] = None,
        tenant_id: Optional[str] = None,
        is_system: bool = False,
        is_admin: bool = False
    ) -> Dict[str, Any]:
        """创建权限用例"""
        try:
            # 转换枚举类型
            permission_type_enum = PermissionType(permission_type)
            scope_enum = PermissionScope(scope)
            
            permissionEntity = await self.role_permission_domain_service.create_permission(
                name=name,
                display_name=display_name,
                description=description,
                permission_type=permission_type_enum,
                scope=scope_enum,
                resource=resource,
                action=action,
                tenant_id=tenant_id,
                is_system=is_system,
                is_admin=is_admin
            )
            
            return {
                "id": permissionEntity.id,
                "name": permissionEntity.name,
                "display_name": permissionEntity.displayName,
                "description": permissionEntity.description,
                "permission_type": permissionEntity.permissionType.value,
                "scope": permissionEntity.scope.value,
                "resource": permissionEntity.resource,
                "action": permissionEntity.action,
                "is_active": permissionEntity.isActive,
                "is_system": permissionEntity.isSystem,
                "is_admin": permissionEntity.isAdmin,
                "priority": permissionEntity.priority,
                "tenant_id": permissionEntity.tenantId,
                "created_at": permissionEntity.createdAt.isoformat(),
                "updated_at": permissionEntity.updatedAt.isoformat()
            }
            
        except Exception as e:
            logger.error(f"创建权限失败: {str(e)}", exc_info=True)
            raise
    
    async def get_permission(self, permission_id: str) -> Optional[Dict[str, Any]]:
        """获取权限用例"""
        try:
            permissionEntity = await self.role_permission_domain_service.get_permission_by_id(permission_id)
            if not permissionEntity:
                return None
            
            return {
                "id": permissionEntity.id,
                "name": permissionEntity.name,
                "display_name": permissionEntity.displayName,
                "description": permissionEntity.description,
                "permission_type": permissionEntity.permissionType.value,
                "scope": permissionEntity.scope.value,
                "resource": permissionEntity.resource,
                "action": permissionEntity.action,
                "is_active": permissionEntity.isActive,
                "is_system": permissionEntity.isSystem,
                "is_admin": permissionEntity.isAdmin,
                "priority": permissionEntity.priority,
                "tenant_id": permissionEntity.tenantId,
                "created_at": permissionEntity.createdAt.isoformat(),
                "updated_at": permissionEntity.updatedAt.isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取权限失败: {str(e)}", exc_info=True)
            raise
    
    async def list_permissions(self, tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取权限列表用例"""
        try:
            permissionEntities = await self.role_permission_domain_service.list_active_permissions(tenant_id)
            
            return [
                {
                    "id": permissionEntity.id,
                    "name": permissionEntity.name,
                    "display_name": permissionEntity.displayName,
                    "description": permissionEntity.description,
                    "permission_type": permissionEntity.permissionType.value,
                    "scope": permissionEntity.scope.value,
                    "resource": permissionEntity.resource,
                    "action": permissionEntity.action,
                    "is_active": permissionEntity.isActive,
                    "is_system": permissionEntity.isSystem,
                    "is_admin": permissionEntity.isAdmin,
                    "priority": permissionEntity.priority,
                    "tenant_id": permissionEntity.tenantId,
                    "created_at": permissionEntity.createdAt.isoformat(),
                    "updated_at": permissionEntity.updatedAt.isoformat()
                }
                for permissionEntity in permissionEntities
            ]
            
        except Exception as e:
            logger.error(f"获取权限列表失败: {str(e)}", exc_info=True)
            raise
    
    # ==================== 角色权限关联用例 ====================
    
    async def assign_permission_to_role(self, role_id: str, permission_id: str) -> bool:
        """为角色分配权限用例"""
        try:
            return await self.role_permission_domain_service.assign_permission_to_role(role_id, permission_id)
        except Exception as e:
            logger.error(f"为角色分配权限失败: {str(e)}", exc_info=True)
            raise
    
    async def remove_permission_from_role(self, role_id: str, permission_id: str) -> bool:
        """从角色移除权限用例"""
        try:
            return await self.role_permission_domain_service.remove_permission_from_role(role_id, permission_id)
        except Exception as e:
            logger.error(f"从角色移除权限失败: {str(e)}", exc_info=True)
            raise
    
    async def get_role_permissions(self, role_id: str) -> List[Dict[str, Any]]:
        """获取角色权限用例"""
        try:
            permissionEntities = await self.role_permission_domain_service.get_role_permissions(role_id)
            
            return [
                {
                    "id": permissionEntity.id,
                    "name": permissionEntity.name,
                    "display_name": permissionEntity.displayName,
                    "description": permissionEntity.description,
                    "permission_type": permissionEntity.permissionType.value,
                    "scope": permissionEntity.scope.value,
                    "resource": permissionEntity.resource,
                    "action": permissionEntity.action,
                    "is_active": permissionEntity.isActive,
                    "is_system": permissionEntity.isSystem,
                    "is_admin": permissionEntity.isAdmin,
                    "priority": permissionEntity.priority,
                    "tenant_id": permissionEntity.tenantId,
                    "created_at": permissionEntity.createdAt.isoformat(),
                    "updated_at": permissionEntity.updatedAt.isoformat()
                }
                for permissionEntity in permissionEntities
            ]
            
        except Exception as e:
            logger.error(f"获取角色权限失败: {str(e)}", exc_info=True)
            raise
    
    async def get_permission_roles(self, permission_id: str) -> List[Dict[str, Any]]:
        """获取权限角色用例"""
        try:
            roles = await self.role_permission_domain_service.get_permission_roles(permission_id)
            
            return [
                {
                    "id": role.id,
                    "name": role.name,
                    "display_name": role.displayName,
                    "description": role.description,
                    "is_active": role.isActive,
                    "is_system": role.isSystem,
                    "is_admin": role.isAdmin,
                    "priority": role.priority,
                    "tenant_id": role.tenantId,
                    "created_at": role.createdAt.isoformat(),
                    "updated_at": role.updatedAt.isoformat()
                }
                for role in roles
            ]
            
        except Exception as e:
            logger.error(f"获取权限角色失败: {str(e)}", exc_info=True)
            raise
    
    # ==================== 用户权限检查用例 ====================
    
    async def check_user_permission(self, user_id: str, permission_name: str) -> bool:
        """检查用户权限用例"""
        try:
            return await self.role_permission_domain_service.check_user_permission(user_id, permission_name)
        except Exception as e:
            logger.error(f"检查用户权限失败: {str(e)}", exc_info=True)
            return False
    
    async def check_user_role(self, user_id: str, role_name: str) -> bool:
        """检查用户角色用例"""
        try:
            return await self.role_permission_domain_service.check_user_role(user_id, role_name)
        except Exception as e:
            logger.error(f"检查用户角色失败: {str(e)}", exc_info=True)
            return False
    
    async def get_user_permissions(self, user_id: str) -> List[str]:
        """获取用户权限用例"""
        try:
            permissions = await self.role_permission_domain_service.get_user_permissions(user_id)
            return list(permissions)
        except Exception as e:
            logger.error(f"获取用户权限失败: {str(e)}", exc_info=True)
            return []
    
    async def get_user_roles(self, user_id: str) -> List[str]:
        """获取用户角色用例"""
        try:
            return await self.role_permission_domain_service.get_user_roles(user_id)
        except Exception as e:
            logger.error(f"获取用户角色失败: {str(e)}", exc_info=True)
            return []
    
    async def is_user_admin(self, user_id: str) -> bool:
        """检查用户是否为管理员用例"""
        try:
            return await self.role_permission_domain_service.is_user_admin(user_id)
        except Exception as e:
            logger.error(f"检查用户管理员权限失败: {str(e)}", exc_info=True)
            return False
    
    async def get_user_permission_summary(self, user_id: str) -> Dict[str, Any]:
        """获取用户权限摘要用例"""
        try:
            return await self.role_permission_domain_service.get_user_permission_summary(user_id)
        except Exception as e:
            logger.error(f"获取用户权限摘要失败: {str(e)}", exc_info=True)
            return {}
