"""
任务状态值对象
"""
from enum import Enum
from typing import List


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    
    @classmethod
    def get_active_statuses(cls) -> List[str]:
        """获取活跃状态列表"""
        return [cls.PENDING.value, cls.ASSIGNED.value, cls.IN_PROGRESS.value]
    
    @classmethod
    def get_final_statuses(cls) -> List[str]:
        """获取最终状态列表"""
        return [cls.COMPLETED.value, cls.CANCELLED.value]
    
    @classmethod
    def get_all_values(cls) -> List[str]:
        """获取所有状态值列表"""
        return [e.value for e in cls]
    
    @classmethod
    def is_valid_transition(cls, from_status: str, to_status: str) -> bool:
        """检查状态转换是否有效"""
        valid_transitions = {
            cls.PENDING.value: [cls.ASSIGNED.value, cls.CANCELLED.value],
            cls.ASSIGNED.value: [cls.IN_PROGRESS.value, cls.CANCELLED.value],
            cls.IN_PROGRESS.value: [cls.COMPLETED.value, cls.CANCELLED.value],
            cls.COMPLETED.value: [],
            cls.CANCELLED.value: []
        }
        
        return to_status in valid_transitions.get(from_status, [])
