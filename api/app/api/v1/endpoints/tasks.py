"""
待办任务管理API端点
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.db.models.user import User
from app.schemas.task import (
    TaskResponse,
    CreateTaskRequest,
    UpdateTaskRequest,
    ClaimTaskRequest
)
from app.services.task_service import TaskService

logger = logging.getLogger(__name__)
router = APIRouter()


def get_user_role(user: User) -> str:
    """获取用户角色"""
    if hasattr(user, '_active_role') and user._active_role:
        return user._active_role
    elif user.roles:
        return user.roles[0].name
    return 'customer'


@router.get("/")
async def get_tasks(
    status: Optional[str] = Query(None, description="状态筛选"),
    task_type: Optional[str] = Query(None, description="任务类型筛选"),
    priority: Optional[str] = Query(None, description="优先级筛选"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    user_role: Optional[str] = Query(None, description="用户角色（用于筛选）"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取待办任务列表"""
    try:
        # 获取用户角色
        actual_user_role = user_role or get_user_role(current_user)
        
        service = TaskService(db)
        tasks = service.get_tasks_for_user(
            user_id=current_user.id,
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
        
    except Exception as e:
        logger.error(f"获取任务列表失败: {e}")
        return {
            "success": False,
            "data": [],
            "message": f"获取任务列表失败: {str(e)}"
        }


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取任务详情"""
    try:
        user_role = get_user_role(current_user)
        service = TaskService(db)
        task = service.get_task_by_id(task_id, current_user.id, user_role)
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务不存在或无权限访问"
            )
        
        return task
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取任务详情失败"
        )


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    data: CreateTaskRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建待办任务"""
    try:
        service = TaskService(db)
        task = service.create_task(current_user.id, data)
        
        return task
        
    except Exception as e:
        logger.error(f"创建任务失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建任务失败: {str(e)}"
        )


@router.post("/{task_id}/claim", response_model=TaskResponse)
async def claim_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """认领任务"""
    try:
        service = TaskService(db)
        task = service.claim_task(task_id, current_user.id)
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务不存在或已被认领"
            )
        
        return task
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"认领任务失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"认领任务失败: {str(e)}"
        )


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    data: UpdateTaskRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新任务状态"""
    try:
        user_role = get_user_role(current_user)
        service = TaskService(db)
        task = service.update_task_status(task_id, current_user.id, user_role, data)
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务不存在或无权限修改"
            )
        
        return task
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新任务失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新任务失败: {str(e)}"
        )
