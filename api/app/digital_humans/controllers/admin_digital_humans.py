"""
管理员端数字人管理API端点

遵循 docs/API_ERROR_HANDLING_STANDARD.md：
- 使用 ApiResponse 统一响应格式
- 使用 BusinessException/SystemException + ErrorCode 统一错误处理
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.api import ApiResponse, BusinessException, ErrorCode, SystemException
from app.common.deps import get_db
from app.digital_humans.schemas.digital_human import (
    AdminDigitalHumanResponse,
    AdminCreateDigitalHumanRequest,
    AdminUpdateDigitalHumanRequest,
    UpdateDigitalHumanStatusRequest,
)
from app.identity_access.deps import get_current_admin
from app.identity_access.models.user import User
from ..deps.digital_humans import get_digital_human_service
from ..services.digital_human_service import DigitalHumanService

logger = logging.getLogger(__name__)
router = APIRouter()


def _handle_unexpected_error(message: str, exc: Exception) -> SystemException:
    logger.error(f"{message}: {exc}", exc_info=True)
    return SystemException(message=message, code=ErrorCode.SYSTEM_ERROR)


@router.get("/", response_model=ApiResponse[List[AdminDigitalHumanResponse]])
async def get_all_digital_humans(
    status: Optional[str] = Query(None, description="状态筛选"),
    type: Optional[str] = Query(None, description="类型筛选"),
    user_id: Optional[str] = Query(None, description="用户ID筛选"),
    is_system_created: Optional[bool] = Query(None, description="是否系统创建筛选"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    current_user: User = Depends(get_current_admin),
    service: DigitalHumanService = Depends(get_digital_human_service),
) -> ApiResponse[List[AdminDigitalHumanResponse]]:
    """获取所有数字人列表（管理员专用）"""
    try:
        digital_humans = service.get_all_digital_humans(
            status=status,
            type=type,
            user_id=user_id,
            is_system_created=is_system_created,
            search=search,
        )

        return ApiResponse.success(digital_humans, message="获取数字人列表成功")
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("管理员获取数字人列表失败", e)


@router.post(
    "/",
    response_model=ApiResponse[AdminDigitalHumanResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_digital_human_admin(
    data: AdminCreateDigitalHumanRequest,
    current_user: User = Depends(get_current_admin),
    service: DigitalHumanService = Depends(get_digital_human_service),
) -> ApiResponse[AdminDigitalHumanResponse]:
    """创建数字人（管理员专用，可创建系统助手并分配所属用户）"""
    try:
        digital_human = service.create_digital_human_admin(data)
        return ApiResponse.success(digital_human, message="创建数字人成功")
    except ValueError as e:
        raise BusinessException(
            str(e),
            code=ErrorCode.VALIDATION_ERROR,
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("管理员创建数字人失败", e)


@router.get(
    "/{digital_human_id}",
    response_model=ApiResponse[AdminDigitalHumanResponse],
)
async def get_digital_human_detail(
    digital_human_id: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> ApiResponse[AdminDigitalHumanResponse]:
    """获取数字人详情（管理员专用）"""
    try:
        service = DigitalHumanService(db)
        digital_human = service.get_digital_human_by_id(digital_human_id)  # 管理员可查看所有数字人

        if not digital_human:
            raise BusinessException(
                "数字人不存在",
                code=ErrorCode.NOT_FOUND,
                status_code=status.HTTP_404_NOT_FOUND,
            )

        return ApiResponse.success(digital_human, message="获取数字人详情成功")
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("管理员获取数字人详情失败", e)


@router.put(
    "/{digital_human_id}",
    response_model=ApiResponse[AdminDigitalHumanResponse],
)
async def update_digital_human_admin(
    digital_human_id: str,
    data: AdminUpdateDigitalHumanRequest,
    current_user: User = Depends(get_current_admin),
    service: DigitalHumanService = Depends(get_digital_human_service),
) -> ApiResponse[AdminDigitalHumanResponse]:
    """更新数字人（管理员专用，可调整所属用户）"""
    try:
        digital_human = service.update_digital_human_admin(digital_human_id, data)
        if not digital_human:
            raise BusinessException(
                "数字人不存在",
                code=ErrorCode.NOT_FOUND,
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return ApiResponse.success(digital_human, message="更新数字人成功")
    except ValueError as e:
        raise BusinessException(
            str(e),
            code=ErrorCode.VALIDATION_ERROR,
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("管理员更新数字人失败", e)


@router.put(
    "/{digital_human_id}/status",
    response_model=ApiResponse[AdminDigitalHumanResponse],
)
async def update_digital_human_status(
    digital_human_id: str,
    data: UpdateDigitalHumanStatusRequest,
    current_user: User = Depends(get_current_admin),
    service: DigitalHumanService = Depends(get_digital_human_service),
) -> ApiResponse[AdminDigitalHumanResponse]:
    """更新数字人状态（管理员专用）"""
    try:
        # 验证状态值
        valid_statuses = ["active", "inactive", "maintenance"]
        if data.status not in valid_statuses:
            raise BusinessException(
                f"无效的状态值，必须是: {', '.join(valid_statuses)}",
                code=ErrorCode.VALIDATION_ERROR,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        digital_human = service.update_digital_human_status(digital_human_id, data.status)

        if not digital_human:
            raise BusinessException(
                "数字人不存在",
                code=ErrorCode.NOT_FOUND,
                status_code=status.HTTP_404_NOT_FOUND,
            )

        return ApiResponse.success(digital_human, message="更新数字人状态成功")
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("管理员更新数字人状态失败", e)


@router.delete(
    "/{digital_human_id}",
    response_model=ApiResponse[None],
)
async def delete_digital_human_admin(
    digital_human_id: str,
    current_user: User = Depends(get_current_admin),
    service: DigitalHumanService = Depends(get_digital_human_service),
) -> ApiResponse[None]:
    """删除数字人（管理员专用，允许删除系统创建数字人）"""
    try:
        success = service.delete_digital_human_admin(digital_human_id)
        if not success:
            raise BusinessException(
                "数字人不存在",
                code=ErrorCode.NOT_FOUND,
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return ApiResponse.success(message="删除数字人成功")
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("管理员删除数字人失败", e)


@router.post(
    "/batch",
    response_model=ApiResponse[dict],
    status_code=status.HTTP_200_OK,
)
async def batch_update_digital_humans(
    digital_human_ids: List[str],
    action: str,
    data: Optional[dict] = None,
    current_user: User = Depends(get_current_admin),
    service: DigitalHumanService = Depends(get_digital_human_service),
) -> ApiResponse[dict]:
    """批量操作数字人（管理员专用）"""
    try:
        if action == "update_status":
            if not data or "status" not in data:
                raise BusinessException(
                    "批量更新状态需要提供status参数",
                    code=ErrorCode.VALIDATION_ERROR,
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            results: list[dict] = []
            for dh_id in digital_human_ids:
                try:
                    result = service.update_digital_human_status(dh_id, data["status"])
                    if result:
                        results.append({"id": dh_id, "success": True})
                    else:
                        results.append({"id": dh_id, "success": False, "error": "数字人不存在"})
                except Exception as e:  # 单条失败不影响整体
                    logger.error(f"批量更新数字人状态失败: id={dh_id}, error={e}")
                    results.append({"id": dh_id, "success": False, "error": str(e)})

            return ApiResponse.success({"results": results}, message="批量操作完成")

        raise BusinessException(
            f"不支持的批量操作: {action}",
            code=ErrorCode.BUSINESS_ERROR,
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("批量操作数字人失败", e)
