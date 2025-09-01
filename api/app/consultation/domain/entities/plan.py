"""
方案聚合根实体
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

from ..value_objects.plan_status import PlanStatus


class Plan:
    """方案聚合根 - 管理方案的生命周期"""
    
    def __init__(
        self,
        id: str,
        consultation_id: str,
        customer_id: str,
        consultant_id: str,
        status: PlanStatus,
        title: str,
        content: Dict[str, Any],
        version: int,
        created_at: datetime,
        updated_at: datetime,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self._id = id
        self._consultation_id = consultation_id
        self._customer_id = customer_id
        self._consultant_id = consultant_id
        self._status = status
        self._title = title
        self._content = content
        self._version = version
        self._created_at = created_at
        self._updated_at = updated_at
        self._metadata = metadata or {}
        self._domain_events = []
    
    @property
    def id(self) -> str:
        return self._id
    
    @property
    def consultation_id(self) -> str:
        return self._consultation_id
    
    @property
    def customer_id(self) -> str:
        return self._customer_id
    
    @property
    def consultant_id(self) -> str:
        return self._consultant_id
    
    @property
    def status(self) -> PlanStatus:
        return self._status
    
    @property
    def title(self) -> str:
        return self._title
    
    @property
    def content(self) -> Dict[str, Any]:
        return self._content.copy()
    
    @property
    def version(self) -> int:
        return self._version
    
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
    
    def update_content(self, content: Dict[str, Any]) -> None:
        """更新方案内容"""
        if not self._status.is_editable():
            raise ValueError(f"当前状态 {self._status} 不允许编辑")
        
        self._content = content
        self._updated_at = datetime.utcnow()
        
        self._add_domain_event("PlanContentUpdated", {
            "plan_id": self._id,
            "version": self._version,
            "timestamp": self._updated_at
        })
    
    def start_generation(self) -> None:
        """开始生成方案"""
        if not self._status.can_transition_to(PlanStatus.GENERATING):
            raise ValueError(f"当前状态 {self._status} 无法转换为生成中状态")
        
        self._status = PlanStatus.GENERATING
        self._updated_at = datetime.utcnow()
        
        self._add_domain_event("PlanGenerationStarted", {
            "plan_id": self._id,
            "timestamp": self._updated_at
        })
    
    def complete_generation(self) -> None:
        """完成方案生成"""
        if self._status != PlanStatus.GENERATING:
            raise ValueError("只有生成中状态的方案才能完成生成")
        
        self._status = PlanStatus.REVIEWING
        self._updated_at = datetime.utcnow()
        
        self._add_domain_event("PlanGenerationCompleted", {
            "plan_id": self._id,
            "timestamp": self._updated_at
        })
    
    def approve(self) -> None:
        """批准方案"""
        if not self._status.can_transition_to(PlanStatus.APPROVED):
            raise ValueError(f"当前状态 {self._status} 无法转换为已批准状态")
        
        self._status = PlanStatus.APPROVED
        self._updated_at = datetime.utcnow()
        
        self._add_domain_event("PlanApproved", {
            "plan_id": self._id,
            "timestamp": self._updated_at
        })
    
    def reject(self, reason: Optional[str] = None) -> None:
        """拒绝方案"""
        if not self._status.can_transition_to(PlanStatus.REJECTED):
            raise ValueError(f"当前状态 {self._status} 无法转换为已拒绝状态")
        
        self._status = PlanStatus.REJECTED
        self._updated_at = datetime.utcnow()
        
        if reason:
            self._metadata["rejection_reason"] = reason
        
        self._add_domain_event("PlanRejected", {
            "plan_id": self._id,
            "reason": reason,
            "timestamp": self._updated_at
        })
    
    def create_new_version(self) -> "Plan":
        """创建新版本"""
        new_version = self._version + 1
        new_plan = Plan(
            id=str(uuid.uuid4()),
            consultation_id=self._consultation_id,
            customer_id=self._customer_id,
            consultant_id=self._consultant_id,
            status=PlanStatus.DRAFT,
            title=self._title,
            content=self._content.copy(),
            version=new_version,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            metadata=self._metadata.copy()
        )
        
        self._add_domain_event("PlanVersionCreated", {
            "original_plan_id": self._id,
            "new_plan_id": new_plan.id,
            "version": new_version,
            "timestamp": datetime.utcnow()
        })
        
        return new_plan
    
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
        consultation_id: str,
        customer_id: str,
        consultant_id: str,
        title: str,
        content: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> "Plan":
        """创建新的方案"""
        if not consultation_id:
            raise ValueError("咨询ID不能为空")
        
        if not customer_id:
            raise ValueError("客户ID不能为空")
        
        if not consultant_id:
            raise ValueError("顾问ID不能为空")
        
        if not title or not title.strip():
            raise ValueError("方案标题不能为空")
        
        plan_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        return cls(
            id=plan_id,
            consultation_id=consultation_id,
            customer_id=customer_id,
            consultant_id=consultant_id,
            status=PlanStatus.DRAFT,
            title=title.strip(),
            content=content,
            version=1,
            created_at=now,
            updated_at=now,
            metadata=metadata or {}
        )
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Plan):
            return False
        return self._id == other._id
    
    def __hash__(self) -> int:
        return hash(self._id)
