"""
角色仓储实现

实现角色数据访问的具体逻辑。
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from app.identity_access.infrastructure.db.user import Role as RoleModel, Permission
from ...interfaces.repository_interfaces import IRoleRepository
from ...interfaces.converter_interfaces import IRoleConverter
from app.identity_access.domain.entities.role import RoleEntity
from app.identity_access.domain.entities.permission import PermissionEntity


class RoleRepository(IRoleRepository):
    """角色仓储实现"""
    
    def __init__(self, db: Session, role_converter: IRoleConverter):
        self.db = db
        self.role_converter = role_converter
    
    async def get_by_id(self, role_id: str) -> Optional[RoleModel]:
        """根据ID获取角色"""
        role_model = self.db.query(RoleModel).filter(RoleModel.id == role_id).first()
        if not role_model:
            return None
        
        return self.role_converter.from_model(role_model)
    
    async def get_by_name(self, name: str) -> Optional[RoleModel]:
        """根据名称获取角色"""
        role_model = self.db.query(RoleModel).filter(RoleModel.name == name).first()
        if not role_model:
            return None
        
        return self.role_converter.from_model(role_model)
    
    async def get_all(self) -> List[RoleModel]:
        """获取所有角色"""
        roles = self.db.query(RoleModel).all()
        return [self.role_converter.from_model(role) for role in roles]
    
    async def exists_by_name(self, name: str) -> bool:
        """检查角色名称是否存在"""
        return self.db.query(RoleModel).filter(RoleModel.name == name).first() is not None
    
    async def save(self, role: RoleModel) -> RoleModel:
        """保存角色"""
        # 检查角色是否存在
        existing_role = self.db.query(RoleModel).filter(RoleModel.id == role.id).first()
        
        if existing_role:
            # 更新现有角色
            role_dict = self.role_converter.to_model_dict(role)
            for key, value in role_dict.items():
                if key != "id":  # 不更新ID
                    setattr(existing_role, key, value)
            
            self.db.commit()
            self.db.refresh(existing_role)
            return self.role_converter.from_model(existing_role)
        else:
            # 创建新角色
            role_dict = self.role_converter.to_model_dict(role)
            new_role = RoleModel(**role_dict)
            
            self.db.add(new_role)
            self.db.commit()
            self.db.refresh(new_role)
            return self.role_converter.from_model(new_role)
    
    async def delete(self, role_id: str) -> bool:
        """删除角色"""
        role = self.db.query(RoleModel).filter(RoleModel.id == role_id).first()
        if not role:
            return False
        
        self.db.delete(role)
        self.db.commit()
        return True
    
    async def get_or_create(self, name: str, description: Optional[str] = None) -> RoleModel:
        """获取或创建角色"""
        # 先尝试获取现有角色
        existing_role = await self.get_by_name(name)
        if existing_role:
            return existing_role
        
        # 创建新角色
        role = RoleEntity.create(name=name, description=description)
        return await self.save(role)
    
    async def list_active(self, tenant_id: Optional[str] = None) -> List[RoleEntity]:
        """获取活跃角色列表"""
        query = self.db.query(RoleModel).filter(RoleModel.is_active == True)
        
        if tenant_id:
            query = query.filter(RoleModel.tenant_id == tenant_id)
        
        db_roles = query.all()
        return [self._to_entity(role) for role in db_roles]
    
    async def list_system_roles(self) -> List[RoleEntity]:
        """获取系统角色列表"""
        db_roles = self.db.query(RoleModel).filter(RoleModel.is_system == True).all()
        return [self._to_entity(role) for role in db_roles]
    
    async def list_admin_roles(self) -> List[RoleEntity]:
        """获取管理员角色列表"""
        db_roles = self.db.query(RoleModel).filter(RoleModel.is_admin == True).all()
        return [self._to_entity(role) for role in db_roles]
    
    async def assign_permission(self, role_id: str, permission_id: str) -> bool:
        """为角色分配权限"""
        try:
            role = self.db.query(RoleModel).filter(RoleModel.id == role_id).first()
            permission = self.db.query(Permission).filter(Permission.id == permission_id).first()
            
            if not role or not permission:
                return False
            
            # 检查是否已经存在关联
            if permission not in role.permissions:
                role.permissions.append(permission)
                self.db.commit()
            
            return True
        except Exception:
            self.db.rollback()
            return False
    
    async def remove_permission(self, role_id: str, permission_id: str) -> bool:
        """从角色移除权限"""
        try:
            role = self.db.query(RoleModel).filter(RoleModel.id == role_id).first()
            permission = self.db.query(Permission).filter(Permission.id == permission_id).first()
            
            if not role or not permission:
                return False
            
            # 移除关联
            if permission in role.permissions:
                role.permissions.remove(permission)
                self.db.commit()
            
            return True
        except Exception:
            self.db.rollback()
            return False
    
    async def get_permissions(self, role_id: str) -> List[PermissionEntity]:
        """获取角色的权限列表"""
        role = self.db.query(RoleModel).filter(RoleModel.id == role_id).first()
        if not role:
            return []
        
        permissions = role.permissions
        return [self._permission_to_entity(permission) for permission in permissions]
    
    def _to_entity(self, db_role: RoleModel) -> RoleEntity:
        """将数据库模型转换为领域实体"""
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
    
    def _permission_to_entity(self, db_permission: Permission) -> PermissionEntity:
        """将权限数据库模型转换为领域实体"""
        from app.identity_access.domain.value_objects.permission_type import PermissionType
        from app.identity_access.domain.value_objects.permission_scope import PermissionScope
        
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
