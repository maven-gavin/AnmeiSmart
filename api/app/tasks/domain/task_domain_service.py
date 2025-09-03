"""
任务领域服务实现
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.tasks.domain.interfaces import ITaskDomainService, ITaskRepository
from app.tasks.domain.entities.task import Task
from app.tasks.domain.value_objects import TaskStatus, TaskType

logger = logging.getLogger(__name__)


class TaskDomainService(ITaskDomainService):
    """任务领域服务 - 实现任务相关的领域逻辑"""
    
    def __init__(self, task_repository: ITaskRepository):
        self.task_repository = task_repository
    
    def create_task(self, title: str, task_type: str, created_by: Optional[str] = None, **kwargs) -> Task:
        """创建任务 - 领域逻辑"""
        # 领域规则验证
        if not title or not title.strip():
            raise ValueError("任务标题不能为空")
        
        if not TaskType.get_task_type_metadata(task_type):
            raise ValueError(f"无效的任务类型: {task_type}")
        
        # 创建领域对象
        task = Task.create(
            title=title,
            task_type=task_type,
            created_by=created_by,
            **kwargs
        )
        
        # 保存到仓储
        saved_task = self.task_repository.save(task)
        
        logger.info(f"创建任务成功: {saved_task.title}")
        return saved_task
    
    def assign_task(self, task_id: str, user_id: str) -> Task:
        """分配任务 - 领域逻辑"""
        if not user_id:
            raise ValueError("用户ID不能为空")
        
        task = self.task_repository.get_by_id(task_id)
        if not task:
            raise ValueError("任务不存在")
        
        # 调用实体的业务方法
        task.assign_to(user_id)
        
        # 保存到仓储
        saved_task = self.task_repository.save(task)
        
        logger.info(f"任务 {saved_task.title} 已分配给用户 {user_id}")
        return saved_task
    
    def claim_task(self, task_id: str, user_id: str) -> Task:
        """认领任务 - 领域逻辑"""
        if not user_id:
            raise ValueError("用户ID不能为空")
        
        task = self.task_repository.get_by_id(task_id)
        if not task:
            raise ValueError("任务不存在")
        
        # 调用实体的业务方法
        task.claim(user_id)
        
        # 保存到仓储
        saved_task = self.task_repository.save(task)
        
        logger.info(f"用户 {user_id} 认领任务: {saved_task.title}")
        return saved_task
    
    def start_task_progress(self, task_id: str, user_id: str) -> Task:
        """开始处理任务 - 领域逻辑"""
        if not user_id:
            raise ValueError("用户ID不能为空")
        
        task = self.task_repository.get_by_id(task_id)
        if not task:
            raise ValueError("任务不存在")
        
        # 权限检查
        if task.assigned_to != user_id:
            raise ValueError("只有任务负责人可以开始处理任务")
        
        # 调用实体的业务方法
        task.start_progress()
        
        # 保存到仓储
        saved_task = self.task_repository.save(task)
        
        logger.info(f"任务 {saved_task.title} 开始处理")
        return saved_task
    
    def complete_task(self, task_id: str, user_id: str, result: Optional[Dict[str, Any]] = None, notes: Optional[str] = None) -> Task:
        """完成任务 - 领域逻辑"""
        if not user_id:
            raise ValueError("用户ID不能为空")
        
        task = self.task_repository.get_by_id(task_id)
        if not task:
            raise ValueError("任务不存在")
        
        # 权限检查
        if task.assigned_to != user_id:
            raise ValueError("只有任务负责人可以完成任务")
        
        # 调用实体的业务方法
        task.complete(result=result, notes=notes)
        
        # 保存到仓储
        saved_task = self.task_repository.save(task)
        
        logger.info(f"任务 {saved_task.title} 已完成")
        return saved_task
    
    def cancel_task(self, task_id: str, user_id: str, reason: Optional[str] = None) -> Task:
        """取消任务 - 领域逻辑"""
        if not user_id:
            raise ValueError("用户ID不能为空")
        
        task = self.task_repository.get_by_id(task_id)
        if not task:
            raise ValueError("任务不存在")
        
        # 权限检查
        if task.assigned_to != user_id and task.created_by != user_id:
            raise ValueError("只有任务负责人或创建者可以取消任务")
        
        # 调用实体的业务方法
        task.cancel(reason=reason)
        
        # 保存到仓储
        saved_task = self.task_repository.save(task)
        
        logger.info(f"任务 {saved_task.title} 已取消")
        return saved_task
    
    def update_task_priority(self, task_id: str, user_id: str, new_priority: str) -> Task:
        """更新任务优先级 - 领域逻辑"""
        if not user_id:
            raise ValueError("用户ID不能为空")
        
        task = self.task_repository.get_by_id(task_id)
        if not task:
            raise ValueError("任务不存在")
        
        # 权限检查
        if task.assigned_to != user_id and task.created_by != user_id:
            raise ValueError("只有任务负责人或创建者可以更新任务优先级")
        
        # 调用实体的业务方法
        task.update_priority(new_priority)
        
        # 保存到仓储
        saved_task = self.task_repository.save(task)
        
        logger.info(f"任务 {saved_task.title} 优先级已更新为 {new_priority}")
        return saved_task
    
    def update_task_details(self, task_id: str, user_id: str, title: Optional[str] = None, description: Optional[str] = None) -> Task:
        """更新任务详情 - 领域逻辑"""
        if not user_id:
            raise ValueError("用户ID不能为空")
        
        task = self.task_repository.get_by_id(task_id)
        if not task:
            raise ValueError("任务不存在")
        
        # 权限检查
        if task.assigned_to != user_id and task.created_by != user_id:
            raise ValueError("只有任务负责人或创建者可以更新任务详情")
        
        # 调用实体的业务方法
        task.update_details(title=title, description=description)
        
        # 保存到仓储
        saved_task = self.task_repository.save(task)
        
        logger.info(f"任务 {saved_task.title} 详情已更新")
        return saved_task
    
    def create_new_user_reception_task(self, user_id: str, username: str) -> Task:
        """为新用户创建接待任务 - 领域逻辑"""
        if not user_id:
            raise ValueError("用户ID不能为空")
        
        if not username:
            raise ValueError("用户名不能为空")
        
        # 创建任务
        task = Task.create(
            title=f"新用户接待：{username}",
            description=f"用户 {username} 刚刚注册，需要顾问主动联系提供咨询服务",
            task_type=TaskType.NEW_USER_RECEPTION.value,
            priority="medium",
            created_by=None,  # 系统创建
            related_object_type="user",
            related_object_id=user_id,
            task_data={
                "user_id": user_id,
                "username": username,
                "registration_time": datetime.now().isoformat()
            }
        )
        
        # 保存到仓储
        saved_task = self.task_repository.save(task)
        
        logger.info(f"为新用户 {username} 创建接待任务")
        return saved_task
