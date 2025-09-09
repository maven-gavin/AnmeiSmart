"""
任务应用服务 - 编排任务相关的用例
"""
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.tasks.domain.interfaces import ITaskDomainService
from app.tasks.schemas.task import (
    CreateTaskRequest,
    UpdateTaskRequest,
    TaskResponse
)
from app.tasks.converters.task_converter import TaskConverter

logger = logging.getLogger(__name__)


class TaskApplicationService:
    """任务应用服务 - 编排任务相关的用例"""
    
    def __init__(self, task_domain_service: ITaskDomainService):
        self.task_domain_service = task_domain_service
    
    def get_tasks_for_user_use_case(self, 
                                   user_id: str, 
                                   user_role: str,
                                   status: Optional[str] = None,
                                   task_type: Optional[str] = None,
                                   priority: Optional[str] = None,
                                   search: Optional[str] = None,
                                   db: Optional[Session] = None) -> List[TaskResponse]:
        """获取用户任务列表用例"""
        try:
            # 构建筛选条件
            filters = {}
            if status:
                filters['status'] = status
            if task_type:
                filters['task_type'] = task_type
            if priority:
                filters['priority'] = priority
            if search:
                filters['search'] = search
            
            # 调用领域服务获取任务
            tasks = self.task_domain_service.task_repository.get_tasks_for_user(
                user_id=user_id,
                user_role=user_role,
                **filters
            )
            
            # 转换为响应格式
            return TaskConverter.to_list_response(tasks, db)
            
        except Exception as e:
            logger.error(f"获取用户任务列表失败: {e}")
            raise
    
    def get_task_by_id_use_case(self, task_id: str, user_id: str, user_role: str, db: Optional[Session] = None) -> Optional[TaskResponse]:
        """获取任务详情用例"""
        try:
            # 调用领域服务获取任务
            task = self.task_domain_service.task_repository.get_by_id(task_id)
            
            if not task:
                return None
            
            # 权限检查
            from app.identity_access.deps.permission_deps import is_user_admin
            if not await is_user_admin(user):
                if task.assigned_to != user_id and not (task.status == "pending" and not task.assigned_to):
                    return None
            
            # 转换为响应格式
            return TaskConverter.to_response(task, db)
            
        except Exception as e:
            logger.error(f"获取任务详情失败: {e}")
            raise
    
    def create_task_use_case(self, user_id: str, data: CreateTaskRequest, db: Optional[Session] = None) -> TaskResponse:
        """创建任务用例"""
        try:
            # 调用领域服务创建任务
            task = self.task_domain_service.create_task(
                title=data.title,
                task_type=data.task_type,
                created_by=user_id,
                description=data.description,
                priority=data.priority,
                due_date=data.due_date,
                related_object_type=data.related_object_type,
                related_object_id=data.related_object_id,
                task_data=data.task_data,
                assigned_to=data.assigned_to
            )
            
            # 转换为响应格式
            return TaskConverter.to_response(task, db)
            
        except Exception as e:
            logger.error(f"创建任务失败: {e}")
            raise
    
    def claim_task_use_case(self, task_id: str, user_id: str, db: Optional[Session] = None) -> TaskResponse:
        """认领任务用例"""
        try:
            # 调用领域服务认领任务
            task = self.task_domain_service.claim_task(task_id, user_id)
            
            # 转换为响应格式
            return TaskConverter.to_response(task, db)
            
        except Exception as e:
            logger.error(f"认领任务失败: {e}")
            raise
    
    def update_task_status_use_case(self, 
                                   task_id: str, 
                                   user_id: str, 
                                   user_role: str,
                                   data: UpdateTaskRequest,
                                   db: Optional[Session] = None) -> Optional[TaskResponse]:
        """更新任务状态用例"""
        try:
            # 获取当前任务
            task = self.task_domain_service.task_repository.get_by_id(task_id)
            if not task:
                return None
            
            # 权限检查
            from app.identity_access.deps.permission_deps import is_user_admin
            if not await is_user_admin(user):
                if task.assigned_to != user_id:
                    return None
            
            # 根据更新内容调用相应的领域服务方法
            if data.status == "completed":
                task = self.task_domain_service.complete_task(
                    task_id, user_id, 
                    result=data.result, 
                    notes=data.notes
                )
            elif data.status == "cancelled":
                task = self.task_domain_service.cancel_task(
                    task_id, user_id, 
                    reason=data.notes
                )
            elif data.status == "in_progress":
                task = self.task_domain_service.start_task_progress(task_id, user_id)
            else:
                # 更新其他字段
                if data.title is not None or data.description is not None:
                    task = self.task_domain_service.update_task_details(
                        task_id, user_id,
                        title=data.title,
                        description=data.description
                    )
                
                if data.priority is not None:
                    task = self.task_domain_service.update_task_priority(
                        task_id, user_id, data.priority
                    )
                
                # 更新其他字段
                if data.notes is not None:
                    task.notes = data.notes
                if data.result is not None:
                    task.result = data.result
                
                # 保存更新
                task = self.task_domain_service.task_repository.save(task)
            
            # 转换为响应格式
            return TaskConverter.to_response(task, db)
            
        except Exception as e:
            logger.error(f"更新任务状态失败: {e}")
            raise
    
    def create_new_user_reception_task_use_case(self, user_id: str, username: str, db: Optional[Session] = None) -> TaskResponse:
        """创建新用户接待任务用例"""
        try:
            # 调用领域服务创建接待任务
            task = self.task_domain_service.create_new_user_reception_task(user_id, username)
            
            # 转换为响应格式
            return TaskConverter.to_response(task, db)
            
        except Exception as e:
            logger.error(f"创建新用户接待任务失败: {e}")
            raise
