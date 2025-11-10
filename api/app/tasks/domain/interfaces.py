"""
任务领域服务接口定义
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from app.tasks.domain.entities.task import TaskEntity


class ITaskDomainService(ABC):
    """任务领域服务接口"""
    
    @abstractmethod
    def create_task(self, title: str, task_type: str, created_by: Optional[str] = None, **kwargs) -> TaskEntity:
        """创建任务"""
        pass
    
    @abstractmethod
    def assign_task(self, task_id: str, user_id: str) -> TaskEntity:
        """分配任务"""
        pass
    
    @abstractmethod
    def claim_task(self, task_id: str, user_id: str) -> TaskEntity:
        """认领任务"""
        pass
    
    @abstractmethod
    def start_task_progress(self, task_id: str, user_id: str) -> TaskEntity:
        """开始处理任务"""
        pass
    
    @abstractmethod
    def complete_task(self, task_id: str, user_id: str, result: Optional[Dict[str, Any]] = None, notes: Optional[str] = None) -> TaskEntity:
        """完成任务"""
        pass
    
    @abstractmethod
    def cancel_task(self, task_id: str, user_id: str, reason: Optional[str] = None) -> TaskEntity:
        """取消任务"""
        pass
    
    @abstractmethod
    def update_task_priority(self, task_id: str, user_id: str, new_priority: str) -> TaskEntity:
        """更新任务优先级"""
        pass
    
    @abstractmethod
    def update_task_details(self, task_id: str, user_id: str, title: Optional[str] = None, description: Optional[str] = None) -> TaskEntity:
        """更新任务详情"""
        pass
    
    @abstractmethod
    def create_new_user_reception_task(self, user_id: str, username: str) -> TaskEntity:
        """为新用户创建接待任务"""
        pass


class ITaskRepository(ABC):
    """任务仓储接口"""
    
    @abstractmethod
    def save(self, task: TaskEntity) -> TaskEntity:
        """保存任务"""
        pass
    
    @abstractmethod
    def get_by_id(self, task_id: str) -> Optional[TaskEntity]:
        """根据ID获取任务"""
        pass
    
    @abstractmethod
    def get_tasks_for_user(self, user_id: str, user_role: str, **filters) -> List[TaskEntity]:
        """获取用户相关任务"""
        pass
    
    @abstractmethod
    def get_claimable_tasks(self, user_role: str) -> List[TaskEntity]:
        """获取可认领的任务"""
        pass
    
    @abstractmethod
    def get_tasks_by_status(self, status: str) -> List[TaskEntity]:
        """根据状态获取任务"""
        pass
    
    @abstractmethod
    def get_tasks_by_type(self, task_type: str) -> List[TaskEntity]:
        """根据类型获取任务"""
        pass
    
    @abstractmethod
    def get_overdue_tasks(self) -> List[TaskEntity]:
        """获取逾期任务"""
        pass
    
    @abstractmethod
    def delete(self, task_id: str) -> bool:
        """删除任务"""
        pass
