"""
资源领域服务

处理资源管理相关的业务逻辑。
"""

from typing import Optional, List
import logging

from .entities.resource import ResourceEntity
from .entities.permission import PermissionEntity
from .value_objects.resource_type import ResourceType

logger = logging.getLogger(__name__)


class ResourceDomainService:
    """资源领域服务"""
    
    def __init__(self, resource_repository, permission_repository):
        self.resource_repository = resource_repository
        self.permission_repository = permission_repository
    
    # ==================== 资源管理 ====================
    
    async def create_resource(
        self,
        name: str,
        resource_type: ResourceType,
        resource_path: str,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        http_method: Optional[str] = None,
        parent_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        is_system: bool = False,
        priority: int = 0
    ) -> ResourceEntity:
        """创建新资源"""
        # 检查资源名称是否已存在
        existing_resource = await self.resource_repository.get_by_name(name)
        if existing_resource:
            raise ValueError(f"资源名称 '{name}' 已存在")
        
        # 创建资源
        resource = ResourceEntity.create(
            name=name,
            resourceType=resource_type,
            resourcePath=resource_path,
            displayName=display_name,
            description=description,
            httpMethod=http_method,
            parentId=parent_id,
            tenantId=tenant_id,
            isSystem=is_system,
            priority=priority
        )
        
        # 保存资源
        saved_resource = await self.resource_repository.save(resource)
        logger.info(f"创建资源成功: {saved_resource.name}")
        
        return saved_resource
    
    async def update_resource(
        self,
        resource_id: str,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        resource_path: Optional[str] = None,
        http_method: Optional[str] = None,
        priority: Optional[int] = None
    ) -> ResourceEntity:
        """更新资源"""
        resource = await self.resource_repository.get_by_id(resource_id)
        if not resource:
            raise ValueError(f"资源不存在: {resource_id}")
        
        # 更新资源信息
        resource.update_info(
            displayName=display_name,
            description=description,
            resourcePath=resource_path,
            httpMethod=http_method,
            priority=priority
        )
        
        # 保存更新
        updated_resource = await self.resource_repository.save(resource)
        logger.info(f"更新资源成功: {updated_resource.name}")
        
        return updated_resource
    
    async def delete_resource(self, resource_id: str) -> bool:
        """删除资源"""
        resource = await self.resource_repository.get_by_id(resource_id)
        if not resource:
            return False
        
        if not resource.can_be_deleted():
            raise ValueError("系统资源不能被删除")
        
        # 删除资源
        result = await self.resource_repository.delete(resource_id)
        if result:
            logger.info(f"删除资源成功: {resource.name}")
        
        return result
    
    async def sync_resource(
        self,
        name: str,
        resource_type: ResourceType,
        resource_path: str,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        http_method: Optional[str] = None,
        parent_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        is_system: bool = True,
        priority: int = 0
    ) -> ResourceEntity:
        """同步资源（创建或更新）"""
        existing_resource = await self.resource_repository.get_by_name(name)
        
        if existing_resource:
            # 更新现有资源
            existing_resource.update_info(
                displayName=display_name or existing_resource.displayName,
                description=description or existing_resource.description,
                resourcePath=resource_path,
                httpMethod=http_method,
                priority=priority
            )
            return await self.resource_repository.save(existing_resource)
        else:
            # 创建新资源
            return await self.create_resource(
                name=name,
                resource_type=resource_type,
                resource_path=resource_path,
                display_name=display_name,
                description=description,
                http_method=http_method,
                parent_id=parent_id,
                tenant_id=tenant_id,
                is_system=is_system,
                priority=priority
            )
    
    # ==================== 资源权限关联 ====================
    
    async def assign_permission_to_resource(
        self,
        resource_id: str,
        permission_id: str
    ) -> bool:
        """为资源分配权限"""
        resource = await self.resource_repository.get_by_id(resource_id)
        if not resource:
            raise ValueError(f"资源不存在: {resource_id}")
        
        permission = await self.permission_repository.get_by_id(permission_id)
        if not permission:
            raise ValueError(f"权限不存在: {permission_id}")
        
        # 这里需要更新数据库关联表
        # 由于使用了SQLAlchemy的relationship，可以通过直接操作关联对象来实现
        # 但为了保持领域服务的纯净性，这里只做验证，实际的关联操作在应用层或仓储层处理
        logger.info(f"为资源 {resource.name} 分配权限 {permission.name}")
        
        return True
    
    async def remove_permission_from_resource(
        self,
        resource_id: str,
        permission_id: str
    ) -> bool:
        """移除资源的权限"""
        resource = await self.resource_repository.get_by_id(resource_id)
        if not resource:
            raise ValueError(f"资源不存在: {resource_id}")
        
        permission = await self.permission_repository.get_by_id(permission_id)
        if not permission:
            raise ValueError(f"权限不存在: {permission_id}")
        
        logger.info(f"从资源 {resource.name} 移除权限 {permission.name}")
        
        return True
    
    async def get_resource_permissions(self, resource_id: str) -> List[PermissionEntity]:
        """获取资源关联的权限列表"""
        return await self.resource_repository.get_permissions(resource_id)

