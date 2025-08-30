"""
咨询聚合根实体
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

from ..value_objects.consultation_status import ConsultationStatus


class Consultation:
    """咨询聚合根 - 管理咨询会话的生命周期"""
    
    def __init__(
        self,
        id: str,
        customer_id: str,
        consultant_id: Optional[str],
        status: ConsultationStatus,
        title: str,
        created_at: datetime,
        updated_at: datetime,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self._id = id
        self._customer_id = customer_id
        self._consultant_id = consultant_id
        self._status = status
        self._title = title
        self._created_at = created_at
        self._updated_at = updated_at
        self._metadata = metadata or {}
        self._domain_events = []
    
    @property
    def id(self) -> str:
        return self._id
    
    @property
    def customer_id(self) -> str:
        return self._customer_id
    
    @property
    def consultant_id(self) -> Optional[str]:
        return self._consultant_id
    
    @property
    def status(self) -> ConsultationStatus:
        return self._status
    
    @property
    def title(self) -> str:
        return self._title
    
    @property
    def created_at(self) -> datetime:
        return self._created_at
    
    @property
    def updated_at(self) -> datetime:
        return self._updated_at
    
    @property
    def metadata(self) -> Dict[str, Any]:
        return self._metadata.copy()
    
    @property
    def domain_events(self) -> List:
        return self._domain_events.copy()
    
    def assign_consultant(self, consultant_id: str) -> None:
        """分配顾问"""
        if not consultant_id:
            raise ValueError("顾问ID不能为空")
        
        if self._consultant_id:
            raise ValueError("咨询已分配顾问")
        
        self._consultant_id = consultant_id
        self._status = ConsultationStatus.IN_PROGRESS
        self._updated_at = datetime.utcnow()
        
        self._add_domain_event("ConsultantAssigned", {
            "consultation_id": self._id,
            "consultant_id": consultant_id,
            "timestamp": self._updated_at
        })
    
    def complete_consultation(self) -> None:
        """完成咨询"""
        if not self._consultant_id:
            raise ValueError("咨询未分配顾问，无法完成")
        
        if not self._status.can_transition_to(ConsultationStatus.COMPLETED):
            raise ValueError(f"当前状态 {self._status} 无法转换为完成状态")
        
        self._status = ConsultationStatus.COMPLETED
        self._updated_at = datetime.utcnow()
        
        self._add_domain_event("ConsultationCompleted", {
            "consultation_id": self._id,
            "timestamp": self._updated_at
        })
    
    def cancel_consultation(self, reason: Optional[str] = None) -> None:
        """取消咨询"""
        if not self._status.can_transition_to(ConsultationStatus.CANCELLED):
            raise ValueError(f"当前状态 {self._status} 无法转换为取消状态")
        
        self._status = ConsultationStatus.CANCELLED
        self._updated_at = datetime.utcnow()
        
        if reason:
            self._metadata["cancellation_reason"] = reason
        
        self._add_domain_event("ConsultationCancelled", {
            "consultation_id": self._id,
            "reason": reason,
            "timestamp": self._updated_at
        })
    
    def update_metadata(self, metadata: Dict[str, Any]) -> None:
        """更新元数据"""
        self._metadata.update(metadata)
        self._updated_at = datetime.utcnow()
    
    def _add_domain_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """添加领域事件"""
        event = {
            "type": event_type,
            "data": event_data,
            "timestamp": datetime.utcnow()
        }
        self._domain_events.append(event)
    
    @classmethod
    def create(
        cls,
        customer_id: str,
        title: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "Consultation":
        """创建新的咨询"""
        if not customer_id:
            raise ValueError("客户ID不能为空")
        
        if not title or not title.strip():
            raise ValueError("咨询标题不能为空")
        
        consultation_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        return cls(
            id=consultation_id,
            customer_id=customer_id,
            consultant_id=None,
            status=ConsultationStatus.PENDING,
            title=title.strip(),
            created_at=now,
            updated_at=now,
            metadata=metadata or {}
        )
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Consultation):
            return False
        return self._id == other._id
    
    def __hash__(self) -> int:
        return hash(self._id)
