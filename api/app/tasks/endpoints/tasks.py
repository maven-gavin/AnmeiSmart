"""
待办任务管理API端点
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.common.deps import get_db
from app.identity_access.deps import get_current_user, get_user_primary_role
from app.identity_access.infrastructure.db.user import User
from app.tasks.schemas.task import (
    TaskResponse,
    CreateTaskRequest,
    UpdateTaskRequest,
)
from app.tasks.application.task_application_service import TaskApplicationService
from app.tasks.deps.tasks import get_task_application_service

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
    task_app_service: TaskApplicationService = Depends(get_task_application_service),
    db: Session = Depends(get_db)
):
    """获取待办任务列表 - 表现层只负责请求路由和响应格式化"""
    try:
        logger.info(f"开始获取任务列表 - 用户ID: {current_user.id}, 请求参数: status={status}, task_type={task_type}, priority={priority}, search={search}, user_role={user_role}")
        
        # 获取用户角色
        actual_user_role = user_role or get_user_primary_role(current_user)
        logger.info(f"确定用户角色: {actual_user_role}")
        
        # 调用应用服务用例
        logger.info(f"调用应用服务获取任务列表")
        tasks = task_app_service.get_tasks_for_user_use_case(
            user_id=str(current_user.id),
            user_role=actual_user_role,
            status=status,
            task_type=task_type,
            priority=priority,
            search=search,
            db=db
        )
        
        logger.info(f"成功获取任务列表，共 {len(tasks)} 个任务")
        return {
            "success": True,
            "data": tasks,
            "message": "获取任务列表成功"
        }
        
    except ValueError as e:
        # 业务逻辑错误 - 400 Bad Request
        logger.error(f"获取任务列表业务逻辑错误: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # 系统错误 - 500 Internal Server Error
        logger.error(f"获取任务列表失败: {e}")
        import traceback
        logger.error(f"详细错误堆栈: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="获取任务列表失败")


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    task_app_service: TaskApplicationService = Depends(get_task_application_service),
    db: Session = Depends(get_db)
):
    """获取任务详情 - 表现层只负责请求路由和响应格式化"""
    try:
        user_role = get_user_primary_role(current_user)
        
        # 调用应用服务用例
        task = task_app_service.get_task_by_id_use_case(
            task_id=task_id,
            user_id=str(current_user.id),
            user_role=user_role,
            db=db
        )
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务不存在或无权限访问"
            )
        
        return task
        
    except HTTPException:
        raise
    except ValueError as e:
        # 业务逻辑错误 - 400 Bad Request
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # 系统错误 - 500 Internal Server Error
        logger.error(f"获取任务详情失败: {e}")
        raise HTTPException(status_code=500, detail="获取任务详情失败")


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    data: CreateTaskRequest,
    current_user: User = Depends(get_current_user),
    task_app_service: TaskApplicationService = Depends(get_task_application_service),
    db: Session = Depends(get_db)
):
    """创建待办任务 - 表现层只负责请求路由和响应格式化"""
    try:
        # 调用应用服务用例
        task = task_app_service.create_task_use_case(
            user_id=str(current_user.id),
            data=data,
            db=db
        )
        
        return task
        
    except ValueError as e:
        # 业务逻辑错误 - 400 Bad Request
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # 系统错误 - 500 Internal Server Error
        logger.error(f"创建任务失败: {e}")
        raise HTTPException(status_code=500, detail="创建任务失败")


@router.post("/{task_id}/claim", response_model=TaskResponse)
async def claim_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    task_app_service: TaskApplicationService = Depends(get_task_application_service),
    db: Session = Depends(get_db)
):
    """认领任务 - 表现层只负责请求路由和响应格式化"""
    try:
        # 调用应用服务用例
        task = task_app_service.claim_task_use_case(
            task_id=task_id,
            user_id=str(current_user.id),
            db=db
        )
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务不存在或已被认领"
            )
        
        return task
        
    except HTTPException:
        raise
    except ValueError as e:
        # 业务逻辑错误 - 400 Bad Request
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # 系统错误 - 500 Internal Server Error
        logger.error(f"认领任务失败: {e}")
        raise HTTPException(status_code=500, detail="认领任务失败")


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    data: UpdateTaskRequest,
    current_user: User = Depends(get_current_user),
    task_app_service: TaskApplicationService = Depends(get_task_application_service),
    db: Session = Depends(get_db)
):
    """更新任务状态 - 表现层只负责请求路由和响应格式化"""
    try:
        user_role = get_user_primary_role(current_user)
        
        # 调用应用服务用例
        task = task_app_service.update_task_status_use_case(
            task_id=task_id,
            user_id=str(current_user.id),
            user_role=user_role,
            data=data,
            db=db
        )
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务不存在或无权限修改"
            )
        
        return task
        
    except HTTPException:
        raise
    except ValueError as e:
        # 业务逻辑错误 - 400 Bad Request
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # 系统错误 - 500 Internal Server Error
        logger.error(f"更新任务失败: {e}")
        raise HTTPException(status_code=500, detail="更新任务失败")
