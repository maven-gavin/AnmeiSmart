"""
任务聚合根实体
"""
from datetime import datetime
from typing import Optional, Dict, Any

from app.common.domain.entities.base_entity import BaseEntity, DomainEvent
from app.tasks.domain.value_objects import TaskStatus, TaskPriority, TaskType


class TaskEntity(BaseEntity):
    """任务聚合根 - 管理任务的核心业务逻辑"""
    
    def __init__(
        self,
        id: str,
        title: str,
        taskType: str,
        description: Optional[str] = None,
        status: str = TaskStatus.PENDING.value,
        priority: str = TaskPriority.MEDIUM.value,
        createdBy: Optional[str] = None,
        assignedTo: Optional[str] = None,
        assignedAt: Optional[datetime] = None,
        relatedObjectType: Optional[str] = None,
        relatedObjectId: Optional[str] = None,
        taskData: Optional[Dict[str, Any]] = None,
        dueDate: Optional[datetime] = None,
        completedAt: Optional[datetime] = None,
        result: Optional[Dict[str, Any]] = None,
        notes: Optional[str] = None,
        createdAt: Optional[datetime] = None,
        updatedAt: Optional[datetime] = None,
    ):
        # 调用父类构造函数
        super().__init__(id)
        
        # 设置属性
        self.title = title
        self.taskType = taskType
        self.description = description
        self.status = status
        self.priority = priority
        self.createdBy = createdBy
        self.assignedTo = assignedTo
        self.assignedAt = assignedAt
        self.relatedObjectType = relatedObjectType
        self.relatedObjectId = relatedObjectId
        self.taskData = taskData
        self.dueDate = dueDate
        self.completedAt = completedAt
        self.result = result
        self.notes = notes
        self.createdAt = createdAt or datetime.now()
        self.updatedAt = updatedAt or datetime.now()
        
        # 验证实体状态
        self.validate()
    
    def validate(self) -> None:
        """验证实体状态 - 必须实现"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.debug(f"TaskEntity.validate开始验证任务: ID={self.id}, title={self.title}, type={self.taskType}, status={self.status}, priority={self.priority}")
        
        if not self.title or not self.title.strip():
            logger.error(f"任务标题验证失败: title={self.title}")
            raise ValueError("任务标题不能为空")
        
        if len(self.title.strip()) > 500:
            logger.error(f"任务标题过长: length={len(self.title.strip())}")
            raise ValueError("任务标题过长，不能超过500字符")
        
        if self.description and len(self.description.strip()) > 2000:
            logger.error(f"任务描述过长: length={len(self.description.strip())}")
            raise ValueError("任务描述过长，不能超过2000字符")
        
        logger.debug(f"验证任务类型: {self.taskType}")
        if not TaskType.get_task_type_metadata(self.taskType):
            logger.error(f"无效的任务类型: {self.taskType}")
            raise ValueError(f"无效的任务类型: {self.taskType}")
        
        logger.debug(f"验证任务状态: {self.status}")
        valid_statuses = TaskStatus.get_all_values()
        logger.debug(f"有效状态列表: {valid_statuses}, 类型: {type(valid_statuses)}")
        if self.status not in valid_statuses:
            logger.error(f"无效的任务状态: {self.status}, 有效状态: {valid_statuses}")
            raise ValueError(f"无效的任务状态: {self.status}")
        
        logger.debug(f"验证任务优先级: {self.priority}")
        valid_priorities = TaskPriority.get_all_values()
        logger.debug(f"有效优先级列表: {valid_priorities}, 类型: {type(valid_priorities)}")
        if self.priority not in valid_priorities:
            logger.error(f"无效的任务优先级: {self.priority}, 有效优先级: {valid_priorities}")
            raise ValueError(f"无效的任务优先级: {self.priority}")
        
        logger.debug(f"TaskEntity.validate验证通过: ID={self.id}")
    
    @classmethod
    def create(
        cls,
        title: str,
        taskType: str,
        createdBy: Optional[str] = None,
        **kwargs
    ) -> "TaskEntity":
        """工厂方法 - 创建任务"""
        from app.common.infrastructure.db.uuid_utils import task_id
        
        # 获取任务类型元数据
        metadata = TaskType.get_task_type_metadata(taskType)
        default_priority = kwargs.pop('priority', metadata.get('default_priority', TaskPriority.MEDIUM.value))

        field_map = {
            "description": "description",
            "priority": "priority",
            "due_date": "dueDate",
            "related_object_type": "relatedObjectType",
            "related_object_id": "relatedObjectId",
            "task_data": "taskData",
            "assigned_to": "assignedTo",
            "assigned_at": "assignedAt",
            "completed_at": "completedAt",
            "created_at": "createdAt",
            "updated_at": "updatedAt",
            "result": "result",
            "notes": "notes",
        }
        normalized_kwargs = {}
        for key, value in kwargs.items():
            camel_key = field_map.get(key, key)
            normalized_kwargs[camel_key] = value

        task = cls(
            id=task_id(),
            title=title.strip(),
            taskType=taskType,
            priority=default_priority,
            createdBy=createdBy,
            **normalized_kwargs
        )
        
        task.validate()
        return task
    
    def assignTo(self, user_id: str) -> None:
        """分配任务给用户"""
        if not user_id:
            raise ValueError("用户ID不能为空")
        
        if self.status not in [TaskStatus.PENDING.value]:
            raise ValueError(f"只有待处理状态的任务可以被分配，当前状态: {self.status}")
        
        old_assigned_to = self.assignedTo
        self.assignedTo = user_id
        self.assignedAt = datetime.now()
        self.status = TaskStatus.ASSIGNED.value
        self.updatedAt = datetime.now()
        
        # 添加领域事件
        self._add_domain_event(DomainEvent(
            event_type="task_assigned",
            aggregate_id=self.id,
            data={
                "oldAssignedTo": old_assigned_to,
                "newAssignedTo": user_id,
                "assignedAt": self.assignedAt.isoformat()
            }
        ))
    
    def claim(self, user_id: str) -> None:
        """认领任务"""
        if not user_id:
            raise ValueError("用户ID不能为空")
        
        if self.status != TaskStatus.PENDING.value:
            raise ValueError(f"只有待处理状态的任务可以被认领，当前状态: {self.status}")
        
        if self.assignedTo:
            raise ValueError("任务已被分配，无法认领")
        
        self.assignedTo = user_id
        self.assignedAt = datetime.now()
        self.status = TaskStatus.ASSIGNED.value
        self.updatedAt = datetime.now()
        
        # 添加领域事件
        self._add_domain_event(DomainEvent(
            event_type="task_claimed",
            aggregate_id=self.id,
            data={
                "claimedBy": user_id,
                "claimedAt": self.assignedAt.isoformat()
            }
        ))
    
    def startProgress(self) -> None:
        """开始处理任务"""
        if self.status != TaskStatus.ASSIGNED.value:
            raise ValueError(f"只有已分配状态的任务可以开始处理，当前状态: {self.status}")
        
        if not self.assignedTo:
            raise ValueError("任务未分配，无法开始处理")
        
        old_status = self.status
        self.status = TaskStatus.IN_PROGRESS.value
        self.updatedAt = datetime.now()
        
        # 添加领域事件
        self._add_domain_event(DomainEvent(
            event_type="task_started",
            aggregate_id=self.id,
            data={
                "oldStatus": old_status,
                "newStatus": self.status,
                "startedAt": self.updatedAt.isoformat()
            }
        ))
    
    def complete(self, result: Optional[Dict[str, Any]] = None, notes: Optional[str] = None) -> None:
        """完成任务"""
        if self.status not in [TaskStatus.ASSIGNED.value, TaskStatus.IN_PROGRESS.value]:
            raise ValueError(f"只有已分配或处理中状态的任务可以完成，当前状态: {self.status}")
        
        if not self.assignedTo:
            raise ValueError("任务未分配，无法完成")
        
        old_status = self.status
        self.status = TaskStatus.COMPLETED.value
        self.completedAt = datetime.now()
        self.updatedAt = datetime.now()
        
        if result is not None:
            self.result = result
        
        if notes is not None:
            self.notes = notes
        
        # 添加领域事件
        self._add_domain_event(DomainEvent(
            event_type="task_completed",
            aggregate_id=self.id,
            data={
                "oldStatus": old_status,
                "newStatus": self.status,
                "completedAt": self.completedAt.isoformat(),
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
        self.updatedAt = datetime.now()
        
        if reason:
            self.notes = f"取消原因: {reason}"
        
        # 添加领域事件
        self._add_domain_event(DomainEvent(
            event_type="task_cancelled",
            aggregate_id=self.id,
            data={
                "oldStatus": old_status,
                "newStatus": self.status,
                "cancelledAt": self.updatedAt.isoformat(),
                "reason": reason
            }
        ))
    
    def updatePriority(self, new_priority: str) -> None:
        """更新任务优先级"""
        if new_priority not in TaskPriority.get_all_values():
            raise ValueError(f"无效的任务优先级: {new_priority}")
        
        if new_priority == self.priority:
            return
        
        old_priority = self.priority
        self.priority = new_priority
        self.updatedAt = datetime.now()
        
        self._add_domain_event(DomainEvent(
            event_type="task_priority_updated",
            aggregate_id=self.id,
            data={
                "oldPriority": old_priority,
                "newPriority": new_priority,
                "updatedAt": self.updatedAt.isoformat()
            }
        ))
    
    def updateDetails(self, title: Optional[str] = None, description: Optional[str] = None) -> None:
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
        
        self.updatedAt = datetime.now()
        
        # 添加领域事件
        self._add_domain_event(DomainEvent(
            event_type="task_details_updated",
            aggregate_id=self.id,
            data={
                "title": self.title,
                "description": self.description,
                "updatedAt": self.updatedAt.isoformat()
            }
        ))
    
    def isAssignable(self) -> bool:
        """检查任务是否可以被分配"""
        return self.status == TaskStatus.PENDING.value and not self.assignedTo
    
    def isClaimable(self) -> bool:
        """检查任务是否可以被认领"""
        return self.status == TaskStatus.PENDING.value and not self.assignedTo
    
    def isEditable(self) -> bool:
        """检查任务是否可以被编辑"""
        return self.status not in [TaskStatus.COMPLETED.value, TaskStatus.CANCELLED.value]
    
    def getRemainingTime(self) -> Optional[float]:
        """获取剩余时间（小时）"""
        if not self.dueDate:
            return None
        
        now = datetime.now()
        if now >= self.dueDate:
            return 0.0
        
        remaining = self.dueDate - now
        return remaining.total_seconds() / 3600  # 转换为小时

    def __str__(self) -> str:
        return (
            f"TaskEntity(id={self.id}, title={self.title}, status={self.status}, "
            f"priority={self.priority}, assignedTo={self.assignedTo})"
        )

    def __repr__(self) -> str:
        return (
            "TaskEntity("
            f"id={self.id}, title={self.title}, taskType={self.taskType}, "
            f"status={self.status}, priority={self.priority}, createdBy={self.createdBy}, "
            f"assignedTo={self.assignedTo}, dueDate={self.dueDate}, "
            f"completedAt={self.completedAt}, createdAt={self.createdAt}, updatedAt={self.updatedAt})"
        )
