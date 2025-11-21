"""
角色权限领域服务

处理角色和权限管理相关的业务逻辑，支持数据库配置的角色权限系统。
"""

from typing import Optional, List, Set, Dict
import logging

from .entities.role import RoleEntity
from .entities.permission import PermissionEntity
from .entities.user import UserEntity
from .value_objects.permission_type import PermissionType
from .value_objects.permission_scope import PermissionScope

logger = logging.getLogger(__name__)


class RolePermissionDomainService:
    """角色权限领域服务"""
    
    def __init__(self, role_repository, permission_repository, user_repository):
        self.role_repository = role_repository
        self.permission_repository = permission_repository
        self.user_repository = user_repository
    
    # ==================== 角色管理 ====================
    
    async def create_role(
        self,
        name: str,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        tenant_id: Optional[str] = None,
        is_system: bool = False,
        is_admin: bool = False
    ) -> RoleEntity:
        """创建新角色"""
        # 检查角色名称是否已存在
        existing_role = await self.role_repository.get_by_name(name)
        if existing_role:
            raise ValueError(f"角色名称 '{name}' 已存在")
        
        # 创建角色
        roleEntity = RoleEntity.create(
            name=name,
            displayName=display_name,
            description=description,
            tenantId=tenant_id,
            isSystem=is_system,
            isAdmin=is_admin
        )
        
        # 保存角色
        await self.role_repository.save(roleEntity)
        logger.info(f"创建角色: {roleEntity.name} (ID: {roleEntity.id})")
        
        return roleEntity
    
    async def get_role_by_id(self, role_id: str) -> Optional[RoleEntity]:
        """根据ID获取角色"""
        return await self.role_repository.get_by_id(role_id)
    
    async def get_role_by_name(self, name: str) -> Optional[RoleEntity]:
        """根据名称获取角色"""
        return await self.role_repository.get_by_name(name)
    
    async def list_active_roles(self, tenant_id: Optional[str] = None) -> List[RoleEntity]:
        """获取所有激活的角色"""
        return await self.role_repository.list_active(tenant_id)
    
    async def list_system_roles(self) -> List[RoleEntity]:
        """获取所有系统角色"""
        return await self.role_repository.list_system_roles()
    
    async def update_role(
        self,
        role_id: str,
        name: Optional[str] = None,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_system: Optional[bool] = None,
        is_admin: Optional[bool] = None,
        priority: Optional[int] = None
    ) -> RoleEntity:
        """更新角色"""
        from datetime import datetime
        
        role = await self.role_repository.get_by_id(role_id)
        if not role:
            raise ValueError("角色不存在")

        # 检查名称唯一性
        if name is not None and name != role.name:
            normalized_name = name.strip()
            if not normalized_name:
                raise ValueError("角色名称不能为空")
                
            if role.isSystem:
                raise ValueError("系统角色名称不可修改")
            
            existing_role = await self.role_repository.get_by_name(normalized_name)
            if existing_role and existing_role.id != role.id:
                raise ValueError(f"角色名称 '{normalized_name}' 已存在")
            role.name = normalized_name

        if display_name is not None:
            role.displayName = display_name.strip() if display_name.strip() else role.name
        
        if description is not None:
            role.description = description.strip() or None
            
        if is_active is not None:
            if not is_active and role.isSystem:
                raise ValueError("系统角色必须保持启用状态")
            role.isActive = is_active
            
        if is_system is not None:
            # 如果尝试更改系统角色状态，需要额外检查（通常不允许随意更改）
            role.isSystem = is_system
            
        if is_admin is not None:
            role.isAdmin = is_admin
            
        if priority is not None:
            if priority < 0:
                raise ValueError("角色优先级不能为负数")
            role.priority = priority
            
        role.updatedAt = datetime.utcnow()
        
        # 保存更新
        updated_role = await self.role_repository.save(role)
        logger.info(f"更新角色: {role.name} (ID: {role.id})")
        return updated_role

    async def delete_role(self, role_id: str) -> bool:
        """删除角色"""
        role = await self.role_repository.get_by_id(role_id)
        if not role:
            raise ValueError("角色不存在")
            
        if role.isSystem:
            raise ValueError("不能删除系统基础角色")
            
        await self.role_repository.delete(role_id)
        logger.info(f"删除角色: {role.name} (ID: {role.id})")
        return True

    # ==================== 权限管理 ====================
    
    async def create_permission(
        self,
        name: str,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        permission_type: PermissionType = PermissionType.ACTION,
        scope: PermissionScope = PermissionScope.TENANT,
        resource: Optional[str] = None,
        action: Optional[str] = None,
        tenant_id: Optional[str] = None,
        is_system: bool = False,
        is_admin: bool = False
    ) -> PermissionEntity:
        """创建新权限"""
        # 检查权限名称是否已存在
        existing_permission = await self.permission_repository.get_by_name(name)
        if existing_permission:
            raise ValueError(f"权限名称 '{name}' 已存在")
        
        # 创建权限
        permissionEntity = PermissionEntity.create(
            name=name,
            displayName=display_name,
            description=description,
            permissionType=permission_type,
            scope=scope,
            resource=resource,
            action=action,
            tenantId=tenant_id,
            isSystem=is_system,
            isAdmin=is_admin
        )
        
        # 保存权限
        await self.permission_repository.save(permissionEntity)
        logger.info(f"创建权限: {permissionEntity.name} (ID: {permissionEntity.id})")
        
        return permissionEntity
    
    async def get_permission_by_id(self, permission_id: str) -> Optional[PermissionEntity]:
        """根据ID获取权限"""
        return await self.permission_repository.get_by_id(permission_id)
    
    async def get_permission_by_name(self, name: str) -> Optional[PermissionEntity]:
        """根据名称获取权限"""
        return await self.permission_repository.get_by_name(name)
    
    async def list_active_permissions(self, tenant_id: Optional[str] = None) -> List[PermissionEntity]:
        """获取所有激活的权限"""
        return await self.permission_repository.list_active(tenant_id)
    
    async def list_system_permissions(self) -> List[PermissionEntity]:
        """获取所有系统权限"""
        return await self.permission_repository.list_system_permissions()
    
    # ==================== 角色权限关联 ====================
    
    async def assign_permission_to_role(self, role_id: str, permission_id: str) -> bool:
        """为角色分配权限"""
        role = await self.role_repository.get_by_id(role_id)
        permissionEntity = await self.permission_repository.get_by_id(permission_id)
        
        if not role or not permissionEntity:
            return False
        
        if not role.is_available() or not permissionEntity.is_available():
            raise ValueError("角色或权限不可用")
        
        # 检查权限范围是否匹配
        if permissionEntity.scope == PermissionScope.SYSTEM and not role.is_system_role():
            raise ValueError("系统权限只能分配给系统角色")
        
        await self.role_repository.assign_permission(role_id, permission_id)
        logger.info(f"为角色 {role.name} 分配权限 {permissionEntity.name}")
        
        return True
    
    async def remove_permission_from_role(self, role_id: str, permission_id: str) -> bool:
        """从角色移除权限"""
        role = await self.role_repository.get_by_id(role_id)
        permissionEntity = await self.permission_repository.get_by_id(permission_id)
        
        if not role or not permissionEntity:
            return False
        
        if role.is_system_role() and permissionEntity.is_system_permission():
            raise ValueError("系统角色的系统权限不能被移除")
        
        await self.role_repository.remove_permission(role_id, permission_id)
        logger.info(f"从角色 {role.name} 移除权限 {permissionEntity.name}")
        
        return True
    
    async def get_role_permissions(self, role_id: str) -> List[PermissionEntity]:
        """获取角色的所有权限"""
        return await self.role_repository.get_permissions(role_id)
    
    async def get_permission_roles(self, permission_id: str) -> List[RoleEntity]:
        """获取拥有指定权限的所有角色"""
        return await self.permission_repository.get_roles(permission_id)
    
    # ==================== 用户权限检查 ====================
    
    async def check_user_permission(self, user_id: str, permission_name: str) -> bool:
        """检查用户是否有指定权限"""
        user = await self.user_repository.get_by_id(user_id)
        if not user or not user.can_access_system():
            return False
        
        # 获取用户的所有角色
        user_roles = await self.user_repository.get_user_roles(user_id)
        
        # 检查每个角色是否有该权限
        for role in user_roles:
            if not role.is_available():
                continue
            
            # 检查数据库配置的权限
            role_permissions = await self.get_role_permissions(role.id)
            for permissionEntity in role_permissions:
                if permissionEntity.matches_permission(permission_name):
                    return True
            
            # 检查传统角色权限（向后兼容）
            if role.has_legacy_permission(permission_name):
                return True
        
        return False
    
    async def check_user_role(self, user_id: str, role_name: str) -> bool:
        """检查用户是否有指定角色"""
        user = await self.user_repository.get_by_id(user_id)
        if not user or not user.can_access_system():
            return False
        
        # 检查数据库配置的角色
        user_roles = await self.user_repository.get_user_roles(user_id)
        for role in user_roles:
            if role.is_available() and role.name == role_name:
                return True
        
        # 检查传统角色（向后兼容）
        return role_name in user.roles
    
    async def get_user_permissions(self, user_id: str) -> Set[str]:
        """获取用户的所有权限"""
        user = await self.user_repository.get_by_id(user_id)
        if not user or not user.can_access_system():
            return set()
        
        permissions = set()
        
        # 获取用户的所有角色
        user_roles = await self.user_repository.get_user_roles(user_id)
        
        for role in user_roles:
            if not role.is_available():
                continue
            
            # 获取数据库配置的权限
            role_permissions = await self.get_role_permissions(role.id)
            for permissionEntity in role_permissions:
                permissions.add(permissionEntity.get_permission_key())
            
            # 获取传统角色权限（向后兼容）
            permissions.update(role.get_legacy_permissions())
        
        return permissions
    
    async def get_user_roles(self, user_id: str) -> List[str]:
        """获取用户的所有角色名称"""
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            return []
        
        roles = []
        
        # 获取数据库配置的角色
        user_roles = await self.user_repository.get_user_roles(user_id)
        for role in user_roles:
            if role.is_available():
                roles.append(role.name)
        
        # 获取传统角色（向后兼容）
        for role_name in user.roles:
            if role_name not in roles:
                roles.append(role_name)
        
        return roles
    
    async def is_user_admin(self, user_id: str) -> bool:
        """检查用户是否为管理员"""
        user_roles = await self.get_user_roles(user_id)
        
        # 检查数据库配置的管理员角色
        db_roles = await self.role_repository.list_admin_roles()
        for role in db_roles:
            if role.is_available() and role.name in user_roles:
                return True
        
        # 检查传统管理员角色（向后兼容）
        admin_roles = ["administrator", "operator"]
        return any(role in admin_roles for role in user_roles)
    
    async def get_user_permission_summary(self, user_id: str) -> Dict:
        """获取用户权限摘要"""
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            return {}
        
        roles = await self.get_user_roles(user_id)
        permissions = await self.get_user_permissions(user_id)
        is_admin = await self.is_user_admin(user_id)
        
        return {
            "user_id": user_id,
            "username": user.username,
            "roles": roles,
            "permissions": list(permissions),
            "is_admin": is_admin,
            "tenant_id": user.tenantId
        }
