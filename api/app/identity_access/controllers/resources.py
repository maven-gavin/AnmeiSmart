"""
资源管理控制器
"""
from fastapi import APIRouter, Depends, status
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.common.deps import get_db
from app.identity_access.models.user import User
from app.identity_access.services.resource_service import ResourceService
from app.identity_access.services.resource_sync_service import ResourceSyncService
from app.identity_access.schemas.resource_schemas import SyncMenusRequest, SyncMenusResponse
from app.identity_access.deps.auth_deps import get_current_user, require_role
from app.core.api import ApiResponse, BusinessException, ErrorCode, SystemException

router = APIRouter()

def _handle_unexpected_error(message: str, exc: Exception) -> SystemException:
    return SystemException(message=message, code=ErrorCode.SYSTEM_ERROR)

@router.post("/sync-menus", response_model=ApiResponse[SyncMenusResponse])
async def sync_menus(
    request: SyncMenusRequest,
    current_user: User = Depends(require_role("administrator")),
    db: Session = Depends(get_db)
) -> ApiResponse[SyncMenusResponse]:
    """
    同步菜单资源到资源库
    需要管理员权限
    """
    try:
        resource_service = ResourceService(db)
        resource_sync_service = ResourceSyncService(resource_service)
        
        result = await resource_sync_service.sync_menu_resources(request.menus)
        
        response = SyncMenusResponse(
            synced_count=result["synced_count"],
            created_count=result["created_count"],
            updated_count=result["updated_count"]
        )
        
        return ApiResponse.success(response, message="菜单资源同步成功")
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("同步菜单资源失败", e)

