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
        return [cls.PENDING, cls.ASSIGNED, cls.IN_PROGRESS]
    
    @classmethod
    def get_final_statuses(cls) -> List[str]:
        """获取最终状态列表"""
        return [cls.COMPLETED, cls.CANCELLED]
    
    @classmethod
    def is_valid_transition(cls, from_status: str, to_status: str) -> bool:
        """检查状态转换是否有效"""
        valid_transitions = {
            cls.PENDING: [cls.ASSIGNED, cls.CANCELLED],
            cls.ASSIGNED: [cls.IN_PROGRESS, cls.CANCELLED],
            cls.IN_PROGRESS: [cls.COMPLETED, cls.CANCELLED],
            cls.COMPLETED: [],
            cls.CANCELLED: []
        }
        
        return to_status in valid_transitions.get(from_status, [])
