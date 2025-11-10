"""
权限仓储实现

实现权限相关的数据访问操作。
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.identity_access.infrastructure.db.user import Permission, Role
from app.identity_access.interfaces.repository_interfaces import IPermissionRepository
from app.identity_access.domain.entities.permission import PermissionEntity
from app.identity_access.domain.entities.role import RoleEntity
from app.identity_access.domain.value_objects.permission_type import PermissionType
from app.identity_access.domain.value_objects.permission_scope import PermissionScope


class PermissionRepository(IPermissionRepository):
    """权限仓储实现"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_by_id(self, permission_id: str) -> Optional[PermissionEntity]:
        """根据ID获取权限"""
        db_permission = self.db.query(Permission).filter(Permission.id == permission_id).first()
        if not db_permission:
            return None
        
        return self._to_entity(db_permission)
    
    async def get_by_name(self, name: str) -> Optional[PermissionEntity]:
        """根据名称获取权限"""
        db_permission = self.db.query(Permission).filter(Permission.name == name).first()
        if not db_permission:
            return None
        
        return self._to_entity(db_permission)
    
    async def save(self, permission: PermissionEntity) -> PermissionEntity:
        """保存权限"""
        db_permission = self.db.query(Permission).filter(Permission.id == permission.id).first()
        
        if db_permission:
            # 更新现有权限
            self._update_db_model(db_permission, permission)
        else:
            # 创建新权限
            db_permission = self._to_db_model(permission)
            self.db.add(db_permission)
        
        self.db.commit()
        self.db.refresh(db_permission)
        
        return self._to_entity(db_permission)
    
    async def delete(self, permission_id: str) -> bool:
        """删除权限"""
        db_permission = self.db.query(Permission).filter(Permission.id == permission_id).first()
        if not db_permission:
            return False
        
        self.db.delete(db_permission)
        self.db.commit()
        return True
    
    async def list_active(self, tenant_id: Optional[str] = None) -> List[PermissionEntity]:
        """获取活跃权限列表"""
        query = self.db.query(Permission).filter(Permission.is_active == True)
        
        if tenant_id:
            query = query.filter(Permission.tenant_id == tenant_id)
        
        db_permissions = query.all()
        return [self._to_entity(permission) for permission in db_permissions]
    
    async def list_system_permissions(self) -> List[PermissionEntity]:
        """获取系统权限列表"""
        db_permissions = self.db.query(Permission).filter(Permission.is_system == True).all()
        return [self._to_entity(permission) for permission in db_permissions]
    
    async def get_roles(self, permission_id: str) -> List[RoleEntity]:
        """获取拥有指定权限的角色列表"""
        db_permission = self.db.query(Permission).filter(Permission.id == permission_id).first()
        if not db_permission:
            return []
        
        # 通过关联表获取角色
        db_roles = db_permission.roles
        return [self._role_to_entity(role) for role in db_roles]
    
    def _to_entity(self, db_permission: Permission) -> PermissionEntity:
        """将数据库模型转换为领域实体"""
        return PermissionEntity(
            id=db_permission.id,
            name=db_permission.name,
            displayName=db_permission.display_name,
            description=db_permission.description,
            permissionType=PermissionType(db_permission.permission_type) if db_permission.permission_type else PermissionType.ACTION,
            scope=PermissionScope(db_permission.scope) if db_permission.scope else PermissionScope.TENANT,
            resource=db_permission.resource,
            action=db_permission.action,
            isActive=db_permission.is_active,
            isSystem=db_permission.is_system,
            isAdmin=db_permission.is_admin,
            priority=db_permission.priority,
            tenantId=db_permission.tenant_id,
            createdAt=db_permission.created_at,
            updatedAt=db_permission.updated_at
        )
    
    def _to_db_model(self, permission: PermissionEntity) -> Permission:
        """将领域实体转换为数据库模型"""
        return Permission(
            id=permission.id,
            name=permission.name,
            display_name=permission.displayName,
            description=permission.description,
            permission_type=permission.permissionType.value,
            scope=permission.scope.value,
            resource=permission.resource,
            action=permission.action,
            is_active=permission.isActive,
            is_system=permission.isSystem,
            is_admin=permission.isAdmin,
            priority=permission.priority,
            tenant_id=permission.tenantId,
            created_at=permission.createdAt,
            updated_at=permission.updatedAt
        )
    
    def _update_db_model(self, db_permission: Permission, permission: PermissionEntity) -> None:
        """更新数据库模型"""
        db_permission.name = permission.name
        db_permission.display_name = permission.displayName
        db_permission.description = permission.description
        db_permission.permission_type = permission.permissionType.value
        db_permission.scope = permission.scope.value
        db_permission.resource = permission.resource
        db_permission.action = permission.action
        db_permission.is_active = permission.isActive
        db_permission.is_system = permission.isSystem
        db_permission.is_admin = permission.isAdmin
        db_permission.priority = permission.priority
        db_permission.tenant_id = permission.tenantId
        db_permission.updated_at = permission.updatedAt
    
    def _role_to_entity(self, db_role: Role) -> RoleEntity:
        """将角色数据库模型转换为领域实体"""
        return RoleEntity(
            id=db_role.id,
            name=db_role.name,
            displayName=db_role.display_name,
            description=db_role.description,
            isActive=db_role.is_active,
            isSystem=db_role.is_system,
            isAdmin=db_role.is_admin,
            priority=db_role.priority,
            tenantId=db_role.tenant_id,
            createdAt=db_role.created_at,
            updatedAt=db_role.updated_at
        )
