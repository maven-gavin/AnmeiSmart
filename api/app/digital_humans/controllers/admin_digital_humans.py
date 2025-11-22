"""
管理员端数字人管理API端点
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.common.deps import get_db
from app.identity_access.deps import get_current_admin
from app.identity_access.models.user import User
from app.digital_humans.schemas.digital_human import (
    AdminDigitalHumanResponse,
    UpdateDigitalHumanStatusRequest
)
from ..deps.digital_humans import get_digital_human_service
from ..services.digital_human_service import DigitalHumanService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/")
async def get_all_digital_humans(
    status: Optional[str] = Query(None, description="状态筛选"),
    type: Optional[str] = Query(None, description="类型筛选"),
    user_id: Optional[str] = Query(None, description="用户ID筛选"),
    is_system_created: Optional[bool] = Query(None, description="是否系统创建筛选"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    current_user: User = Depends(get_current_admin),
    service: DigitalHumanService = Depends(get_digital_human_service)
):
    """获取所有数字人列表（管理员专用）"""
    try:
        digital_humans = service.get_all_digital_humans(
            status=status,
            type=type,
            user_id=user_id,
            is_system_created=is_system_created,
            search=search
        )
        
        return {
            "success": True,
            "data": digital_humans,
            "message": "获取数字人列表成功"
        }
        
    except Exception as e:
        logger.error(f"管理员获取数字人列表失败: {e}")
        return {
            "success": False,
            "data": [],
            "message": f"获取数字人列表失败: {str(e)}"
        }


@router.get("/{digital_human_id}", response_model=AdminDigitalHumanResponse)
async def get_digital_human_detail(
    digital_human_id: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """获取数字人详情（管理员专用）"""
    try:
        service = DigitalHumanService(db)
        digital_human = service.get_digital_human_by_id(digital_human_id)  # 管理员可查看所有数字人
        
        if not digital_human:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="数字人不存在"
            )
        
        return digital_human
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"管理员获取数字人详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取数字人详情失败"
        )


@router.put("/{digital_human_id}/status", response_model=AdminDigitalHumanResponse)
async def update_digital_human_status(
    digital_human_id: str,
    data: UpdateDigitalHumanStatusRequest,
    current_user: User = Depends(get_current_admin),
    service: DigitalHumanService = Depends(get_digital_human_service)
):
    """更新数字人状态（管理员专用）"""
    try:
        # 验证状态值
        valid_statuses = ['active', 'inactive', 'maintenance']
        if data.status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的状态值，必须是: {', '.join(valid_statuses)}"
            )
        digital_human = service.update_digital_human_status(digital_human_id, data.status)
        
        if not digital_human:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="数字人不存在"
            )
        
        return digital_human
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"管理员更新数字人状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新数字人状态失败: {str(e)}"
        )


@router.post("/batch", status_code=status.HTTP_200_OK)
async def batch_update_digital_humans(
    digital_human_ids: List[str],
    action: str,
    data: Optional[dict] = None,
    current_user: User = Depends(get_current_admin),
    service: DigitalHumanService = Depends(get_digital_human_service)
):
    """批量操作数字人（管理员专用）"""
    try:
        
        if action == "update_status":
            if not data or "status" not in data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="批量更新状态需要提供status参数"
                )
            
            results = []
            for dh_id in digital_human_ids:
                try:
                    result = service.update_digital_human_status(dh_id, data["status"])
                    if result:
                        results.append({"id": dh_id, "success": True})
                    else:
                        results.append({"id": dh_id, "success": False, "error": "数字人不存在"})
                except Exception as e:
                    results.append({"id": dh_id, "success": False, "error": str(e)})
            
            return {"results": results}
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的批量操作: {action}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量操作数字人失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量操作失败: {str(e)}"
        )
