"""
顾问实体
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime
import uuid


@dataclass
class ConsultantEntity:
    """顾问实体 - 管理顾问信息和能力"""
    
    id: str
    userId: str
    name: str
    specialization: str
    experienceYears: int
    isActive: bool
    createdAt: datetime
    updatedAt: datetime
    _metadata: Dict[str, Any] = field(default_factory=dict, repr=False)
    
    def __post_init__(self) -> None:
        if not self.userId:
            raise ValueError("用户ID不能为空")
        
        if not self.name or not self.name.strip():
            raise ValueError("顾问姓名不能为空")
        self.name = self.name.strip()
        
        if not self.specialization or not self.specialization.strip():
            raise ValueError("专业领域不能为空")
        self.specialization = self.specialization.strip()
        
        if self.experienceYears < 0:
            raise ValueError("工作经验年数不能为负数")
        
        self.createdAt = self.createdAt or datetime.utcnow()
        self.updatedAt = self.updatedAt or datetime.utcnow()
        self._metadata = dict(self._metadata or {})

    @property
    def metadata(self) -> Dict[str, Any]:
        return dict(self._metadata)
    
    def update_profile(
        self,
        name: Optional[str] = None,
        specialization: Optional[str] = None,
        experienceYears: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """更新顾问资料"""
        if name is not None:
            if not name.strip():
                raise ValueError("顾问姓名不能为空")
            self.name = name.strip()
        
        if specialization is not None:
            if not specialization.strip():
                raise ValueError("专业领域不能为空")
            self.specialization = specialization.strip()
        
        if experienceYears is not None:
            if experienceYears < 0:
                raise ValueError("工作经验年数不能为负数")
            self.experienceYears = experienceYears
        
        if metadata is not None:
            self.update_metadata(metadata)
        else:
            self.updatedAt = datetime.utcnow()
    
    def activate(self) -> None:
        """激活顾问"""
        if self.isActive:
            raise ValueError("顾问已经是激活状态")
        
        self.isActive = True
        self.updatedAt = datetime.utcnow()
    
    def deactivate(self) -> None:
        """停用顾问"""
        if not self.isActive:
            raise ValueError("顾问已经是停用状态")
        
        self.isActive = False
        self.updatedAt = datetime.utcnow()
    
    def update_metadata(self, metadata: Dict[str, Any]) -> None:
        """更新元数据"""
        self._metadata.update(dict(metadata or {}))
        self.updatedAt = datetime.utcnow()
    
    def can_handle_consultation(self, consultation_type: str) -> bool:
        """检查是否可以处理特定类型的咨询"""
        if not self.isActive:
            return False
        
        supported_types = self._metadata.get("supported_consultation_types", [])
        return consultation_type in supported_types
    
    @classmethod
    def create(
        cls,
        userId: str,
        name: str,
        specialization: str,
        experienceYears: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "ConsultantEntity":
        """创建新的顾问"""
        consultant_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        return cls(
            id=consultant_id,
            userId=userId,
            name=name,
            specialization=specialization,
            experienceYears=experienceYears,
            isActive=True,
            createdAt=now,
            updatedAt=now,
            _metadata=dict(metadata or {})
        )
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ConsultantEntity):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        return hash(self.id)
    
    def __str__(self) -> str:
        return (
            f"ConsultantEntity(id={self.id}, userId={self.userId}, name={self.name}, "
            f"specialization={self.specialization}, experienceYears={self.experienceYears}, "
            f"isActive={self.isActive}, createdAt={self.createdAt}, updatedAt={self.updatedAt})"
        )
    
    def __repr__(self) -> str:
        return (
            f"ConsultantEntity(id={self.id}, userId={self.userId}, name={self.name}, "
            f"specialization={self.specialization}, experienceYears={self.experienceYears}, "
            f"isActive={self.isActive}, metadata={self.metadata}, createdAt={self.createdAt}, "
            f"updatedAt={self.updatedAt})"
        )
