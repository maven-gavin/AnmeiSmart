"""
资源仓储实现

实现资源相关的数据访问操作。
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from app.identity_access.infrastructure.db.user import Resource, Permission
from app.identity_access.interfaces.repository_interfaces import IResourceRepository
from app.identity_access.domain.entities.resource import ResourceEntity
from app.identity_access.domain.entities.permission import PermissionEntity
from app.identity_access.domain.value_objects.resource_type import ResourceType
from app.identity_access.domain.value_objects.permission_type import PermissionType
from app.identity_access.domain.value_objects.permission_scope import PermissionScope


class ResourceRepository(IResourceRepository):
    """资源仓储实现"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_by_id(self, resource_id: str) -> Optional[ResourceEntity]:
        """根据ID获取资源"""
        db_resource = self.db.query(Resource).filter(Resource.id == resource_id).first()
        if not db_resource:
            return None
        
        return self._to_entity(db_resource)
    
    async def get_by_name(self, name: str) -> Optional[ResourceEntity]:
        """根据名称获取资源"""
        db_resource = self.db.query(Resource).filter(Resource.name == name).first()
        if not db_resource:
            return None
        
        return self._to_entity(db_resource)
    
    async def save(self, resource: ResourceEntity) -> ResourceEntity:
        """保存资源"""
        db_resource = self.db.query(Resource).filter(Resource.id == resource.id).first()
        
        if db_resource:
            # 更新现有资源
            self._update_db_model(db_resource, resource)
        else:
            # 创建新资源
            db_resource = self._to_db_model(resource)
            self.db.add(db_resource)
        
        self.db.commit()
        self.db.refresh(db_resource)
        
        return self._to_entity(db_resource)
    
    async def delete(self, resource_id: str) -> bool:
        """删除资源"""
        db_resource = self.db.query(Resource).filter(Resource.id == resource_id).first()
        if not db_resource:
            return False
        
        self.db.delete(db_resource)
        self.db.commit()
        return True
    
    async def list_active(self, tenant_id: Optional[str] = None, resource_type: Optional[str] = None) -> List[ResourceEntity]:
        """获取活跃资源列表"""
        query = self.db.query(Resource).filter(Resource.is_active == True)
        
        if tenant_id:
            query = query.filter(Resource.tenant_id == tenant_id)
        
        if resource_type:
            query = query.filter(Resource.resource_type == resource_type)
        
        db_resources = query.all()
        return [self._to_entity(resource) for resource in db_resources]
    
    async def list_system_resources(self, resource_type: Optional[str] = None) -> List[ResourceEntity]:
        """获取系统资源列表"""
        query = self.db.query(Resource).filter(Resource.is_system == True)
        
        if resource_type:
            query = query.filter(Resource.resource_type == resource_type)
        
        db_resources = query.all()
        return [self._to_entity(resource) for resource in db_resources]
    
    async def get_permissions(self, resource_id: str) -> List[PermissionEntity]:
        """获取资源关联的权限列表"""
        db_resource = self.db.query(Resource).filter(Resource.id == resource_id).first()
        if not db_resource:
            return []
        
        # 通过关联表获取权限
        db_permissions = db_resource.permissions
        return [self._permission_to_entity(permission) for permission in db_permissions]
    
    def _to_entity(self, db_resource: Resource) -> ResourceEntity:
        """将数据库模型转换为领域实体"""
        return ResourceEntity(
            id=db_resource.id,
            name=db_resource.name,
            displayName=db_resource.display_name,
            description=db_resource.description,
            resourceType=ResourceType(db_resource.resource_type) if db_resource.resource_type else ResourceType.API,
            resourcePath=db_resource.resource_path,
            httpMethod=db_resource.http_method,
            parentId=db_resource.parent_id,
            isActive=db_resource.is_active,
            isSystem=db_resource.is_system,
            priority=db_resource.priority,
            tenantId=db_resource.tenant_id,
            createdAt=db_resource.created_at,
            updatedAt=db_resource.updated_at
        )
    
    def _to_db_model(self, resource: ResourceEntity) -> Resource:
        """将领域实体转换为数据库模型"""
        return Resource(
            id=resource.id,
            name=resource.name,
            display_name=resource.displayName,
            description=resource.description,
            resource_type=resource.resourceType.value,
            resource_path=resource.resourcePath,
            http_method=resource.httpMethod,
            parent_id=resource.parentId,
            is_active=resource.isActive,
            is_system=resource.isSystem,
            priority=resource.priority,
            tenant_id=resource.tenantId,
            created_at=resource.createdAt,
            updated_at=resource.updatedAt
        )
    
    def _update_db_model(self, db_resource: Resource, resource: ResourceEntity) -> None:
        """更新数据库模型"""
        db_resource.name = resource.name
        db_resource.display_name = resource.displayName
        db_resource.description = resource.description
        db_resource.resource_type = resource.resourceType.value
        db_resource.resource_path = resource.resourcePath
        db_resource.http_method = resource.httpMethod
        db_resource.parent_id = resource.parentId
        db_resource.is_active = resource.isActive
        db_resource.is_system = resource.isSystem
        db_resource.priority = resource.priority
        db_resource.tenant_id = resource.tenantId
        db_resource.updated_at = resource.updatedAt
    
    def _permission_to_entity(self, db_permission: Permission) -> PermissionEntity:
        """将权限数据库模型转换为领域实体"""
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

