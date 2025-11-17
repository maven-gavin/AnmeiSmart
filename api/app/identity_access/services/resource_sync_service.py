"""
资源同步服务

负责同步API资源和菜单资源到资源库。
"""

import logging
from typing import List, Dict, Any
from fastapi import FastAPI

from ..domain.resource_domain_service import ResourceDomainService
from ..domain.value_objects.resource_type import ResourceType

logger = logging.getLogger(__name__)


class ResourceSyncService:
    """资源同步服务"""
    
    def __init__(self, resource_domain_service: ResourceDomainService):
        self.resource_domain_service = resource_domain_service
    
    async def sync_api_resources(self, app: FastAPI) -> Dict[str, int]:
        """
        从OpenAPI文档同步API资源到资源库
        
        使用OpenAPI文档作为数据源，可以获取更完整的API信息：
        - 路径和方法
        - 标签（tags）
        - 摘要（summary）
        - 描述（description）
        
        如果OpenAPI文档不可用或格式不正确，将记录警告并返回空结果。
        """
        created_count = 0
        updated_count = 0
        
        try:
            # 获取OpenAPI文档
            openapi_schema = app.openapi()
            
            if not openapi_schema:
                logger.warning("无法获取OpenAPI文档，跳过API资源同步")
                return {
                    "synced_count": 0,
                    "created_count": 0,
                    "updated_count": 0
                }
            
            if 'paths' not in openapi_schema:
                logger.warning("OpenAPI文档中没有找到paths信息，跳过API资源同步")
                return {
                    "synced_count": 0,
                    "created_count": 0,
                    "updated_count": 0
                }
            
            paths = openapi_schema.get('paths', {})
            
            if not paths:
                logger.warning("OpenAPI文档中paths为空，跳过API资源同步")
                return {
                    "synced_count": 0,
                    "created_count": 0,
                    "updated_count": 0
                }
            
            # 遍历所有路径
            for path, path_item in paths.items():
                # 跳过非API路径（如WebSocket、内部路径等）
                if path.startswith('/.well-known') or path.startswith('/docs') or path.startswith('/openapi'):
                    continue
                
                # 遍历路径的所有HTTP方法
                for method, operation in path_item.items():
                    # 跳过非HTTP方法的键（如parameters、servers等）
                    if method.upper() not in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']:
                        continue
                    
                    # 跳过OPTIONS和HEAD方法
                    if method.upper() in ['OPTIONS', 'HEAD']:
                        continue
                    
                    # 确保operation是字典类型
                    if not isinstance(operation, dict):
                        logger.warning(f"路径 {path} 的方法 {method} 的操作信息不是字典类型，跳过")
                        continue
                    
                    # 从OpenAPI操作中提取信息
                    operation_id = operation.get('operationId', '')
                    summary = operation.get('summary', '')
                    description = operation.get('description', '')
                    
                    # 资源名称使用 OpenAPI 的 operationId 在 '_api_v1_' 之前的部分；缺失则跳过
                    if not operation_id:
                        logger.warning(f"路径 {path} 的方法 {method} 缺少 operationId，跳过该端点")
                        continue
                    base_name = operation_id.split("_api_v1_")[0] if "_api_v1_" in operation_id else operation_id
                    resource_name = base_name[:100]
                    
                    # 生成显示名称：优先summary，否则使用operationId
                    display_name = summary if summary else operation_id
                    
                    # 生成描述：使用description（可能为空字符串）
                    resource_description = description or ""
                    
                    # 检查资源是否已存在
                    existing_resource = await self.resource_domain_service.resource_repository.get_by_name(resource_name)
                    
                    if existing_resource:
                        updated_count += 1
                    else:
                        created_count += 1
                    
                    # 同步资源
                    await self.resource_domain_service.sync_resource(
                        name=resource_name,
                        resource_type=ResourceType.API,
                        resource_path=path,
                        http_method=method.upper(),
                        display_name=display_name,
                        description=resource_description,
                        tenant_id=None,  # API资源默认系统级
                        is_system=True,
                        priority=0
                    )
            
            logger.info(f"API资源同步完成: 创建 {created_count} 个，更新 {updated_count} 个")
            
            return {
                "synced_count": created_count + updated_count,
                "created_count": created_count,
                "updated_count": updated_count
            }
            
        except Exception as e:
            logger.error(f"同步API资源失败: {str(e)}", exc_info=True)
            logger.warning("由于OpenAPI文档处理失败，跳过API资源同步")
            return {
                "synced_count": 0,
                "created_count": 0,
                "updated_count": 0
            }
    
    async def sync_menu_resources(self, menus: List[Dict[str, Any]]) -> Dict[str, int]:
        """同步菜单资源到资源库"""
        created_count = 0
        updated_count = 0
        
        try:
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
                    tenant_id=None,  # 菜单资源默认系统级
                    is_system=True,
                    priority=menu.get('priority', 0)
                )
            
            logger.info(f"菜单资源同步完成: 创建 {created_count} 个，更新 {updated_count} 个")
            
            return {
                "synced_count": created_count + updated_count,
                "created_count": created_count,
                "updated_count": updated_count
            }
            
        except Exception as e:
            logger.error(f"同步菜单资源失败: {str(e)}", exc_info=True)
            raise

