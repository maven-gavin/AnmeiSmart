"""
基础实体类
"""
from abc import ABC, abstractmethod
from typing import List, Any
from datetime import datetime
import uuid


class DomainEvent:
    """领域事件基类"""
    
    def __init__(self, event_type: str, aggregate_id: str, data: dict = None):
        self.event_id = str(uuid.uuid4())
        self.event_type = event_type
        self.aggregate_id = aggregate_id
        self.data = data or {}
        self.occurred_on = datetime.now()


class BaseEntity(ABC):
    """领域实体基类"""
    
    def __init__(self, id: str):
        self._id = id
        self._domain_events: List[DomainEvent] = []
    
    @property
    def id(self) -> str:
        """获取实体ID"""
        return self._id
    
    def _add_domain_event(self, event: DomainEvent) -> None:
        """添加领域事件"""
        self._domain_events.append(event)
    
    def get_domain_events(self) -> List[DomainEvent]:
        """获取所有领域事件"""
        return self._domain_events.copy()
    
    def clear_domain_events(self) -> None:
        """清除所有领域事件"""
        self._domain_events.clear()
    
    def __eq__(self, other: object) -> bool:
        """实体相等性比较"""
        if not isinstance(other, BaseEntity):
            return False
        return self._id == other._id
    
    def __hash__(self) -> int:
        """实体哈希值"""
        return hash(self._id)
    
    @abstractmethod
    def validate(self) -> None:
        """验证实体状态"""
        pass
