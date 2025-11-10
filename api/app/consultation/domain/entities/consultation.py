"""
咨询聚合根实体
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

from ..value_objects.consultation_status import ConsultationStatus


@dataclass
class ConsultationEntity:
    """咨询聚合根 - 管理咨询会话的生命周期"""
    
    id: str
    customerId: str
    consultantId: Optional[str]
    status: ConsultationStatus
    title: str
    createdAt: datetime
    updatedAt: datetime
    _metadata: Dict[str, Any] = field(default_factory=dict, repr=False)
    _domainEvents: List[Dict[str, Any]] = field(default_factory=list, repr=False)
    
    def __post_init__(self) -> None:
        if not self.customerId:
            raise ValueError("客户ID不能为空")
        
        if not self.title or not self.title.strip():
            raise ValueError("咨询标题不能为空")
        self.title = self.title.strip()
        
        self.createdAt = self.createdAt or datetime.utcnow()
        self.updatedAt = self.updatedAt or datetime.utcnow()
        self._metadata = dict(self._metadata or {})
        self._domainEvents = list(self._domainEvents or [])
    
    @property
    def metadata(self) -> Dict[str, Any]:
        return dict(self._metadata)
    
    @property
    def domainEvents(self) -> List[Dict[str, Any]]:
        return list(self._domainEvents)
    
    def assignConsultant(self, consultantId: str) -> None:
        """分配顾问"""
        if not consultantId:
            raise ValueError("顾问ID不能为空")
        
        if self.consultantId:
            raise ValueError("咨询已分配顾问")
        
        self.consultantId = consultantId
        self.status = ConsultationStatus.IN_PROGRESS
        self.updatedAt = datetime.utcnow()
        
        self._addDomainEvent("ConsultantAssigned", {
            "consultation_id": self.id,
            "consultant_id": consultantId,
            "timestamp": self.updatedAt
        })
    
    def completeConsultation(self) -> None:
        """完成咨询"""
        if not self.consultantId:
            raise ValueError("咨询未分配顾问，无法完成")
        
        if not self.status.can_transition_to(ConsultationStatus.COMPLETED):
            raise ValueError(f"当前状态 {self.status} 无法转换为完成状态")
        
        self.status = ConsultationStatus.COMPLETED
        self.updatedAt = datetime.utcnow()
        
        self._addDomainEvent("ConsultationCompleted", {
            "consultation_id": self.id,
            "timestamp": self.updatedAt
        })
    
    def cancelConsultation(self, reason: Optional[str] = None) -> None:
        """取消咨询"""
        if not self.status.can_transition_to(ConsultationStatus.CANCELLED):
            raise ValueError(f"当前状态 {self.status} 无法转换为取消状态")
        
        self.status = ConsultationStatus.CANCELLED
        self.updatedAt = datetime.utcnow()
        
        if reason:
            self._metadata["cancellation_reason"] = reason
        
        self._addDomainEvent("ConsultationCancelled", {
            "consultation_id": self.id,
            "reason": reason,
            "timestamp": self.updatedAt
        })
    
    def updateMetadata(self, metadata: Dict[str, Any]) -> None:
        """更新元数据"""
        self._metadata.update(dict(metadata or {}))
        self.updatedAt = datetime.utcnow()
    
    def updateTitle(self, title: str) -> None:
        """更新咨询标题"""
        if not title or not title.strip():
            raise ValueError("咨询标题不能为空")
        self.title = title.strip()
        self.updatedAt = datetime.utcnow()
    
    def clearDomainEvents(self) -> None:
        """清空领域事件"""
        self._domainEvents.clear()
    
    def _addDomainEvent(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """添加领域事件"""
        event = {
            "type": event_type,
            "data": event_data,
            "timestamp": datetime.utcnow()
        }
        self._domainEvents.append(event)
    
    @classmethod
    def create(
        cls,
        customerId: str,
        title: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "ConsultationEntity":
        """创建新的咨询"""
        consultation_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        return cls(
            id=consultation_id,
            customerId=customerId,
            consultantId=None,
            status=ConsultationStatus.PENDING,
            title=title,
            createdAt=now,
            updatedAt=now,
            _metadata=dict(metadata or {})
        )
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ConsultationEntity):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        return hash(self.id)
    
    def __str__(self) -> str:
        return (
            f"ConsultationEntity(id={self.id}, customerId={self.customerId}, consultantId={self.consultantId}, "
            f"status={self.status}, title={self.title}, createdAt={self.createdAt}, updatedAt={self.updatedAt})"
        )
    
    def __repr__(self) -> str:
        return (
            f"ConsultationEntity(id={self.id}, customerId={self.customerId}, consultantId={self.consultantId}, "
            f"status={self.status}, title={self.title}, metadata={self.metadata}, "
            f"domainEvents={self.domainEvents}, createdAt={self.createdAt}, updatedAt={self.updatedAt})"
        )
