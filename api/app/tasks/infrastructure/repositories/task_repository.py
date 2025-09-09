"""
任务仓储实现
"""
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.tasks.domain.interfaces import ITaskRepository
from app.tasks.domain.entities.task import Task
from app.tasks.infrastructure.db.task import PendingTask
from app.tasks.converters.task_converter import TaskConverter

logger = logging.getLogger(__name__)


class TaskRepository(ITaskRepository):
    """任务仓储实现"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def save(self, task: Task) -> Task:
        """保存任务"""
        try:
            # 检查任务是否已存在
            existing_task = self.db.query(PendingTask).filter(PendingTask.id == task.id).first()
            
            if existing_task:
                # 更新现有任务
                task_dict = TaskConverter.to_model_dict(task)
                for key, value in task_dict.items():
                    if key != 'id':  # 不更新ID
                        setattr(existing_task, key, value)
                updated_task = existing_task
            else:
                # 创建新任务
                task_dict = TaskConverter.to_model_dict(task)
                updated_task = PendingTask(**task_dict)
                self.db.add(updated_task)
            
            self.db.commit()
            self.db.refresh(updated_task)
            
            # 转换为领域实体
            return TaskConverter.from_model(updated_task)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"保存任务失败: {e}")
            raise
    
    def get_by_id(self, task_id: str) -> Optional[Task]:
        """根据ID获取任务"""
        try:
            task_model = self.db.query(PendingTask).filter(PendingTask.id == task_id).first()
            
            if not task_model:
                return None
            
            return TaskConverter.from_model(task_model)
            
        except Exception as e:
            logger.error(f"根据ID获取任务失败: {e}")
            raise
    
    def get_tasks_for_user(self, user_id: str, user_role: str, **filters) -> List[Task]:
        """获取用户相关任务"""
        try:
            query = self.db.query(PendingTask)
            
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
            if filters.get('status'):
                query = query.filter(PendingTask.status == filters['status'])
            
            if filters.get('task_type'):
                query = query.filter(PendingTask.task_type == filters['task_type'])
            
            if filters.get('priority'):
                query = query.filter(PendingTask.priority == filters['priority'])
            
            if filters.get('search'):
                search_term = filters['search']
                query = query.filter(
                    or_(
                        PendingTask.title.contains(search_term),
                        PendingTask.description.contains(search_term)
                    )
                )
            
            # 排序
            tasks = query.order_by(
                PendingTask.priority.desc(),
                PendingTask.created_at.desc()
            ).all()
            
            # 转换为领域实体
            return [TaskConverter.from_model(task) for task in tasks]
            
        except Exception as e:
            logger.error(f"获取用户任务列表失败: {e}")
            raise
    
    def get_claimable_tasks(self, user_role: str) -> List[Task]:
        """获取可认领的任务"""
        try:
            query = self.db.query(PendingTask).filter(
                and_(
                    PendingTask.status == 'pending',
                    PendingTask.assigned_to.is_(None)
                )
            )
            
            # 根据用户角色筛选可认领的任务类型
            if user_role == "consultant":
                query = query.filter(
                    PendingTask.task_type.in_(['new_user_reception', 'consultation_upgrade'])
                )
            elif user_role == "doctor":
                query = query.filter(
                    PendingTask.task_type.in_(['prescription_review', 'medical_consultation'])
                )
            elif user_role == "operator":
                query = query.filter(
                    PendingTask.task_type.in_(['system_maintenance', 'user_feedback'])
                )
            
            tasks = query.order_by(
                PendingTask.priority.desc(),
                PendingTask.created_at.desc()
            ).all()
            
            return [TaskConverter.from_model(task) for task in tasks]
            
        except Exception as e:
            logger.error(f"获取可认领任务失败: {e}")
            raise
    
    def get_tasks_by_status(self, status: str) -> List[Task]:
        """根据状态获取任务"""
        try:
            tasks = self.db.query(PendingTask).filter(
                PendingTask.status == status
            ).order_by(
                PendingTask.priority.desc(),
                PendingTask.created_at.desc()
            ).all()
            
            return [TaskConverter.from_model(task) for task in tasks]
            
        except Exception as e:
            logger.error(f"根据状态获取任务失败: {e}")
            raise
    
    def get_tasks_by_type(self, task_type: str) -> List[Task]:
        """根据类型获取任务"""
        try:
            tasks = self.db.query(PendingTask).filter(
                PendingTask.task_type == task_type
            ).order_by(
                PendingTask.priority.desc(),
                PendingTask.created_at.desc()
            ).all()
            
            return [TaskConverter.from_model(task) for task in tasks]
            
        except Exception as e:
            logger.error(f"根据类型获取任务失败: {e}")
            raise
    
    def get_overdue_tasks(self) -> List[Task]:
        """获取逾期任务"""
        try:
            from datetime import datetime
            
            now = datetime.now()
            tasks = self.db.query(PendingTask).filter(
                and_(
                    PendingTask.due_date < now,
                    PendingTask.status.in_(['pending', 'assigned', 'in_progress'])
                )
            ).order_by(
                PendingTask.due_date.asc(),
                PendingTask.priority.desc()
            ).all()
            
            return [TaskConverter.from_model(task) for task in tasks]
            
        except Exception as e:
            logger.error(f"获取逾期任务失败: {e}")
            raise
    
    def delete(self, task_id: str) -> bool:
        """删除任务"""
        try:
            task = self.db.query(PendingTask).filter(PendingTask.id == task_id).first()
            
            if not task:
                return False
            
            self.db.delete(task)
            self.db.commit()
            
            logger.info(f"删除任务成功: {task_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"删除任务失败: {e}")
            raise
