"""
权限管理控制器
"""
from fastapi import APIRouter, Depends, Query, status, Body, Request
from typing import Optional, List
from sqlalchemy.orm import Session
import logging
import json

from app.common.deps import get_db
from app.identity_access.models.user import User, Permission
from app.identity_access.services.permission_service import PermissionService
from app.identity_access.services.resource_service import ResourceService
from app.identity_access.schemas.permission_schemas import (
    PermissionCreate, PermissionUpdate, PermissionResponse, PermissionListResponse
)
from app.identity_access.schemas.resource_schemas import ResourceResponse, ResourceType
from app.identity_access.enums import PermissionType, PermissionScope
from app.identity_access.deps.auth_deps import get_current_user, require_role
from app.identity_access.controllers.resources import get_resource_service
from app.core.api import ApiResponse, BusinessException, ErrorCode, SystemException

logger = logging.getLogger(__name__)

router = APIRouter()

def _handle_unexpected_error(message: str, exc: Exception) -> SystemException:
    return SystemException(message=message, code=ErrorCode.SYSTEM_ERROR)

def get_permission_service(db: Session = Depends(get_db)) -> PermissionService:
    return PermissionService(db)

def _convert_permission_to_response(permission: Permission) -> PermissionResponse:
    """将 Permission 模型转换为 PermissionResponse"""
    # 处理 permission_type：如果为无效值，使用 ACTION 作为默认值
    permission_type_value = permission.permission_type
    try:
        permission_type_value = PermissionType(permission_type_value.lower())
    except ValueError:
        # 如果枚举中没有对应的值，使用 ACTION 作为默认值
        permission_type_value = PermissionType.ACTION
    
    # 处理 scope：如果为无效值，使用 TENANT 作为默认值
    scope_value = permission.scope
    try:
        scope_value = PermissionScope(scope_value.lower())
    except ValueError:
        # 如果枚举中没有对应的值，使用 TENANT 作为默认值
        scope_value = PermissionScope.TENANT
    
    return PermissionResponse(
        id=permission.id,
        code=permission.code,
        name=permission.name,
        display_name=permission.display_name,
        description=permission.description,
        permission_type=permission_type_value,
        scope=scope_value,
        is_active=permission.is_active if permission.is_active is not None else True,
        is_system=permission.is_system if permission.is_system is not None else False,
        is_admin=permission.is_admin if permission.is_admin is not None else False,
        priority=permission.priority if permission.priority is not None else 0,
        created_at=permission.created_at,
        updated_at=permission.updated_at,
    )

@router.get("", response_model=ApiResponse[PermissionListResponse])
async def list_permissions(
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=1000, description="限制数量"),
    current_user: User = Depends(require_role("admin")),
    permission_service: PermissionService = Depends(get_permission_service)
) -> ApiResponse[PermissionListResponse]:
    """获取权限列表（全局，不区分租户）"""
    try:
        # 获取所有权限（全局）
        all_permissions = permission_service.get_all_permissions()
        
        total = len(all_permissions)
        
        # 分页
        paged_permissions = all_permissions[skip:skip + limit]
        
        # 转换为响应格式
        permission_responses = [
            _convert_permission_to_response(permission)
            for permission in paged_permissions
        ]
        
        return ApiResponse.success(
            data=PermissionListResponse(
                permissions=permission_responses,
                total=total,
                skip=skip,
                limit=limit
            ),
            message="获取权限列表成功"
        )
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("获取权限列表失败", e)

@router.get("/{permission_id}", response_model=ApiResponse[PermissionResponse])
async def get_permission(
    permission_id: str,
    current_user: User = Depends(require_role("admin")),
    permission_service: PermissionService = Depends(get_permission_service)
) -> ApiResponse[PermissionResponse]:
    """获取权限详情"""
    try:
        permission = permission_service.get_by_id(permission_id)
        if not permission:
            raise BusinessException("权限不存在", code=ErrorCode.NOT_FOUND, status_code=status.HTTP_404_NOT_FOUND)
        
        permission_response = _convert_permission_to_response(permission)
        
        return ApiResponse.success(permission_response, message="获取权限详情成功")
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("获取权限详情失败", e)

@router.post("", response_model=ApiResponse[PermissionResponse], status_code=status.HTTP_201_CREATED)
async def create_permission(
    permission_in: PermissionCreate,
    current_user: User = Depends(require_role("admin")),
    permission_service: PermissionService = Depends(get_permission_service)
) -> ApiResponse[PermissionResponse]:
    """创建权限"""
    try:
        permission = permission_service.create_permission(permission_in)
        permission_response = _convert_permission_to_response(permission)
        
        return ApiResponse.success(permission_response, message="创建权限成功")
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("创建权限失败", e)

@router.put("/{permission_id}", response_model=ApiResponse[PermissionResponse])
async def update_permission(
    permission_id: str,
    permission_in: PermissionUpdate,
    current_user: User = Depends(require_role("admin")),
    permission_service: PermissionService = Depends(get_permission_service)
) -> ApiResponse[PermissionResponse]:
    """更新权限"""
    try:
        permission = permission_service.update_permission(permission_id, permission_in)
        permission_response = _convert_permission_to_response(permission)
        
        return ApiResponse.success(permission_response, message="更新权限成功")
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("更新权限失败", e)

@router.delete("/{permission_id}", status_code=status.HTTP_200_OK)
async def delete_permission(
    permission_id: str,
    current_user: User = Depends(require_role("admin")),
    permission_service: PermissionService = Depends(get_permission_service)
) -> ApiResponse[dict]:
    """删除权限（物理删除）"""
    try:
        permission = permission_service.get_by_id(permission_id)
        if not permission:
            raise BusinessException("权限不存在", code=ErrorCode.NOT_FOUND, status_code=status.HTTP_404_NOT_FOUND)
        
        # 系统权限不允许删除
        if permission.is_system:
            raise BusinessException("系统权限无法删除", code=ErrorCode.PERMISSION_DENIED, status_code=status.HTTP_403_FORBIDDEN)
        
        success = permission_service.delete_permission(permission_id)
        if not success:
            raise BusinessException("删除权限失败", code=ErrorCode.SYSTEM_ERROR)
        
        return ApiResponse.success({}, message="删除权限成功")
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("删除权限失败", e)

@router.get("/{permission_id}/resources", response_model=ApiResponse[List[ResourceResponse]])
async def get_permission_resources(
    permission_id: str,
    current_user: User = Depends(require_role("admin")),
    permission_service: PermissionService = Depends(get_permission_service),
    resource_service: ResourceService = Depends(get_resource_service)
) -> ApiResponse[List[ResourceResponse]]:
    """获取权限已分配的资源"""
    try:
        resources = permission_service.get_permission_resources(permission_id)
        
        resource_responses = [
            ResourceResponse(
                id=resource.id,
                name=resource.name,
                display_name=resource.display_name,
                description=resource.description,
                resource_type=ResourceType(resource.resource_type),
                resource_path=resource.resource_path,
                http_method=resource.http_method,
                parent_id=resource.parent_id,
                priority=resource.priority,
                is_active=resource.is_active,
                is_system=resource.is_system,
                created_at=resource.created_at,
                updated_at=resource.updated_at,
            )
            for resource in resources
        ]
        
        return ApiResponse.success(resource_responses, message="获取权限资源成功")
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("获取权限资源失败", e)

@router.post("/{permission_id}/resources/assign", response_model=ApiResponse[dict])
async def assign_resources_to_permission(
    permission_id: str,
    request: Request,
    current_user: User = Depends(require_role("admin")),
    permission_service: PermissionService = Depends(get_permission_service)
) -> ApiResponse[dict]:
    """为权限分配资源"""
    try:
        # 详细的调试日志
        logger.info("=" * 80)
        logger.info(f"分配资源请求开始 - permission_id: {permission_id}")
        logger.info(f"请求方法: {request.method}")
        logger.info(f"请求URL: {request.url}")
        logger.info(f"请求头:")
        for key, value in request.headers.items():
            logger.info(f"  {key}: {value}")
        
        # 读取原始请求体
        try:
            body_bytes = await request.body()
            logger.info(f"原始请求体 (bytes): {body_bytes}")
            logger.info(f"原始请求体长度: {len(body_bytes)}")
            
            if body_bytes:
                import json
                try:
                    body_json = json.loads(body_bytes.decode('utf-8'))
                    logger.info(f"解析后的请求体 (JSON): {body_json}")
                    logger.info(f"解析后的请求体类型: {type(body_json)}")
                except json.JSONDecodeError as e:
                    logger.error(f"JSON解析失败: {e}")
                    logger.error(f"原始内容: {body_bytes.decode('utf-8', errors='ignore')}")
            else:
                logger.warning("请求体为空!")
        except Exception as e:
            logger.error(f"读取请求体失败: {e}", exc_info=True)
        
        # 尝试从请求中获取 JSON 数据
        try:
            body_data = await request.json()
            logger.info(f"从 request.json() 获取的数据: {body_data}")
            logger.info(f"数据类型: {type(body_data)}")
            
            # 处理不同的数据格式
            if isinstance(body_data, list):
                resource_ids = body_data
                logger.info(f"请求体是数组，直接使用: {resource_ids}")
            elif isinstance(body_data, dict):
                if 'resource_ids' in body_data:
                    resource_ids = body_data['resource_ids']
                    logger.info(f"从字典中提取 resource_ids: {resource_ids}")
                elif 'json' in body_data:
                    resource_ids = body_data['json']
                    logger.info(f"从 json 字段中提取: {resource_ids}")
                elif 'body' in body_data:
                    # 如果 body 字段是数组，直接使用
                    if isinstance(body_data['body'], list):
                        resource_ids = body_data['body']
                        logger.info(f"从 body 字段中提取数组: {resource_ids}")
                    else:
                        logger.warning(f"body 字段不是数组: {type(body_data['body'])}")
                        raise BusinessException("请求体格式错误：body 字段必须是数组", code=ErrorCode.VALIDATION_ERROR)
                else:
                    logger.warning(f"字典中没有找到 resource_ids、json 或 body 字段，keys: {list(body_data.keys())}")
                    raise BusinessException("请求体格式错误：缺少 resource_ids 字段", code=ErrorCode.VALIDATION_ERROR)
            else:
                logger.warning(f"未知的数据类型: {type(body_data)}")
                raise BusinessException("请求体格式错误", code=ErrorCode.VALIDATION_ERROR)
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            logger.error(f"原始请求体为空，可能是前端未发送数据")
            raise BusinessException("请求体为空或格式错误，请检查前端是否正确发送数据", code=ErrorCode.VALIDATION_ERROR)
        except Exception as e:
            logger.error(f"解析请求体失败: {e}", exc_info=True)
            raise BusinessException(f"请求体解析失败: {str(e)}", code=ErrorCode.VALIDATION_ERROR)
        
        logger.info(f"最终 resource_ids: {resource_ids}, 类型: {type(resource_ids)}")
        
        if not resource_ids:
            logger.warning("resource_ids 为空")
            raise BusinessException("资源ID列表不能为空", code=ErrorCode.VALIDATION_ERROR)
        
        if not isinstance(resource_ids, list):
            logger.warning(f"resource_ids 不是列表类型: {type(resource_ids)}")
            raise BusinessException("资源ID列表格式错误", code=ErrorCode.VALIDATION_ERROR)
        
        permission_service.assign_resources_to_permission(permission_id, resource_ids)
        logger.info(f"成功为权限 {permission_id} 分配 {len(resource_ids)} 个资源")
        logger.info("=" * 80)
        return ApiResponse.success({}, message="分配资源成功")
    except BusinessException:
        raise
    except Exception as e:
        logger.error(f"分配资源失败: {str(e)}", exc_info=True)
        logger.info("=" * 80)
        raise _handle_unexpected_error("分配资源失败", e)

@router.post("/{permission_id}/resources/unassign", response_model=ApiResponse[dict])
async def unassign_resources_from_permission(
    permission_id: str,
    request: Request,
    current_user: User = Depends(require_role("admin")),
    permission_service: PermissionService = Depends(get_permission_service)
) -> ApiResponse[dict]:
    """从权限移除资源"""
    try:
        # 详细的调试日志
        logger.info("=" * 80)
        logger.info(f"移除资源请求开始 - permission_id: {permission_id}")
        logger.info(f"请求方法: {request.method}")
        logger.info(f"请求URL: {request.url}")
        logger.info(f"请求头:")
        for key, value in request.headers.items():
            logger.info(f"  {key}: {value}")
        
        # 读取原始请求体
        try:
            body_bytes = await request.body()
            logger.info(f"原始请求体 (bytes): {body_bytes}")
            logger.info(f"原始请求体长度: {len(body_bytes)}")
            
            if body_bytes:
                import json
                try:
                    body_json = json.loads(body_bytes.decode('utf-8'))
                    logger.info(f"解析后的请求体 (JSON): {body_json}")
                    logger.info(f"解析后的请求体类型: {type(body_json)}")
                except json.JSONDecodeError as e:
                    logger.error(f"JSON解析失败: {e}")
                    logger.error(f"原始内容: {body_bytes.decode('utf-8', errors='ignore')}")
            else:
                logger.warning("请求体为空!")
        except Exception as e:
            logger.error(f"读取请求体失败: {e}", exc_info=True)
        
        # 尝试从请求中获取 JSON 数据
        try:
            body_data = await request.json()
            logger.info(f"从 request.json() 获取的数据: {body_data}")
            logger.info(f"数据类型: {type(body_data)}")
            
            # 处理不同的数据格式
            if isinstance(body_data, list):
                resource_ids = body_data
                logger.info(f"请求体是数组，直接使用: {resource_ids}")
            elif isinstance(body_data, dict):
                if 'resource_ids' in body_data:
                    resource_ids = body_data['resource_ids']
                    logger.info(f"从字典中提取 resource_ids: {resource_ids}")
                elif 'json' in body_data:
                    resource_ids = body_data['json']
                    logger.info(f"从 json 字段中提取: {resource_ids}")
                elif 'body' in body_data:
                    # 如果 body 字段是数组，直接使用
                    if isinstance(body_data['body'], list):
                        resource_ids = body_data['body']
                        logger.info(f"从 body 字段中提取数组: {resource_ids}")
                    else:
                        logger.warning(f"body 字段不是数组: {type(body_data['body'])}")
                        raise BusinessException("请求体格式错误：body 字段必须是数组", code=ErrorCode.VALIDATION_ERROR)
                else:
                    logger.warning(f"字典中没有找到 resource_ids、json 或 body 字段，keys: {list(body_data.keys())}")
                    raise BusinessException("请求体格式错误：缺少 resource_ids 字段", code=ErrorCode.VALIDATION_ERROR)
            else:
                logger.warning(f"未知的数据类型: {type(body_data)}")
                raise BusinessException("请求体格式错误", code=ErrorCode.VALIDATION_ERROR)
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            logger.error(f"原始请求体为空，可能是前端未发送数据")
            raise BusinessException("请求体为空或格式错误，请检查前端是否正确发送数据", code=ErrorCode.VALIDATION_ERROR)
        except Exception as e:
            logger.error(f"解析请求体失败: {e}", exc_info=True)
            raise BusinessException(f"请求体解析失败: {str(e)}", code=ErrorCode.VALIDATION_ERROR)
        
        logger.info(f"最终 resource_ids: {resource_ids}, 类型: {type(resource_ids)}")
        
        if not resource_ids:
            logger.warning("resource_ids 为空")
            raise BusinessException("资源ID列表不能为空", code=ErrorCode.VALIDATION_ERROR)
        
        if not isinstance(resource_ids, list):
            logger.warning(f"resource_ids 不是列表类型: {type(resource_ids)}")
            raise BusinessException("资源ID列表格式错误", code=ErrorCode.VALIDATION_ERROR)
        
        permission_service.unassign_resources_from_permission(permission_id, resource_ids)
        logger.info(f"成功从权限 {permission_id} 移除 {len(resource_ids)} 个资源")
        logger.info("=" * 80)
        return ApiResponse.success({}, message="移除资源成功")
    except BusinessException:
        raise
    except Exception as e:
        logger.error(f"移除资源失败: {str(e)}", exc_info=True)
        logger.info("=" * 80)
        raise _handle_unexpected_error("移除资源失败", e)

