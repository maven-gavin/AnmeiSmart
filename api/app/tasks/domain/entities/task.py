"""
任务聚合根实体
"""
from datetime import datetime
from typing import Optional, Dict, Any

from app.common.domain.entities.base_entity import BaseEntity, DomainEvent
from app.tasks.domain.value_objects import TaskStatus, TaskPriority, TaskType


class Task(BaseEntity):
    """任务聚合根 - 管理任务的核心业务逻辑"""
    
    def __init__(
        self,
        id: str,
        title: str,
        task_type: str,
        description: Optional[str] = None,
        status: str = TaskStatus.PENDING,
        priority: str = TaskPriority.MEDIUM,
        created_by: Optional[str] = None,
        assigned_to: Optional[str] = None,
        assigned_at: Optional[datetime] = None,
        related_object_type: Optional[str] = None,
        related_object_id: Optional[str] = None,
        task_data: Optional[Dict[str, Any]] = None,
        due_date: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        result: Optional[Dict[str, Any]] = None,
        notes: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        # 调用父类构造函数
        super().__init__(id)
        
        # 设置属性
        self.title = title
        self.task_type = task_type
        self.description = description
        self.status = status
        self.priority = priority
        self.created_by = created_by
        self.assigned_to = assigned_to
        self.assigned_at = assigned_at
        self.related_object_type = related_object_type
        self.related_object_id = related_object_id
        self.task_data = task_data
        self.due_date = due_date
        self.completed_at = completed_at
        self.result = result
        self.notes = notes
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
        
        # 验证实体状态
        self.validate()
    
    def validate(self) -> None:
        """验证实体状态 - 必须实现"""
        if not self.title or not self.title.strip():
            raise ValueError("任务标题不能为空")
        
        if len(self.title.strip()) > 500:
            raise ValueError("任务标题过长，不能超过500字符")
        
        if self.description and len(self.description.strip()) > 2000:
            raise ValueError("任务描述过长，不能超过2000字符")
        
        if not TaskType.get_task_type_metadata(self.task_type):
            raise ValueError(f"无效的任务类型: {self.task_type}")
        
        if self.status not in [status.value for status in TaskStatus]:
            raise ValueError(f"无效的任务状态: {self.status}")
        
        if self.priority not in [priority.value for priority in TaskPriority]:
            raise ValueError(f"无效的任务优先级: {self.priority}")
    
    @classmethod
    def create(cls, 
               title: str, 
               task_type: str, 
               created_by: Optional[str] = None,
               **kwargs) -> "Task":
        """工厂方法 - 创建任务"""
        from app.common.infrastructure.db.uuid_utils import task_id
        
        # 获取任务类型元数据
        metadata = TaskType.get_task_type_metadata(task_type)
        default_priority = kwargs.get('priority', metadata.get('default_priority', TaskPriority.MEDIUM))
        
        task = cls(
            id=task_id(),
            title=title.strip(),
            task_type=task_type,
            priority=default_priority,
            created_by=created_by,
            **kwargs
        )
        
        task.validate()
        return task
    
    def assign_to(self, user_id: str) -> None:
        """分配任务给用户"""
        if not user_id:
            raise ValueError("用户ID不能为空")
        
        if self.status not in [TaskStatus.PENDING.value]:
            raise ValueError(f"只有待处理状态的任务可以被分配，当前状态: {self.status}")
        
        old_assigned_to = self.assigned_to
        self.assigned_to = user_id
        self.assigned_at = datetime.now()
        self.status = TaskStatus.ASSIGNED.value
        self.updated_at = datetime.now()
        
        # 添加领域事件
        self._add_domain_event(DomainEvent(
            event_type="task_assigned",
            aggregate_id=self.id,
            data={
                "old_assigned_to": old_assigned_to,
                "new_assigned_to": user_id,
                "assigned_at": self.assigned_at.isoformat()
            }
        ))
    
    def claim(self, user_id: str) -> None:
        """认领任务"""
        if not user_id:
            raise ValueError("用户ID不能为空")
        
        if self.status != TaskStatus.PENDING.value:
            raise ValueError(f"只有待处理状态的任务可以被认领，当前状态: {self.status}")
        
        if self.assigned_to:
            raise ValueError("任务已被分配，无法认领")
        
        self.assigned_to = user_id
        self.assigned_at = datetime.now()
        self.status = TaskStatus.ASSIGNED.value
        self.updated_at = datetime.now()
        
        # 添加领域事件
        self._add_domain_event(DomainEvent(
            event_type="task_claimed",
            aggregate_id=self.id,
            data={
                "claimed_by": user_id,
                "claimed_at": self.assigned_at.isoformat()
            }
        ))
    
    def start_progress(self) -> None:
        """开始处理任务"""
        if self.status != TaskStatus.ASSIGNED.value:
            raise ValueError(f"只有已分配状态的任务可以开始处理，当前状态: {self.status}")
        
        if not self.assigned_to:
            raise ValueError("任务未分配，无法开始处理")
        
        old_status = self.status
        self.status = TaskStatus.IN_PROGRESS.value
        self.updated_at = datetime.now()
        
        # 添加领域事件
        self._add_domain_event(DomainEvent(
            event_type="task_started",
            aggregate_id=self.id,
            data={
                "old_status": old_status,
                "new_status": self.status,
                "started_at": self.updated_at.isoformat()
            }
        ))
    
    def complete(self, result: Optional[Dict[str, Any]] = None, notes: Optional[str] = None) -> None:
        """完成任务"""
        if self.status not in [TaskStatus.ASSIGNED.value, TaskStatus.IN_PROGRESS.value]:
            raise ValueError(f"只有已分配或处理中状态的任务可以完成，当前状态: {self.status}")
        
        if not self.assigned_to:
            raise ValueError("任务未分配，无法完成")
        
        old_status = self.status
        self.status = TaskStatus.COMPLETED.value
        self.completed_at = datetime.now()
        self.updated_at = datetime.now()
        
        if result is not None:
            self.result = result
        
        if notes is not None:
            self.notes = notes
        
        # 添加领域事件
        self._add_domain_event(DomainEvent(
            event_type="task_completed",
            aggregate_id=self.id,
            data={
                "old_status": old_status,
                "new_status": self.status,
                "completed_at": self.completed_at.isoformat(),
                "result": self.result,
                "notes": self.notes
            }
        ))
    
    def cancel(self, reason: Optional[str] = None) -> None:
        """取消任务"""
        if self.status in [TaskStatus.COMPLETED.value, TaskStatus.CANCELLED.value]:
            raise ValueError(f"已完成或已取消的任务无法取消，当前状态: {self.status}")
        
        old_status = self.status
        self.status = TaskStatus.CANCELLED.value
        self.updated_at = datetime.now()
        
        if reason:
            self.notes = f"取消原因: {reason}"
        
        # 添加领域事件
        self._add_domain_event(DomainEvent(
            event_type="task_cancelled",
            aggregate_id=self.id,
            data={
                "old_status": old_status,
                "new_status": self.status,
                "cancelled_at": self.updated_at.isoformat(),
                "reason": reason
            }
        ))
    
    def update_priority(self, new_priority: str) -> None:
        """更新任务优先级"""
        if new_priority not in [priority.value for priority in TaskPriority]:
            raise ValueError(f"无效的任务优先级: {new_priority}")
        
        if new_priority == self.priority:
            return
        
        old_priority = self.priority
        self.priority = new_priority
        self.updated_at = datetime.now()
        
        # 添加领域事件
        self._add_domain_event(DomainEvent(
            event_type="task_priority_updated",
            aggregate_id=self.id,
            data={
                "old_priority": old_priority,
                "new_priority": new_priority,
                "updated_at": self.updated_at.isoformat()
            }
        ))
    
    def update_details(self, title: Optional[str] = None, description: Optional[str] = None) -> None:
        """更新任务详情"""
        if title is not None:
            if not title.strip():
                raise ValueError("任务标题不能为空")
            if len(title.strip()) > 500:
                raise ValueError("任务标题过长，不能超过500字符")
            self.title = title.strip()
        
        if description is not None:
            if description and len(description.strip()) > 2000:
                raise ValueError("任务描述过长，不能超过2000字符")
            self.description = description.strip() if description else None
        
        self.updated_at = datetime.now()
        
        # 添加领域事件
        self._add_domain_event(DomainEvent(
            event_type="task_details_updated",
            aggregate_id=self.id,
            data={
                "title": self.title,
                "description": self.description,
                "updated_at": self.updated_at.isoformat()
            }
        ))
    
    def is_assignable(self) -> bool:
        """检查任务是否可以被分配"""
        return self.status == TaskStatus.PENDING.value and not self.assigned_to
    
    def is_claimable(self) -> bool:
        """检查任务是否可以被认领"""
        return self.status == TaskStatus.PENDING.value and not self.assigned_to
    
    def is_editable(self) -> bool:
        """检查任务是否可以被编辑"""
        return self.status not in [TaskStatus.COMPLETED.value, TaskStatus.CANCELLED.value]
    
    def get_remaining_time(self) -> Optional[float]:
        """获取剩余时间（小时）"""
        if not self.due_date:
            return None
        
        now = datetime.now()
        if now >= self.due_date:
            return 0.0
        
        remaining = self.due_date - now
        return remaining.total_seconds() / 3600  # 转换为小时
