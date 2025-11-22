"""
待办任务管理API端点
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.common.deps import get_db
from app.identity_access.deps import get_current_user, get_user_primary_role
from app.identity_access.models.user import User
from app.tasks.schemas.task import (
    TaskResponse,
    CreateTaskRequest,
    UpdateTaskRequest,
)
from app.tasks.deps.tasks import get_task_service
from app.tasks.services.task_service import TaskService
from app.core.api import BusinessException, ErrorCode

logger = logging.getLogger(__name__)
router = APIRouter()


# 移除本地定义的函数，使用公共方法 get_user_primary_role


@router.get("/")
async def get_tasks(
    status: Optional[str] = Query(None, description="状态筛选"),
    task_type: Optional[str] = Query(None, description="任务类型筛选"),
    priority: Optional[str] = Query(None, description="优先级筛选"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    user_role: Optional[str] = Query(None, description="用户角色（用于筛选）"),
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service)
):
    """获取待办任务列表"""
    try:
        # 获取用户角色
        actual_user_role = user_role or get_user_primary_role(current_user)
        
        # 调用服务
        tasks = task_service.get_tasks_for_user(
            user_id=str(current_user.id),
            user_role=actual_user_role,
            status=status,
            task_type=task_type,
            priority=priority,
            search=search
        )
        
        return {
            "success": True,
            "data": tasks,
            "message": "获取任务列表成功"
        }
        
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"获取任务列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取任务列表失败")


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service)
):
    """获取任务详情"""
    try:
        user_role = get_user_primary_role(current_user)
        
        # 调用服务
        task = task_service.get_task_by_id(
            task_id=task_id,
            user_id=str(current_user.id),
            user_role=user_role
        )
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务不存在或无权限访问"
            )
        
        return task
        
    except HTTPException:
        raise
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"获取任务详情失败: {e}")
        raise HTTPException(status_code=500, detail="获取任务详情失败")


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    data: CreateTaskRequest,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service)
):
    """创建待办任务"""
    try:
        # 调用服务
        task = task_service.create_task(
            user_id=str(current_user.id),
            task_data=data
        )
        
        return task
        
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建任务失败: {e}")
        raise HTTPException(status_code=500, detail="创建任务失败")


@router.post("/{task_id}/claim", response_model=TaskResponse)
async def claim_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service)
):
    """认领任务"""
    try:
        # 调用服务
        task = task_service.claim_task(
            task_id=task_id,
            user_id=str(current_user.id)
        )
        
        return task
        
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"认领任务失败: {e}")
        raise HTTPException(status_code=500, detail="认领任务失败")


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    data: UpdateTaskRequest,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service)
):
    """更新任务状态"""
    try:
        user_role = get_user_primary_role(current_user)
        
        # 调用服务
        task = task_service.update_task(
            task_id=task_id,
            user_id=str(current_user.id),
            user_role=user_role,
            task_data=data
        )
        
        return task
        
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"更新任务失败: {e}")
        raise HTTPException(status_code=500, detail="更新任务失败")
