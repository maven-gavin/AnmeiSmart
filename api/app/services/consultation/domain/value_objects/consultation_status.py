"""
咨询状态值对象
"""
from enum import Enum
from typing import Optional


class ConsultationStatus(Enum):
    """咨询状态枚举"""
    PENDING = "pending"  # 待处理
    IN_PROGRESS = "in_progress"  # 进行中
    COMPLETED = "completed"  # 已完成
    CANCELLED = "cancelled"  # 已取消
    ARCHIVED = "archived"  # 已归档
    
    @classmethod
    def from_string(cls, status: str) -> "ConsultationStatus":
        """从字符串创建状态"""
        try:
            return cls(status)
        except ValueError:
            raise ValueError(f"无效的咨询状态: {status}")
    
    def is_active(self) -> bool:
        """是否为活跃状态"""
        return self in [self.PENDING, self.IN_PROGRESS]
    
    def can_transition_to(self, target_status: "ConsultationStatus") -> bool:
        """检查是否可以转换到目标状态"""
        transitions = {
            self.PENDING: [self.IN_PROGRESS, self.CANCELLED],
            self.IN_PROGRESS: [self.COMPLETED, self.CANCELLED],
            self.COMPLETED: [self.ARCHIVED],
            self.CANCELLED: [self.ARCHIVED],
            self.ARCHIVED: []
        }
        return target_status in transitions.get(self, [])
    
    def __str__(self) -> str:
        return self.value
