"""
方案状态值对象
"""
from enum import Enum
from typing import Optional


class PlanStatus(Enum):
    """方案状态枚举"""
    DRAFT = "draft"  # 草稿
    GENERATING = "generating"  # 生成中
    REVIEWING = "reviewing"  # 审核中
    APPROVED = "approved"  # 已批准
    REJECTED = "rejected"  # 已拒绝
    ARCHIVED = "archived"  # 已归档
    
    @classmethod
    def from_string(cls, status: str) -> "PlanStatus":
        """从字符串创建状态"""
        try:
            return cls(status)
        except ValueError:
            raise ValueError(f"无效的方案状态: {status}")
    
    def is_editable(self) -> bool:
        """是否可编辑"""
        return self in [self.DRAFT, self.REJECTED]
    
    def is_final(self) -> bool:
        """是否为最终状态"""
        return self in [self.APPROVED, self.ARCHIVED]
    
    def can_transition_to(self, target_status: "PlanStatus") -> bool:
        """检查是否可以转换到目标状态"""
        transitions = {
            self.DRAFT: [self.GENERATING, self.ARCHIVED],
            self.GENERATING: [self.REVIEWING, self.DRAFT],
            self.REVIEWING: [self.APPROVED, self.REJECTED, self.DRAFT],
            self.APPROVED: [self.ARCHIVED],
            self.REJECTED: [self.DRAFT, self.ARCHIVED],
            self.ARCHIVED: []
        }
        return target_status in transitions.get(self, [])
    
    def __str__(self) -> str:
        return self.value
