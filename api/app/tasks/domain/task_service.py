"""
待办任务服务 - 处理任务相关的业务逻辑
"""
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime

from app.tasks.infrastructure.db.task import PendingTask, User
from app.common.infrastructure.db.uuid_utils import task_id
from app.tasks.schemas.task import (
    CreateTaskRequest,
    UpdateTaskRequest,
    TaskResponse
)

logger = logging.getLogger(__name__)


class TaskService:
    """待办任务服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_tasks_for_user(self, 
                          user_id: str, 
                          user_role: str,
                          status: Optional[str] = None,
                          task_type: Optional[str] = None,
                          priority: Optional[str] = None,
                          search: Optional[str] = None) -> List[TaskResponse]:
        """根据用户角色获取相关任务"""
        try:
            query = self.db.query(PendingTask)
            
            # 根据用户角色筛选任务
            if user_role == "admin":
                # 管理员可以看到所有任务
                pass
            elif user_role == "consultant":
                # 顾问可以看到：1. 分配给自己的任务 2. 新用户接待类任务
                query = query.filter(
                    or_(
                        PendingTask.assigned_to == user_id,
                        and_(
                            PendingTask.task_type.in_(['new_user_reception', 'consultation_upgrade']),
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
                            PendingTask.task_type.in_(['prescription_review', 'medical_consultation']),
                            PendingTask.status == 'pending'
                        )
                    )
                )
            elif user_role == "operator":
                # 运营人员可以看到：1. 分配给自己的任务 2. 运营相关任务
                query = query.filter(
                    or_(
                        PendingTask.assigned_to == user_id,
                        and_(
                            PendingTask.task_type.in_(['system_maintenance', 'user_feedback']),
                            PendingTask.status == 'pending'
                        )
                    )
                )
            else:
                # 其他角色只能看到分配给自己的任务
                query = query.filter(PendingTask.assigned_to == user_id)
            
            # 应用其他筛选条件
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
            
            return [TaskResponse.from_model(task) for task in tasks]
            
        except Exception as e:
            logger.error(f"获取用户任务列表失败: {e}")
            raise
    
    def get_task_by_id(self, task_id: str, user_id: str, user_role: str) -> Optional[TaskResponse]:
        """获取任务详情"""
        try:
            query = self.db.query(PendingTask).filter(PendingTask.id == task_id)
            
            # 权限检查
            if user_role != "admin":
                # 非管理员只能查看分配给自己的任务或可认领的任务
                query = query.filter(
                    or_(
                        PendingTask.assigned_to == user_id,
                        and_(
                            PendingTask.status == 'pending',
                            PendingTask.assigned_to.is_(None)
                        )
                    )
                )
            
            task = query.first()
            
            if not task:
                return None
            
            return TaskResponse.from_model(task)
            
        except Exception as e:
            logger.error(f"获取任务详情失败: {e}")
            raise
    
    def create_task(self, user_id: str, data: CreateTaskRequest) -> TaskResponse:
        """创建待办任务"""
        try:
            task = PendingTask(
                id=task_id(),
                title=data.title,
                description=data.description,
                task_type=data.task_type,
                status="pending",
                priority=data.priority,
                created_by=user_id,
                assigned_to=data.assigned_to,
                assigned_at=datetime.utcnow() if data.assigned_to else None,
                related_object_type=data.related_object_type,
                related_object_id=data.related_object_id,
                task_data=data.task_data,
                due_date=data.due_date
            )
            
            self.db.add(task)
            self.db.commit()
            self.db.refresh(task)
            
            logger.info(f"创建任务成功: {task.title}")
            return TaskResponse.from_model(task)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建任务失败: {e}")
            raise
    
    def claim_task(self, task_id: str, user_id: str) -> Optional[TaskResponse]:
        """认领任务"""
        try:
            task = (
                self.db.query(PendingTask)
                .filter(and_(
                    PendingTask.id == task_id,
                    PendingTask.status == 'pending',
                    PendingTask.assigned_to.is_(None)
                ))
                .first()
            )
            
            if not task:
                return None
            
            task.assigned_to = user_id
            task.assigned_at = datetime.utcnow()
            task.status = 'assigned'
            task.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(task)
            
            logger.info(f"用户 {user_id} 认领任务: {task.title}")
            return TaskResponse.from_model(task)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"认领任务失败: {e}")
            raise
    
    def update_task_status(self, 
                          task_id: str, 
                          user_id: str, 
                          user_role: str,
                          data: UpdateTaskRequest) -> Optional[TaskResponse]:
        """更新任务状态"""
        try:
            query = self.db.query(PendingTask).filter(PendingTask.id == task_id)
            
            # 权限检查
            if user_role != "admin":
                # 非管理员只能更新分配给自己的任务
                query = query.filter(PendingTask.assigned_to == user_id)
            
            task = query.first()
            
            if not task:
                return None
            
            # 更新字段
            update_data = data.dict(exclude_unset=True)
            for field, value in update_data.items():
                if hasattr(task, field):
                    setattr(task, field, value)
            
            # 如果状态变为completed，设置完成时间
            if data.status == 'completed':
                task.completed_at = datetime.utcnow()
            
            task.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(task)
            
            logger.info(f"更新任务状态成功: {task.title} -> {task.status}")
            return TaskResponse.from_model(task)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新任务状态失败: {e}")
            raise
    
    def create_new_user_reception_task(self, user_id: str, username: str) -> TaskResponse:
        """为新用户创建接待任务"""
        try:
            task = PendingTask(
                id=task_id(),
                title=f"新用户接待：{username}",
                description=f"用户 {username} 刚刚注册，需要顾问主动联系提供咨询服务",
                task_type="new_user_reception",
                status="pending",
                priority="medium",
                created_by=None,  # 系统创建
                related_object_type="user",
                related_object_id=user_id,
                task_data={
                    "user_id": user_id,
                    "username": username,
                    "registration_time": datetime.utcnow().isoformat()
                }
            )
            
            self.db.add(task)
            self.db.commit()
            self.db.refresh(task)
            
            logger.info(f"为新用户 {username} 创建接待任务")
            return TaskResponse.from_model(task)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建新用户接待任务失败: {e}")
            raise
