"""
方案聚合根实体
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

from ..value_objects.plan_status import PlanStatus


@dataclass
class PlanEntity:
    """方案聚合根 - 管理方案的生命周期"""
    
    id: str
    consultationId: str
    customerId: str
    consultantId: str
    status: PlanStatus
    title: str
    content: Dict[str, Any]
    version: int
    createdAt: datetime
    updatedAt: datetime
    _metadata: Dict[str, Any] = field(default_factory=dict, repr=False)
    _domainEvents: List[Dict[str, Any]] = field(default_factory=list, repr=False)
    
    def __post_init__(self) -> None:
        if not self.consultationId:
            raise ValueError("咨询ID不能为空")
        
        if not self.customerId:
            raise ValueError("客户ID不能为空")
        
        if not self.consultantId:
            raise ValueError("顾问ID不能为空")
        
        if not self.title or not self.title.strip():
            raise ValueError("方案标题不能为空")
        self.title = self.title.strip()
        
        if self.version < 1:
            raise ValueError("方案版本号必须大于等于1")
        
        self.createdAt = self.createdAt or datetime.utcnow()
        self.updatedAt = self.updatedAt or datetime.utcnow()
        self._metadata = dict(self._metadata or {})
        self._domainEvents = list(self._domainEvents or [])
        self.content = dict(self.content or {})
    
    @property
    def metadata(self) -> Dict[str, Any]:
        return dict(self._metadata)
    
    @property
    def domainEvents(self) -> List[Dict[str, Any]]:
        return list(self._domainEvents)
    
    def updateContent(self, content: Dict[str, Any]) -> None:
        """更新方案内容"""
        if not self.status.is_editable():
            raise ValueError(f"当前状态 {self.status} 不允许编辑")
        
        self.content = dict(content or {})
        self.updatedAt = datetime.utcnow()
        
        self._addDomainEvent("PlanContentUpdated", {
            "plan_id": self.id,
            "version": self.version,
            "timestamp": self.updatedAt
        })
    
    def startGeneration(self) -> None:
        """开始生成方案"""
        if not self.status.can_transition_to(PlanStatus.GENERATING):
            raise ValueError(f"当前状态 {self.status} 无法转换为生成中状态")
        
        self.status = PlanStatus.GENERATING
        self.updatedAt = datetime.utcnow()
        
        self._addDomainEvent("PlanGenerationStarted", {
            "plan_id": self.id,
            "timestamp": self.updatedAt
        })
    
    def completeGeneration(self) -> None:
        """完成方案生成"""
        if self.status != PlanStatus.GENERATING:
            raise ValueError("只有生成中状态的方案才能完成生成")
        
        self.status = PlanStatus.REVIEWING
        self.updatedAt = datetime.utcnow()
        
        self._addDomainEvent("PlanGenerationCompleted", {
            "plan_id": self.id,
            "timestamp": self.updatedAt
        })
    
    def approve(self) -> None:
        """批准方案"""
        if not self.status.can_transition_to(PlanStatus.APPROVED):
            raise ValueError(f"当前状态 {self.status} 无法转换为已批准状态")
        
        self.status = PlanStatus.APPROVED
        self.updatedAt = datetime.utcnow()
        
        self._addDomainEvent("PlanApproved", {
            "plan_id": self.id,
            "timestamp": self.updatedAt
        })
    
    def reject(self, reason: Optional[str] = None) -> None:
        """拒绝方案"""
        if not self.status.can_transition_to(PlanStatus.REJECTED):
            raise ValueError(f"当前状态 {self.status} 无法转换为已拒绝状态")
        
        self.status = PlanStatus.REJECTED
        self.updatedAt = datetime.utcnow()
        
        if reason:
            self._metadata["rejection_reason"] = reason
        
        self._addDomainEvent("PlanRejected", {
            "plan_id": self.id,
            "reason": reason,
            "timestamp": self.updatedAt
        })
    
    def createNewVersion(self) -> "PlanEntity":
        """创建新版本"""
        new_version = self.version + 1
        new_plan = PlanEntity(
            id=str(uuid.uuid4()),
            consultationId=self.consultationId,
            customerId=self.customerId,
            consultantId=self.consultantId,
            status=PlanStatus.DRAFT,
            title=self.title,
            content=dict(self.content),
            version=new_version,
            createdAt=datetime.utcnow(),
            updatedAt=datetime.utcnow(),
            _metadata=dict(self.metadata)
        )
        
        self._addDomainEvent("PlanVersionCreated", {
            "original_plan_id": self.id,
            "new_plan_id": new_plan.id,
            "version": new_version,
            "timestamp": datetime.utcnow()
        })
        
        return new_plan
    
    def updateMetadata(self, metadata: Dict[str, Any]) -> None:
        """更新元数据"""
        self._metadata.update(dict(metadata or {}))
        self.updatedAt = datetime.utcnow()
    
    def _addDomainEvent(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """添加领域事件"""
        event = {
            "type": event_type,
            "data": event_data,
            "timestamp": datetime.utcnow()
        }
        self._domainEvents.append(event)
    
    def clearDomainEvents(self) -> None:
        """清空领域事件"""
        self._domainEvents.clear()
    
    @classmethod
    def create(
        cls,
        consultationId: str,
        customerId: str,
        consultantId: str,
        title: str,
        content: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> "PlanEntity":
        """创建新的方案"""
        plan_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        return cls(
            id=plan_id,
            consultationId=consultationId,
            customerId=customerId,
            consultantId=consultantId,
            status=PlanStatus.DRAFT,
            title=title,
            content=content,
            version=1,
            createdAt=now,
            updatedAt=now,
            _metadata=dict(metadata or {})
        )
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PlanEntity):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        return hash(self.id)
    
    def __str__(self) -> str:
        return (
            f"PlanEntity(id={self.id}, consultationId={self.consultationId}, customerId={self.customerId}, "
            f"consultantId={self.consultantId}, status={self.status}, title={self.title}, "
            f"version={self.version}, createdAt={self.createdAt}, updatedAt={self.updatedAt})"
        )
    
    def __repr__(self) -> str:
        return (
            f"PlanEntity(id={self.id}, consultationId={self.consultationId}, customerId={self.customerId}, "
            f"consultantId={self.consultantId}, status={self.status}, title={self.title}, "
            f"content={self.content}, version={self.version}, metadata={self.metadata}, "
            f"domainEvents={self.domainEvents}, createdAt={self.createdAt}, updatedAt={self.updatedAt})"
        )
