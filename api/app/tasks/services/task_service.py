"""
任务服务 - 核心业务逻辑
处理任务CRUD、任务状态管理等功能
"""

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
from datetime import datetime

from app.tasks.models.task import PendingTask
from app.tasks.schemas.task import (
    TaskResponse, CreateTaskRequest, UpdateTaskRequest, UserInfo
)
from app.common.deps.uuid_utils import task_id
from app.core.api import BusinessException, ErrorCode

logger = logging.getLogger(__name__)


class TaskService:
    """任务服务 - 直接操作数据库模型"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_tasks_for_user(
        self,
        user_id: str,
        user_role: str,
        status: Optional[str] = None,
        task_type: Optional[str] = None,
        priority: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[TaskResponse]:
        """获取用户相关任务列表"""
        query = self.db.query(PendingTask).options(
            joinedload(PendingTask.created_by_user),
            joinedload(PendingTask.assigned_to_user)
        )
        
        # 根据用户角色筛选任务
        if user_role == "administrator":
            # 管理员可以看到所有任务
            pass
        elif user_role == "consultant":
            # 顾问可以看到：1. 分配给自己的任务 2. 新用户接待类任务
            query = query.filter(
                or_(
                    PendingTask.assigned_to == user_id,
                    and_(
                        PendingTask.task_type.in_(['new_user_reception']),
                        PendingTask.status == 'pending'
                    )
                )
            )
        elif user_role == "doctor":
            # 医生可以看到：1. 分配给自己的任务 2. 医疗相关任务
            query = query.filter(
                or_(
                    PendingTask.assigned_to == user_id,
                    and_(
                        PendingTask.task_type.in_(['prescription_review']),
                        PendingTask.status == 'pending'
                    )
                )
            )
        else:
            # 其他角色只能看到分配给自己的任务
            query = query.filter(PendingTask.assigned_to == user_id)
        
        # 应用筛选条件
        if status:
            query = query.filter(PendingTask.status == status)
        if task_type:
            query = query.filter(PendingTask.task_type == task_type)
        if priority:
            query = query.filter(PendingTask.priority == priority)
        if search:
            query = query.filter(
                or_(
                    PendingTask.title.contains(search),
                    PendingTask.description.contains(search)
                )
            )
        
        tasks = query.order_by(
            PendingTask.priority.desc(),
            PendingTask.created_at.desc()
        ).all()
        
        # 转换为响应模型
        return [self._to_response(task) for task in tasks]
    
    def get_task_by_id(
        self,
        task_id: str,
        user_id: str,
        user_role: str
    ) -> Optional[TaskResponse]:
        """获取任务详情"""
        task = self.db.query(PendingTask).options(
            joinedload(PendingTask.created_by_user),
            joinedload(PendingTask.assigned_to_user)
        ).filter(PendingTask.id == task_id).first()
        
        if not task:
            return None
        
        # 权限检查
        if user_role != "administrator":
            if task.assigned_to != user_id and not (task.status == "pending" and not task.assigned_to):
                return None
        
        return self._to_response(task)
    
    def create_task(
        self,
        user_id: str,
        task_data: CreateTaskRequest
    ) -> TaskResponse:
        """创建任务"""
        # 验证任务标题
        if not task_data.title or not task_data.title.strip():
            raise BusinessException("任务标题不能为空", code=ErrorCode.INVALID_INPUT)
        
        # 创建任务
        task = PendingTask(
            id=task_id(),
            title=task_data.title,
            description=task_data.description,
            task_type=task_data.task_type,
            priority=task_data.priority or "medium",
            due_date=task_data.due_date,
            related_object_type=task_data.related_object_type,
            related_object_id=task_data.related_object_id,
            task_data=task_data.task_data,
            created_by=user_id,
            assigned_to=task_data.assigned_to,
            status="assigned" if task_data.assigned_to else "pending"
        )
        
        if task_data.assigned_to:
            task.assigned_at = datetime.now()
        
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        
        # 重新加载关联数据
        task = self.db.query(PendingTask).options(
            joinedload(PendingTask.created_by_user),
            joinedload(PendingTask.assigned_to_user)
        ).filter(PendingTask.id == task.id).first()
        
        return self._to_response(task)
    
    def claim_task(self, task_id: str, user_id: str) -> TaskResponse:
        """认领任务"""
        task = self.db.query(PendingTask).filter(PendingTask.id == task_id).first()
        
        if not task:
            raise BusinessException("任务不存在", code=ErrorCode.RESOURCE_NOT_FOUND)
        
        if task.status != "pending":
            raise BusinessException("任务状态不允许认领", code=ErrorCode.INVALID_OPERATION)
        
        if task.assigned_to:
            raise BusinessException("任务已被分配", code=ErrorCode.INVALID_OPERATION)
        
        # 认领任务
        task.assigned_to = user_id
        task.assigned_at = datetime.now()
        task.status = "assigned"
        
        self.db.commit()
        self.db.refresh(task)
        
        # 重新加载关联数据
        task = self.db.query(PendingTask).options(
            joinedload(PendingTask.created_by_user),
            joinedload(PendingTask.assigned_to_user)
        ).filter(PendingTask.id == task.id).first()
        
        return self._to_response(task)
    
    def update_task(
        self,
        task_id: str,
        user_id: str,
        user_role: str,
        task_data: UpdateTaskRequest
    ) -> TaskResponse:
        """更新任务"""
        task = self.db.query(PendingTask).filter(PendingTask.id == task_id).first()
        
        if not task:
            raise BusinessException("任务不存在", code=ErrorCode.RESOURCE_NOT_FOUND)
        
        # 权限检查
        if user_role != "administrator":
            if task.assigned_to != user_id:
                raise BusinessException("无权修改此任务", code=ErrorCode.ACCESS_DENIED)
        
        # 根据状态更新
        if task_data.status == "completed":
            task.status = "completed"
            task.completed_at = datetime.now()
        elif task_data.status == "cancelled":
            task.status = "cancelled"
        elif task_data.status == "in_progress":
            task.status = "in_progress"
        
        # 更新其他字段
        if task_data.title is not None:
            task.title = task_data.title
        if task_data.description is not None:
            task.description = task_data.description
        if task_data.priority is not None:
            task.priority = task_data.priority
        if task_data.notes is not None:
            task.notes = task_data.notes
        if task_data.result is not None:
            task.result = task_data.result
        
        self.db.commit()
        self.db.refresh(task)
        
        # 重新加载关联数据
        task = self.db.query(PendingTask).options(
            joinedload(PendingTask.created_by_user),
            joinedload(PendingTask.assigned_to_user)
        ).filter(PendingTask.id == task.id).first()
        
        return self._to_response(task)
    
    def create_new_user_reception_task(self, user_id: str, username: str) -> TaskResponse:
        """创建新用户接待任务"""
        task = PendingTask(
            id=task_id(),
            title=f"新用户接待：{username}",
            description=f"为新注册用户 {username} 创建接待任务，请及时联系并提供服务",
            task_type="new_user_reception",
            priority="high",
            status="pending",
            related_object_type="user",
            related_object_id=user_id,
            task_data={"username": username, "user_id": user_id}
        )
        
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        
        # 重新加载关联数据
        task = self.db.query(PendingTask).options(
            joinedload(PendingTask.created_by_user),
            joinedload(PendingTask.assigned_to_user)
        ).filter(PendingTask.id == task.id).first()
        
        return self._to_response(task)
    
    def _to_response(self, task: PendingTask) -> TaskResponse:
        """转换任务模型为响应模型"""
        return TaskResponse(
            id=task.id,
            title=task.title,
            description=task.description,
            task_type=task.task_type,
            status=task.status,
            priority=task.priority,
            due_date=task.due_date,
            created_by=UserInfo(
                id=task.created_by_user.id,
                username=task.created_by_user.username,
                email=task.created_by_user.email
            ) if task.created_by_user else None,
            assigned_to=UserInfo(
                id=task.assigned_to_user.id,
                username=task.assigned_to_user.username,
                email=task.assigned_to_user.email
            ) if task.assigned_to_user else None,
            assigned_at=task.assigned_at,
            related_object_type=task.related_object_type,
            related_object_id=task.related_object_id,
            task_data=task.task_data,
            completed_at=task.completed_at,
            result=task.result,
            notes=task.notes,
            created_at=task.created_at,
            updated_at=task.updated_at
        )

