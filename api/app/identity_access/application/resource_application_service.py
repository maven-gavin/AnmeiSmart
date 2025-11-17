"""
资源应用服务

处理资源管理相关的应用用例。
"""

import logging
from typing import List, Optional, Dict, Any

from ..domain.resource_domain_service import ResourceDomainService
from ..domain.entities.resource import ResourceEntity
from ..domain.value_objects.resource_type import ResourceType

logger = logging.getLogger(__name__)


class ResourceApplicationService:
    """资源应用服务"""
    
    def __init__(self, resource_domain_service: ResourceDomainService):
        self.resource_domain_service = resource_domain_service
    
    # ==================== 资源管理用例 ====================
    
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
    ) -> Dict[str, Any]:
        """创建资源用例"""
        try:
            resource = await self.resource_domain_service.create_resource(
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
            
            return self._to_dict(resource)
            
        except Exception as e:
            logger.error(f"创建资源失败: {str(e)}", exc_info=True)
            raise
    
    async def get_resource(self, resource_id: str) -> Optional[Dict[str, Any]]:
        """获取资源用例"""
        try:
            resource = await self.resource_domain_service.resource_repository.get_by_id(resource_id)
            if not resource:
                return None
            
            return self._to_dict(resource)
            
        except Exception as e:
            logger.error(f"获取资源失败: {str(e)}", exc_info=True)
            raise
    
    async def update_resource(
        self,
        resource_id: str,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        resource_path: Optional[str] = None,
        http_method: Optional[str] = None,
        priority: Optional[int] = None
    ) -> Dict[str, Any]:
        """更新资源用例"""
        try:
            resource = await self.resource_domain_service.update_resource(
                resource_id=resource_id,
                display_name=display_name,
                description=description,
                resource_path=resource_path,
                http_method=http_method,
                priority=priority
            )
            
            return self._to_dict(resource)
            
        except Exception as e:
            logger.error(f"更新资源失败: {str(e)}", exc_info=True)
            raise
    
    async def delete_resource(self, resource_id: str) -> bool:
        """删除资源用例"""
        try:
            return await self.resource_domain_service.delete_resource(resource_id)
        except Exception as e:
            logger.error(f"删除资源失败: {str(e)}", exc_info=True)
            raise
    
    async def list_resources(
        self,
        tenant_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[Dict[str, Any]], int]:
        """获取资源列表用例，返回(资源列表, 总数)"""
        try:
            resources = await self.resource_domain_service.resource_repository.list_active(
                tenant_id=tenant_id,
                resource_type=resource_type
            )
            
            # 获取总数
            total = len(resources)
            
            # 分页
            resources = resources[skip:skip + limit]
            
            return ([self._to_dict(resource) for resource in resources], total)
            
        except Exception as e:
            logger.error(f"获取资源列表失败: {str(e)}", exc_info=True)
            raise
    
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
    ) -> Dict[str, Any]:
        """同步资源用例（创建或更新）"""
        try:
            resource = await self.resource_domain_service.sync_resource(
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
            
            return self._to_dict(resource)
            
        except Exception as e:
            logger.error(f"同步资源失败: {str(e)}", exc_info=True)
            raise
    
    async def sync_menu_resources(self, menus: List[Dict[str, Any]]) -> Dict[str, int]:
        """同步菜单资源用例"""
        try:
            created_count = 0
            updated_count = 0
            
            for menu in menus:
                name = menu.get('name')
                if not name:
                    continue
                
                # 检查资源是否已存在
                existing_resource = await self.resource_domain_service.resource_repository.get_by_name(name)
                
                if existing_resource:
                    updated_count += 1
                else:
                    created_count += 1
                
                # 同步资源
                await self.resource_domain_service.sync_resource(
                    name=name,
                    resource_type=ResourceType.MENU,
                    resource_path=menu.get('resourcePath', ''),
                    display_name=menu.get('displayName'),
                    description=menu.get('description'),
                    parent_id=menu.get('parentId'),
                    tenant_id=None,
                    is_system=True,
                    priority=menu.get('priority', 0)
                )
            
            return {
                "synced_count": created_count + updated_count,
                "created_count": created_count,
                "updated_count": updated_count
            }
            
        except Exception as e:
            logger.error(f"同步菜单资源失败: {str(e)}", exc_info=True)
            raise
    
    def _to_dict(self, resource: ResourceEntity) -> Dict[str, Any]:
        """将资源实体转换为字典"""
        return {
            "id": resource.id,
            "name": resource.name,
            "display_name": resource.displayName,
            "description": resource.description,
            "resource_type": resource.resourceType.value,
            "resource_path": resource.resourcePath,
            "http_method": resource.httpMethod,
            "parent_id": resource.parentId,
            "is_active": resource.isActive,
            "is_system": resource.isSystem,
            "priority": resource.priority,
            "tenant_id": resource.tenantId,
            "created_at": resource.createdAt.isoformat(),
            "updated_at": resource.updatedAt.isoformat()
        }

