"""
任务优先级值对象
"""
from enum import Enum
from typing import List


class TaskPriority(str, Enum):
    """任务优先级枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
    
    @classmethod
    def get_priority_order(cls) -> List[str]:
        """获取优先级排序（从高到低）"""
        return [cls.URGENT, cls.HIGH, cls.MEDIUM, cls.LOW]
    
    @classmethod
    def get_higher_priorities(cls, priority: str) -> List[str]:
        """获取比指定优先级更高的优先级列表"""
        order = cls.get_priority_order()
        try:
            current_index = order.index(priority)
            return order[:current_index]
        except ValueError:
            return []
    
    @classmethod
    def is_higher_than(cls, priority1: str, priority2: str) -> bool:
        """检查优先级1是否高于优先级2"""
        order = cls.get_priority_order()
        try:
            index1 = order.index(priority1)
            index2 = order.index(priority2)
            return index1 < index2
        except ValueError:
            return False
